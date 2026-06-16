import requests
import sys

base = 'http://localhost:8000'
# Args: sample_id tasting_id filepath
if len(sys.argv) < 4:
    print('USAGE: upload_test_doc.py <sample_id> <tasting_id> <file>')
    sys.exit(1)

sample_id = sys.argv[1]

tasting_id = sys.argv[2]
file_path = sys.argv[3]
url = f"{base}/samples/{sample_id}/tastings/{tasting_id}/documents"
files = {'file': open(file_path, 'rb')}
data = {'document_type': 'cafe_verde'}
try:
    r = requests.post(url, files=files, data=data, allow_redirects=False)
    print('STATUS_CODE:', r.status_code)
    print('HEADERS:', r.headers)
    try:
        print('TEXT:', r.text[:1000])
    except Exception:
        pass
except Exception as e:
    print('ERROR:', e)
