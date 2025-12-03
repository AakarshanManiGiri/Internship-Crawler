from scrapers.google import GoogleScraper


class FakeElement:
    def __init__(self, text=None, href=None):
        self._text = text
        self._href = href

    def inner_text(self):
        return self._text or ''

    def get_attribute(self, name):
        if name == 'href':
            return self._href
        return None


class FakeCard:
    def __init__(self, title=None, location=None, href=None):
        self._title = title
        self._location = location
        self._href = href

    def query_selector(self, selector):
        # Match selectors used in scraper
        if '[class*="title"]' in selector or 'h3' in selector:
            return FakeElement(text=self._title)
        if '[class*="location"]' in selector:
            return FakeElement(text=self._location)
        if 'a[href*="/jobs/results/"]' in selector or 'a[href' in selector:
            return FakeElement(href=self._href)
        return None


class FakePage:
    def __init__(self, cards, raise_on_wait=False, timeout_exc=None):
        self._cards = cards
        self._raise = raise_on_wait
        self._timeout_exc = timeout_exc

    def goto(self, url, timeout=None):
        return None

    def wait_for_selector(self, selector, timeout=None):
        if self._raise:
            raise self._timeout_exc or Exception('timeout')
        return None

    def query_selector_all(self, selector):
        return self._cards


class FakeBrowser:
    def __init__(self, page):
        self._page = page

    def new_page(self):
        return self._page

    def close(self):
        return None


class FakeChromium:
    def __init__(self, browser):
        self._browser = browser

    def launch(self, headless=True):
        return self._browser


class FakePlaywrightCtx:
    def __init__(self, chromium):
        self.chromium = chromium

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_google_playwright_parses_jobs(monkeypatch):
    # Create fake job cards: one intern and one non-intern
    card1 = FakeCard(title='Software Engineering Intern', location='Sydney, Australia', href='/jobs/results/123')
    card2 = FakeCard(title='Senior Software Engineer', location='Mountain View, CA', href='/jobs/results/999')

    page = FakePage([card1, card2])
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakePlaywrightCtx(chromium)

    # Monkeypatch the module-level PLAYWRIGHT_AVAILABLE and sync_playwright
    import scrapers.google as google_mod
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    gs = GoogleScraper()
    results = gs.scrape()

    assert isinstance(results, list)
    # only the intern should be returned
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Software Engineering Intern'
    assert 'Sydney' in job['location']
    assert job['url'].endswith('/jobs/results/123')


def test_google_playwright_timeout_fallback(monkeypatch):
    # Simulate wait_for_selector raising a Playwright timeout exception
    import scrapers.google as google_mod

    class TimeoutExc(Exception):
        pass

    # Ensure the module has a PlaywrightTimeout symbol the scraper expects
    monkeypatch.setattr(google_mod, 'PlaywrightTimeout', TimeoutExc, raising=False)
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)

    page = FakePage([], raise_on_wait=True, timeout_exc=TimeoutExc())
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakePlaywrightCtx(chromium)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    gs = GoogleScraper()
    results = gs.scrape()
    # timeout should result in empty list (scraper closes browser and returns)
    assert results == []
from scrapers.google import GoogleScraper


class FakeElement:
    def __init__(self, text=None, href=None):
        self._text = text
        self._href = href

    def inner_text(self):
        return self._text or ''

    def get_attribute(self, name):
        if name == 'href':
            return self._href
        return None


class FakeCard:
    def __init__(self, title=None, location=None, href=None):
        self._title = title
        self._location = location
        self._href = href

    def query_selector(self, selector):
        # Match selectors used in scraper
        if '[class*="title"]' in selector or 'h3' in selector:
            return FakeElement(text=self._title)
        if '[class*="location"]' in selector:
            return FakeElement(text=self._location)
        if 'a[href*="/jobs/results/"]' in selector or 'a[href' in selector:
            return FakeElement(href=self._href)
        return None


class FakePage:
    def __init__(self, cards, raise_on_wait=False, timeout_exc=None):
        self._cards = cards
        self._raise = raise_on_wait
        self._timeout_exc = timeout_exc

    def goto(self, url, timeout=None):
        return None

    def wait_for_selector(self, selector, timeout=None):
        if self._raise:
            raise self._timeout_exc or Exception('timeout')
        return None

    def query_selector_all(self, selector):
        return self._cards


class FakeBrowser:
    def __init__(self, page):
        self._page = page

    def new_page(self):
        return self._page

    def close(self):
        return None


class FakeChromium:
    def __init__(self, browser):
        self._browser = browser

    def launch(self, headless=True):
        return self._browser


class FakePlaywrightCtx:
    def __init__(self, chromium):
        self.chromium = chromium

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_google_playwright_parses_jobs(monkeypatch):
    # Create fake job cards: one intern and one non-intern
    card1 = FakeCard(title='Software Engineering Intern', location='Sydney, Australia', href='/jobs/results/123')
    card2 = FakeCard(title='Senior Software Engineer', location='Mountain View, CA', href='/jobs/results/999')

    page = FakePage([card1, card2])
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakePlaywrightCtx(chromium)

    # Monkeypatch the module-level PLAYWRIGHT_AVAILABLE and sync_playwright
    import scrapers.google as google_mod
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    gs = GoogleScraper()
    results = gs.scrape()

    assert isinstance(results, list)
    # only the intern should be returned
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Software Engineering Intern'
    assert 'Sydney' in job['location']
    assert job['url'].endswith('/jobs/results/123')


def test_google_playwright_timeout_fallback(monkeypatch):
    # Simulate wait_for_selector raising a Playwright timeout exception
    import scrapers.google as google_mod

    class TimeoutExc(Exception):
        pass

    # Ensure the module has a PlaywrightTimeout symbol the scraper expects
    monkeypatch.setattr(google_mod, 'PlaywrightTimeout', TimeoutExc, raising=False)
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)

    page = FakePage([], raise_on_wait=True, timeout_exc=TimeoutExc())
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakePlaywrightCtx(chromium)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    gs = GoogleScraper()
    results = gs.scrape()
    # timeout should result in empty list (scraper closes browser and returns)
    assert results == []
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
    from scrapers.google import GoogleScraper


    class FakeElement:
        def __init__(self, text=None, href=None):
            self._text = text
            self._href = href

        def inner_text(self):
            return self._text or ''

        def get_attribute(self, name):
            if name == 'href':
                return self._href
            return None


    class FakeCard:
        def __init__(self, title=None, location=None, href=None):
            self._title = title
            self._location = location
            self._href = href

        def query_selector(self, selector):
            # Match selectors used in scraper
            if '[class*="title"]' in selector or 'h3' in selector:
                return FakeElement(text=self._title)
            if '[class*="location"]' in selector:
                return FakeElement(text=self._location)
            if 'a[href*="/jobs/results/"]' in selector or 'a[href' in selector:
                return FakeElement(href=self._href)
            return None


    class FakePage:
        def __init__(self, cards, raise_on_wait=False, timeout_exc=None):
            self._cards = cards
            self._raise = raise_on_wait
            self._timeout_exc = timeout_exc

        def goto(self, url, timeout=None):
            return None

        def wait_for_selector(self, selector, timeout=None):
            if self._raise:
                raise self._timeout_exc or Exception('timeout')
            return None

        def query_selector_all(self, selector):
            return self._cards


    class FakeBrowser:
        def __init__(self, page):
            self._page = page

        def new_page(self):
            return self._page

        def close(self):
            return None


    class FakeChromium:
        def __init__(self, browser):
            self._browser = browser

        def launch(self, headless=True):
            return self._browser


    class FakePlaywrightCtx:
        def __init__(self, chromium):
            self.chromium = chromium

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False


    def test_google_playwright_parses_jobs(monkeypatch):
        # Create fake job cards: one intern and one non-intern
        card1 = FakeCard(title='Software Engineering Intern', location='Sydney, Australia', href='/jobs/results/123')
        card2 = FakeCard(title='Senior Software Engineer', location='Mountain View, CA', href='/jobs/results/999')

        page = FakePage([card1, card2])
        browser = FakeBrowser(page)
        chromium = FakeChromium(browser)
        ctx = FakePlaywrightCtx(chromium)

        # Monkeypatch the module-level PLAYWRIGHT_AVAILABLE and sync_playwright
        import scrapers.google as google_mod
        monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
        monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

        gs = GoogleScraper()
        results = gs.scrape()

        assert isinstance(results, list)
        # only the intern should be returned
        assert len(results) == 1
        job = results[0]
        assert job['title'] == 'Software Engineering Intern'
        assert 'Sydney' in job['location']
        assert job['url'].endswith('/jobs/results/123')


    def test_google_playwright_timeout_fallback(monkeypatch):
        # Simulate wait_for_selector raising a Playwright timeout exception
        import scrapers.google as google_mod

        class TimeoutExc(Exception):
            pass

        # Ensure the module has a PlaywrightTimeout symbol the scraper expects
        monkeypatch.setattr(google_mod, 'PlaywrightTimeout', TimeoutExc, raising=False)
        monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)

        page = FakePage([], raise_on_wait=True, timeout_exc=TimeoutExc())
        browser = FakeBrowser(page)
        chromium = FakeChromium(browser)
        ctx = FakePlaywrightCtx(chromium)
        monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

        gs = GoogleScraper()
        results = gs.scrape()
        # timeout should result in empty list (scraper closes browser and returns)
        assert results == []
