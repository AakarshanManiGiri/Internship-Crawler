from datetime import datetime

from scrapers.meta import MetaScraper


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_meta_graphql_parsing(monkeypatch):
    payload = {
        'data': {
            'jobs': [
                {
                    'id': 'm-1',
                    'title': 'Product Design Intern',
                    'location': 'Menlo Park, CA',
                    'apply_url': 'https://www.metacareers.com/jobs/m-1',
                    'posted_date': '2024-05-01T12:00:00Z',
                    'description': 'Design fun things'
                }
            ]
        }
    }

    ms = MetaScraper()

    def fake_post(url, data=None, headers=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(ms, 'session', ms.session)
    monkeypatch.setattr(ms.session, 'post', fake_post)

    results = ms.scrape()
    assert isinstance(results, list)
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Product Design Intern'
    assert 'Menlo Park' in job['location']
    assert job['url'].startswith('https://')
    assert isinstance(job['posted_date'], datetime)


def test_meta_graphql_first_fails_then_inline_succeeds(monkeypatch):
    # First POST raises an HTTP error (simulating 400), second inline query returns data
    ms = MetaScraper()

    class Resp:
        def __init__(self, status_code=200, data=None):
            self.status_code = status_code
            self._data = data or {}

        def raise_for_status(self):
            import requests
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"{self.status_code} Error")
            return None

        def json(self):
            return self._data

    call_count = {'n': 0}

    def fake_post(url, data=None, headers=None, timeout=None):
        call_count['n'] += 1
        # first call simulates 400
        if call_count['n'] == 1:
            return Resp(status_code=400)

        # second call (inline query) returns valid structure
        return Resp(status_code=200, data={'data': {'jobs': [{'id':'m-2','title':'Design Intern','location':'Menlo','apply_url':'https://www.metacareers.com/jobs/m-2','posted_date':'2024-01-01T01:00:00Z'}]}})

    monkeypatch.setattr(ms, 'session', ms.session)
    monkeypatch.setattr(ms.session, 'post', fake_post)

    results = ms.scrape()
    assert len(results) == 1
    assert results[0]['title'] == 'Design Intern'
