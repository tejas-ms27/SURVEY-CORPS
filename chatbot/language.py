"""
Language boundary for the investigator chatbot.

Everything downstream of this module stays English-only: structured regex
routing, embeddings, retrieval, and answer synthesis. Kannada input is
translated to English before that pipeline, and only the final natural-language
answer is translated back. Citations are never translated.
"""

import json
import logging
import os
import re


LOGGER = logging.getLogger(__name__)
TRANSLATION_MODEL_NAME = os.environ.get("GROQ_TRANSLATION_MODEL", "openai/gpt-oss-120b")

# Kannada Unicode block (U+0C80–U+0CFF). Lets us detect Kannada input locally, with no
# LLM call, so a rate-limited translation service never leaves a Kannada question
# unrouted. When translation is unavailable, a detected-Kannada question is routed to a
# deterministic forensic briefing rather than crashing the chat.
_KANNADA_RE = re.compile(r"[ಀ-೿]")
# Deterministic English query used when Kannada is detected locally but cannot be
# translated — it reliably triggers the suspicious-account investigation route.
_KANNADA_FALLBACK_QUERY = (
    "Which accounts are the most suspicious and what is the strongest evidence against them?"
)


def _has_kannada(text: str) -> bool:
    return bool(_KANNADA_RE.search(text or ""))

_LANGUAGE_DETECT_TRANSLATE_PROMPT = """You are a language boundary for a forensic financial investigation chatbot.

Detect whether the user's message is English or Kannada.

Return ONLY a JSON object with exactly this shape:
{"language": "en" | "kn", "english_text": "..."}

Rules:
- If the message is English, return language "en" and copy the original text unchanged as english_text.
- If the message is Kannada, return language "kn" and translate it to natural, clear English.
- Preserve account numbers, transaction IDs, dates, currency amounts, bank names, and person names exactly as written.
- Do not transliterate, correct, or reformat identifying tokens.
- Do not include markdown, code fences, commentary, or any extra keys.
"""

_ANSWER_TRANSLATE_PROMPT = """Translate the following English answer into natural Kannada for a police financial investigator.

Rules:
- Return only the translated answer text.
- Preserve account numbers, transaction IDs, dates, currency amounts, bank names, person names, and system codes exactly as given.
- Do not transliterate identifying tokens into Kannada script.
- Do not add notes, explanations, or commentary about the translation.
"""


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    return text


def detect_and_translate_to_english(text: str) -> dict:
    """
    Return {"language": "en"|"kn", "english_text": "..."}.

    On malformed model output, degrade to English passthrough and log the raw
    response so translation failures are visible during testing.
    """
    from chatbot.rag_chat import generate

    messages = [
        {"role": "system", "content": _LANGUAGE_DETECT_TRANSLATE_PROMPT},
        {"role": "user", "content": text},
    ]
    try:
        raw = generate(messages, model=TRANSLATION_MODEL_NAME, temperature=0.0)
    except Exception as exc:
        # Translation service unavailable (e.g. every Groq key rate-limited). Detect the
        # language locally so a Kannada question is still handled: route it to a
        # deterministic forensic briefing instead of crashing the chat.
        if _has_kannada(text):
            LOGGER.warning("Translation unavailable (%s); Kannada detected locally — "
                           "routing to deterministic forensic briefing.", exc)
            return {"language": "kn", "english_text": _KANNADA_FALLBACK_QUERY}
        LOGGER.warning("Translation unavailable (%s); treating input as English.", exc)
        return {"language": "en", "english_text": text}
    clean = _strip_json_fences(raw)

    try:
        parsed = json.loads(clean)
        language = str(parsed.get("language") or "en")
        english_text = parsed.get("english_text")
        if not isinstance(english_text, str) or not english_text.strip():
            raise ValueError("Missing english_text")
        return {"language": language, "english_text": english_text}
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        LOGGER.warning(
            "Language detection failed; treating input as English. Error: %s. Raw response: %r",
            exc,
            raw,
        )
        return {"language": "en", "english_text": text}


def translate_answer(english_answer: str, target_language: str) -> str:
    """
    Translate the final answer text. English is a no-op; citations stay outside.
    """
    if target_language == "en":
        return english_answer
    if target_language != "kn":
        LOGGER.warning(
            "Unsupported target language %r; returning English answer unchanged.",
            target_language,
        )
        return english_answer

    from chatbot.rag_chat import generate

    messages = [
        {"role": "system", "content": _ANSWER_TRANSLATE_PROMPT},
        {"role": "user", "content": english_answer},
    ]
    try:
        return generate(messages, model=TRANSLATION_MODEL_NAME, temperature=0.1)
    except Exception as exc:
        # Kannada translation temporarily unavailable (e.g. rate-limited). Return the
        # English forensic answer rather than failing the request — the investigator
        # still gets the substantive finding.
        LOGGER.warning("Kannada answer translation unavailable (%s); returning English "
                       "answer unchanged.", exc)
        return english_answer
