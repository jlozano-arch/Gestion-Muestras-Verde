import requests, sys
base='http://localhost:8000'
if len(sys.argv)<3:
    print('USAGE: test_pdf_request.py <sample_id> <tasting_id>')
    sys.exit(1)
sample_id=sys.argv[1]
tasting_id=sys.argv[2]
url=f"{base}/samples/{sample_id}/tastings/{tasting_id}/pdf"
try:
    r=requests.get(url)
    print('STATUS', r.status_code)
    if r.status_code==200 and r.headers.get('content-type','').startswith('application/pdf'):
        open('out_test_tasting.pdf','wb').write(r.content)
        print('Saved out_test_tasting.pdf size', len(r.content))
    else:
        print('Response headers:', r.headers)
        print('Body preview:', r.text[:500])
except Exception as e:
    print('ERROR', e)
