import types
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class FakeInnerLocator:
    """Simulates Playwright's locator return value with inner_text and get_attribute"""
    def __init__(self, text=None, href=None, elements=None):
        self._text = text
        self._href = href
        self._elements = elements or []

    def inner_text(self, timeout=None):
        return self._text or ''

    def get_attribute(self, name, timeout=None):
        if name == 'href':
            return self._href
        return None

    def first(self):
        """Return self for .first chaining"""
        return self

    def all(self):
        """Return list of elements for .all()"""
        return self._elements if self._elements else [self]

    def count(self):
        """Return count of elements"""
        return len(self._elements) if self._elements else 1


class FakeLocationSpan:
    """Simulates individual location span elements"""
    def __init__(self, text):
        self._text = text

    def inner_text(self, timeout=None):
        return self._text


class FakeCard:
    """Simulates a Google job card (li.lLd3Je)"""
    def __init__(self, title=None, locations=None, href=None, has_more_locations=False):
        self._title = title
        self._locations = locations or []
        self._href = href
        self._has_more = has_more_locations

    def locator(self, selector):
        # Title selector: h3.QJPWVe
        if selector == "h3.QJPWVe":
            return FakeInnerLocator(text=self._title)
        
        # Location container: span.pwO9Dc
        if selector == "span.pwO9Dc":
            # Create a fake location container
            location_spans = [FakeLocationSpan(loc) for loc in self._locations]
            return FakeLocationContainer(location_spans, self._has_more)
        
        # URL selector: a.WpHeLc
        if selector == "a.WpHeLc":
            return FakeInnerLocator(href=self._href)
        
        return FakeInnerLocator()


class FakeLocationContainer:
    """Simulates the location container span.pwO9Dc"""
    def __init__(self, location_spans, has_more=False):
        self._location_spans = location_spans
        self._has_more = has_more

    def first(self):
        return self

    def inner_text(self, timeout=None):
        # Return combined location text
        return "; ".join([span.inner_text() for span in self._location_spans])

    def locator(self, selector):
        # Individual location spans: span.r0wTof
        if selector == "span.r0wTof":
            return FakeInnerLocator(elements=self._location_spans)
        
        # More locations indicator: span.BVHzed, span.Z2gFhf
        if selector in ["span.BVHzed, span.Z2gFhf", "span.BVHzed", "span.Z2gFhf"]:
            return FakeInnerLocator(elements=[FakeLocationSpan("+")] if self._has_more else [])
        
        return FakeInnerLocator()

    def count(self):
        return 1 if self._has_more else 0


class FakeLocatorCollection:
    """Simulates Playwright's locator collection"""
    def __init__(self, cards):
        self._cards = cards

    def count(self):
        return len(self._cards)

    def all(self):
        return self._cards


class FakeMouse:
    def wheel(self, x, y):
        return None


class FakePage:
    """Simulates Playwright page"""
    def __init__(self, cards, raise_on_wait=False, wait_exc=None):
        self._cards = cards
        self._raise = raise_on_wait
        self._wait_exc = wait_exc
        self.mouse = FakeMouse()

    def goto(self, url, timeout=None):
        return None

    def wait_for_selector(self, selector, timeout=None):
        if self._raise:
            raise self._wait_exc or Exception('timeout')
        return None

    def locator(self, selector):
        # Job cards selector: li.lLd3Je
        if selector == 'li.lLd3Je':
            return FakeLocatorCollection(self._cards)
        return FakeLocatorCollection([])


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


class FakeSyncPlaywrightCtx:
    def __init__(self, chromium):
        self.chromium = chromium

    def __enter__(self):
        return types.SimpleNamespace(chromium=self.chromium)

    def __exit__(self, exc_type, exc, tb):
        return False


def test_google_playwright_parses_jobs(monkeypatch):
    """Test that Google scraper correctly parses internship jobs"""
    # Create two cards: one intern, one non-intern
    card1 = FakeCard(
        title='Software Developer Intern, PhD, Summer 2026',
        locations=['Waterloo, ON, Canada', 'Montreal, QC, Canada'],
        href='jobs/results/122888894193509062-software-developer-intern-phd-summer-2026?target_level=INTERN_AND_APPRENTICE',
        has_more_locations=True
    )
    card2 = FakeCard(
        title='Senior Software Engineer',
        locations=['Mountain View, CA, USA'],
        href='jobs/results/999-senior-software-engineer'
    )

    page = FakePage([card1, card2])
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakeSyncPlaywrightCtx(chromium)

    import scrapers.google as google_mod
    # Ensure tests use Playwright path
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    from scrapers.google import GoogleScraper

    gs = GoogleScraper()
    results = gs.scrape()

    assert isinstance(results, list)
    # Only the intern should be returned
    assert len(results) == 1
    job = results[0]
    assert job['title'] == 'Software Developer Intern, PhD, Summer 2026'
    assert 'Waterloo' in job['location']
    assert 'Montreal' in job['location']
    # URL should be properly constructed
    assert 'google.com' in job['url']
    assert '122888894193509062' in job['url']


def test_google_playwright_timeout_fallback(monkeypatch):
    """Test that scraper handles timeout gracefully"""
    import scrapers.google as google_mod

    class TimeoutExc(Exception):
        pass

    # Create a page that raises timeout
    page = FakePage([], raise_on_wait=True, wait_exc=TimeoutExc())
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakeSyncPlaywrightCtx(chromium)

    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)
    # Ensure scraper recognizes Playwright's timeout exception
    monkeypatch.setattr(google_mod, 'PlaywrightTimeout', TimeoutExc, raising=False)

    from scrapers.google import GoogleScraper

    gs = GoogleScraper()
    results = gs.scrape()
    # Timeout should result in empty list
    assert results == []


def test_google_playwright_multiple_locations(monkeypatch):
    """Test handling of jobs with multiple locations"""
    card = FakeCard(
        title='Software Engineering Intern, BS, Summer 2026',
        locations=['New York, NY, USA', 'Seattle, WA, USA', 'Austin, TX, USA'],
        href='jobs/results/123-software-engineering-intern',
        has_more_locations=True
    )

    page = FakePage([card])
    browser = FakeBrowser(page)
    chromium = FakeChromium(browser)
    ctx = FakeSyncPlaywrightCtx(chromium)

    import scrapers.google as google_mod
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', True)
    monkeypatch.setattr(google_mod, 'sync_playwright', lambda: ctx)

    from scrapers.google import GoogleScraper

    gs = GoogleScraper()
    results = gs.scrape()

    assert len(results) == 1
    job = results[0]
    # Should have location info
    assert 'New York' in job['location'] or 'Seattle' in job['location']


def test_google_playwright_no_playwright_available(monkeypatch):
    """Test behavior when Playwright is not available"""
    import scrapers.google as google_mod
    monkeypatch.setattr(google_mod, 'PLAYWRIGHT_AVAILABLE', False)

    from scrapers.google import GoogleScraper

    gs = GoogleScraper()
    results = gs.scrape()
    # Should return empty list when Playwright not available
    assert results == []