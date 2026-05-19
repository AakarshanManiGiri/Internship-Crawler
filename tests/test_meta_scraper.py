from datetime import datetime
import types

from scrapers.meta import MetaScraper


class FakeElement:
    def __init__(self, text=None, href=None):
        self._text = text
        self._href = href

    def inner_text(self, timeout=None):
        return self._text or ''

    def get_attribute(self, name, timeout=None):
        if name == 'href':
            return self._href
        return None


class FakeCard:
    def __init__(self, title=None, locations=None, href=None):
        self._title = title
        self._locations = locations or []
        self._href = href

    def query_selector(self, selector):
        if selector == 'a[href]':
            return FakeElement(href=self._href)
        return None

    def query_selector_all(self, selector):
        if selector in {'h3', 'h2', "[role='heading']", 'span'}:
            if selector == 'span':
                return [FakeElement(text=location) for location in self._locations]
            return [FakeElement(text=self._title)] if self._title else []

        if selector == 'span, div':
            return [FakeElement(text=location) for location in self._locations]

        return []


class FakeKeyboard:
    def press(self, key):
        return None


class FakePage:
    def __init__(self, cards):
        self._cards = cards
        self.keyboard = FakeKeyboard()

    def set_default_timeout(self, timeout):
        return None

    def set_default_navigation_timeout(self, timeout):
        return None

    def goto(self, url, wait_until=None):
        return None

    def wait_for_selector(self, selector, timeout=None):
        return None

    def wait_for_timeout(self, timeout):
        return None

    def query_selector_all(self, selector):
        if selector == 'li, div[role=\'option\']':
            return self._cards
        return []


class FakeContext:
    def __init__(self, page):
        self._page = page

    def new_page(self):
        return self._page


class FakeBrowser:
    def __init__(self, page):
        self._page = page

    def new_context(self, user_agent=None):
        return FakeContext(self._page)

    def close(self):
        return None


class FakeChromium:
    def __init__(self, browser):
        self._browser = browser

    def launch(self, headless=True):
        return self._browser


class FakeSyncPlaywrightCtx:
    def __init__(self, chromium):
        self.chromium = chromium

    def __enter__(self):
        return types.SimpleNamespace(chromium=self.chromium)

    def __exit__(self, exc_type, exc, tb):
        return False


def test_meta_playwright_parses_jobs(monkeypatch):
    page = FakePage([
        FakeCard(
            title='Product Design Intern',
            locations=['Menlo Park, CA'],
            href='https://www.metacareers.com/jobs/m-1'
        ),
        FakeCard(
            title='Senior Product Designer',
            locations=['Remote'],
            href='https://www.metacareers.com/jobs/m-2'
        ),
    ])

    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakeSyncPlaywrightCtx(chromium)

    import scrapers.meta as meta_mod
    monkeypatch.setattr(meta_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(meta_mod, 'sync_playwright', lambda: ctx)

    ms = MetaScraper()
    results = ms.scrape()

    assert isinstance(results, list)
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Product Design Intern'
    assert 'Menlo Park' in job['location']
    assert job['url'].startswith('https://')
    assert isinstance(job['posted_date'], datetime)


def test_meta_playwright_no_playwright_available(monkeypatch):
    import scrapers.meta as meta_mod

    monkeypatch.setattr(meta_mod, 'PLAYWRIGHT_AVAILABLE', False)

    ms = MetaScraper()
    assert ms.scrape() == []
