"""Capture public Kaggle search metadata without credentials or dataset downloads."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
QUERIES = ['EDDF', 'Frankfurt weather', 'METAR', 'runway configuration']


def main():
    raw = ROOT / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    results = []
    for index, query in enumerate(QUERIES):
        url = 'https://www.kaggle.com/api/v1/datasets/list?' + urlencode({'search': query, 'page': 1})
        item = {'query': query, 'url': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat()}
        try:
            with urlopen(Request(url, headers={'User-Agent': 'FraAlliance-data-research/1.0'}), timeout=25) as response:
                body = response.read(4_000_001)
                item.update(http_status=response.status, content_type=response.headers.get('Content-Type'))
            if len(body) > 4_000_000:
                raise ValueError('Public metadata response exceeds 4 MB limit')
            filename = f'search-{index + 1}.response'
            (raw / filename).write_bytes(body)
            item.update(file='raw/' + filename, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                item['outcome'] = 'non_json_response_not_a_verified_catalog_result'
            else:
                item['outcome'] = 'json_response'
                if isinstance(payload, list):
                    item['count_this_page'] = len(payload)
                    item['datasets'] = [{key: row.get(key) for key in ('ref', 'title', 'subtitle', 'totalBytes', 'licenseName', 'lastUpdated', 'url')} for row in payload]
        except HTTPError as error:
            item.update(http_status=error.code, outcome='http_error')
        except (URLError, TimeoutError, ValueError) as error:
            item.update(outcome='request_error', error=str(error))
        results.append(item)
        print(json.dumps(item), flush=True)
        time.sleep(1)
    (ROOT / 'public-catalog-check.json').write_text(json.dumps({'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'First result page for four public queries; no credentials or accounts accessed', 'queries': results}, indent=2) + '\n')


if __name__ == '__main__':
    main()
