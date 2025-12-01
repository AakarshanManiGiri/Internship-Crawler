from datetime import datetime

from scrapers.google import GoogleScraper


class FakeResponse:
    def __init__(self, data):
        self._data = data
        # simulate 200 by default
        self.status_code = getattr(data, 'status_code', 200) if not isinstance(data, dict) else 200
        self.headers = {}

    def json(self):
        return self._data

    def raise_for_status(self):
        # mimic requests behavior
        if getattr(self, 'status_code', 200) >= 400:
            import requests
            raise requests.exceptions.HTTPError(f"{self.status_code} Error")
        return None


def test_google_scraper_parses_jobs(monkeypatch):
    data = {
        'jobs': [
            {
                'id': '111',
                'title': 'Software Engineering Intern',
                'locations': ['Sydney, Australia'],
                'posted_date': '2024-06-01T10:00:00Z',
                'description': 'Do cool things',
                'qualifications': ['Python']
            }
        ]
    }

    gs = GoogleScraper()

    def fake_get(url, params=None, timeout=None, **kwargs):
        return FakeResponse(data)

    monkeypatch.setattr(gs, 'session', gs.session)
    monkeypatch.setattr(gs.session, 'get', fake_get)

    results = gs.scrape()
    assert isinstance(results, list)
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Software Engineering Intern'
    assert 'Sydney' in job['location']
    assert job['requirements'] == ['Python']
    assert isinstance(job['posted_date'], datetime)


def test_google_tries_alternative_endpoints(monkeypatch):
    # First endpoint redirects to a broken URL (302 Location -> 404), second endpoint returns valid json
    gs = GoogleScraper()

    class Resp:
        def __init__(self, status_code=200, json_data=None, headers=None):
            self.status_code = status_code
            self._json = json_data or {}
            self.headers = headers or {}

        def json(self):
            return self._json

        def raise_for_status(self):
            import requests
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"{self.status_code} Error")
            return None

    def fake_get(url, params=None, timeout=None, allow_redirects=True):
        # Simulate first endpoint returning a redirect to an invalid path
        if url.startswith('https://careers.google.com/api/v1/jobs/search'):
            return Resp(status_code=302, headers={'Location': 'https://www.google.com/about/careers/applications/api/v1/jobs/search/'})

        # If the URL is the redirected one -> simulate 404
        if url.startswith('https://www.google.com/about/careers/applications/api/v1/jobs/search/'):
            return Resp(status_code=404)

        # second endpoint returns valid payload
        if url.startswith('https://careers.google.com/api/v1/search'):
            return Resp(status_code=200, json_data={'jobs':[{'id':'22','title':'Hardware Intern','locations':['Sydney'], 'posted_date':'2024-02-01T00:00:00Z'}]})

        # default
        return Resp(status_code=404)

    monkeypatch.setattr(gs, 'session', gs.session)
    monkeypatch.setattr(gs.session, 'get', fake_get)

    res = gs.scrape()
    assert len(res) == 1
    assert res[0]['title'] == 'Hardware Intern'
