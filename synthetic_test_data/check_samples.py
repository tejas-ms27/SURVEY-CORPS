import pdfplumber, pathlib
sample_dir = pathlib.Path(__file__).parent / '_bank_samples' / 'statements'
for pp in sorted(sample_dir.glob('*.pdf')):
    with pdfplumber.open(pp) as pdf:
        text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    bad = [w for w in ['SYNTHETIC','SYN0','synpay','syntest','SYNX'] if w in text]
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print('=== ' + pp.name[:65] + ' ===')
    print('  Pages=%d  Lines=%d  FORBIDDEN=%s' % (len(pdf.pages), len(lines), bad or 'NONE'))
    for l in lines[:4]:
        print('  HDR: ' + l[:100])
    cnt = 0
    for l in lines[4:]:
        u = l.upper()
        if any(x in u for x in ['UPI','NEFT','IMPS','ATM','SALARY','NACH','RTGS','INTEREST','CASH','POS']):
            print('  TXN: ' + l[:110])
            cnt += 1
            if cnt >= 6: break
    print()
