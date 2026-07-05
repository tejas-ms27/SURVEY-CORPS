// TODO: confirm exact team member names/spelling with the team.
// Source mockup read "Tejas S, Vinayak, Tejas MS002C Nikhil" — "002C" treated
// as an OCR artifact.
const TEAM_NAMES = ['Tejas S', 'Vinayak', 'Tejas MS', 'Nikhil']

// TODO: real contact details needed — email + LinkedIn are placeholders.
const TEAM = TEAM_NAMES.map((name) => ({
  name,
  role: 'Survey Corps',
  email: '...', // TODO: real email
  linkedin: '...', // TODO: real LinkedIn URL
}))

export function Footer() {
  return (
    <>
      <footer className="sc-footer">
        <div className="sc-wrap">
          <div className="sc-footer-top">
            <h3>About us</h3>
            <p>
              Survey Corps is built by a small team turning messy financial evidence into clear,
              defensible cases. Reach any of us below.
            </p>
          </div>

          <div className="sc-team">
            {TEAM.map((m) => (
              <div key={m.name} className="sc-member">
                <div className="nm">{m.name}</div>
                <div className="role">{m.role}</div>
                {/* TODO: swap "..." for real values before launch */}
                <a href={m.email === '...' ? undefined : `mailto:${m.email}`}>
                  {m.email === '...' ? 'email — TODO' : m.email}
                </a>
                <a
                  href={m.linkedin === '...' ? undefined : m.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {m.linkedin === '...' ? 'LinkedIn — TODO' : 'LinkedIn'}
                </a>
              </div>
            ))}
          </div>
        </div>
      </footer>
    </>
  )
}
