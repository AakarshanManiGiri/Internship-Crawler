# NowOnwards

## Objective
Make this repository operational with the smallest possible set of changes. Operational here means:

1. `python main.py` starts and exits without crashing.
2. The scraper pipeline can run end to end with Google and Meta loaded as independent modules.
3. The database layer stores and reads internship rows reliably.
4. Notification delivery does not require hardcoded secrets.
5. The current test suite reflects the current scraper architecture instead of an older one.

This is not a feature plan. Do not add new behavior beyond what is necessary to make the existing code path work.

## Current State

The repository is close to a working shape, but it is not operational as-is.

I ran the test suite with `pytest -q` and got 4 failures out of 6 tests. The failures are not random; they line up with the current code structure:

1. The main crawler crashes at the end because it calls an undefined function in [main.py](main.py#L133).
2. The model layer has invalid defaults for `None` in [models/internship.py](models/internship.py#L12), [models/internship.py](models/internship.py#L14), and [models/internship.py](models/internship.py#L15).
3. Email delivery is hardwired to placeholder credentials in [services/email_service.py](services/email_service.py#L11).
4. The Google tests are written against a fake page object that does not match the current Playwright-based implementation in [scrapers/google.py](scrapers/google.py#L44) and [scrapers/google.py](scrapers/google.py#L105).
5. The Meta tests still expect a GraphQL/session-post flow, but [scrapers/meta.py](scrapers/meta.py#L50) now uses browser automation and Playwright selectors.
6. The README describes setup files and CLI flags that do not exist in the codebase, including `test_setup.py`, `.env.example`, and several unsupported `main.py` flags.
7. `requirements.txt` does not include the FastAPI stack even though [api/api.py](api/api.py#L1) imports FastAPI, CORS middleware, and Pydantic.

## Bare Minimum Fix Set

### 1. Stop the main crawl from crashing

The end of [main.py](main.py#L133) calls `print_health_report()` even though no such function exists anywhere in the repository. That is a hard runtime failure.

Minimum fix:

1. Replace the undefined call with a real helper in `main.py` that prints `BaseScraper.get_health_stats()`.
2. If you want the smallest possible patch, it is also acceptable to remove the call entirely.

Why this is first:

1. It blocks every successful crawl from completing cleanly.
2. It is the only guaranteed runtime crash in the main execution path.

### 2. Make email credentials external and optional

[services/email_service.py](services/email_service.py#L11) still contains placeholder Gmail credentials.

Minimum fix:

1. Read `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, and `SENDER_PASSWORD` from environment variables.
2. If sender credentials are missing, skip notification sending and log the reason instead of failing the crawl.
3. Keep notification delivery as an opt-in dependency, not a hardcoded requirement.

Why this is required:

1. The current code cannot send real mail without editing source.
2. A missing email setup should not break scraping or database writes.

### 3. Fix the model defaults that currently violate type expectations

[models/internship.py](models/internship.py#L12), [models/internship.py](models/internship.py#L14), and [models/internship.py](models/internship.py#L15) declare `None` defaults on non-optional types.

Minimum fix:

1. Annotate `posted_date`, `requirements`, and `created_at` as optional.
2. Keep the current fallback behavior that replaces `None` with `datetime.now()` or an empty list.

Why this matters:

1. It removes the static type errors already reported by the checker.
2. It keeps object creation aligned with the scraper output, which may omit fields.

### 4. Align the tests with the current scraper implementation

The current tests are the main reason the suite is failing, but the problem is not the assertions themselves. The test doubles are modeled after an older implementation shape.

Minimum fix for Google:

1. Update the fake page object in [tests/test_google_scraper.py](tests/test_google_scraper.py#L116) so it exposes the methods used by [scrapers/google.py](scrapers/google.py#L44) and [scrapers/google.py](scrapers/google.py#L105).
2. Add `set_default_timeout`, `set_default_navigation_timeout`, `query_selector_all`, `keyboard.press`, and `wait_for_timeout` to the stub where needed.
3. Keep the tests focused on the current Playwright page contract, not the old locator chain.

Minimum fix for Meta:

1. Replace the GraphQL-session mock in [tests/test_meta_scraper.py](tests/test_meta_scraper.py#L17) and [tests/test_meta_scraper.py](tests/test_meta_scraper.py#L51) with Playwright-style page and browser fakes.
2. Mock the selectors and page traversal that [scrapers/meta.py](scrapers/meta.py#L68) and [scrapers/meta.py](scrapers/meta.py#L110) actually use.
3. Keep one fallback test for the Playwright-not-installed path, because that is the one stable branch already present in the code.

Why this is required:

1. The current test suite does not validate the real code path.
2. The repo cannot claim to be operational if its own tests fail because of stale fixtures.

### 5. Make the dependency list match the actual imports

[requirements.txt](requirements.txt) is incomplete for the API module.

Minimum fix:

1. Add `fastapi`, `uvicorn`, and `pydantic` to `requirements.txt`.
2. Keep the existing scraper dependencies in place.
3. Do not introduce extra packages beyond the imports already present in the repo.

Why this is required:

1. `api/api.py` imports these packages directly.
2. A fresh install from `requirements.txt` should not produce an import failure in a supported module.

### 6. Remove or replace README instructions that point to missing code

The README is currently ahead of the codebase.

Minimum fix:

1. Either create a tiny `test_setup.py` and `.env.example`, or remove those references from [README.md](README.md#L91) and [README.md](README.md#L95).
2. Remove the unsupported CLI commands from the documentation unless you plan to implement them immediately.
3. Keep only the commands that already work today, or add the exact minimal code needed to support the documented commands.

Why this is part of operational readiness:

1. Setup instructions are part of the first-run path.
2. Broken docs make the repository effectively non-operational for a new user even if the code imports.

## What Works Already

These parts are structurally sound enough to keep:

1. [database/db.py](database/db.py) creates and uses SQLite tables for internships and users.
2. [scrapers/base_scraper.py](scrapers/base_scraper.py) provides a reusable shared session and health tracking.
3. [scrapers/google.py](scrapers/google.py) and [scrapers/meta.py](scrapers/meta.py) both have clear scraper entry points and return normalized dictionaries when they succeed.
4. [api/api.py](api/api.py) has a functional FastAPI route shape and can serve internship data once dependencies are installed.

These do not need redesign. They need the minimum integration fixes above so they can cooperate without falling over.

## Dependency Chain

The project only becomes operational if these pieces line up in this order:

1. Scrapers return normalized internship dictionaries.
2. `main.py` converts those dictionaries into `Internship` objects.
3. `database/db.py` persists those objects and prevents duplicates by URL.
4. `NotificationService` and `EmailService` run only when credentials are present.
5. The API reads the same database rows back out.

If any one of those steps fails, the project is not operational even if the others look fine in isolation.

## Exact Minimal Implementation Order

1. Fix `main.py` so it finishes a crawl without crashing.
2. Fix `EmailService` so credentials come from the environment and missing credentials do not break the crawl.
3. Fix the optional typing errors in `models/internship.py`.
4. Update `requirements.txt` to include the FastAPI stack.
5. Rewrite the Google tests to match the current Playwright scraper contract.
6. Rewrite the Meta tests to match the current Playwright scraper contract.
7. Trim or correct README setup instructions so the documented first-run path is real.

## Non-Goals

Do not use the operational cleanup as an excuse to add any of the following:

1. New scraping targets.
2. New notification channels.
3. New filtering logic.
4. New scheduling features.
5. A full CLI redesign.

The repo only needs to work as it exists now.

## Bottom Line

This project is blocked by a small set of mismatches, not by missing architecture. The minimum viable path is to fix the main crash, externalize email credentials, correct the model typing, make the dependency list truthful, and rewrite the stale tests and docs so they match the current Playwright-based scraper design.