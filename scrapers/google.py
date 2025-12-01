from datetime import datetime
from typing import Dict, List
from urllib.parse import urljoin

try:
    from dateutil import parser as date_parser
except Exception:
    date_parser = None

from scrapers.base_scraper import BaseScraper

class GoogleScraper(BaseScraper):
    
    def get_company_name(self) -> str:
        return "Google"
    
    def get_careers_url(self) -> str:
        return "https://www.google.com/about/careers/applications/jobs/results/"
    
    def scrape(self) -> List[Dict]:
        """Scrape Google's careers API"""
        positions = []
        
        try:
            # Try several known Google careers JSON endpoints (some setups redirect)
            endpoints = [
                "https://careers.google.com/api/v1/jobs/search/",
                "https://careers.google.com/api/v1/search/",
                # some sites may redirect to this pattern; try as last resort
                urljoin(self.careers_url, 'api/v1/jobs/search/')
            ]

            params = {'query': 'intern', 'employment_type': 'INTERN', 'limit': 50}

            response = None
            last_exc = None
            for api_url in endpoints:
                try:
                    # Do an initial request without following redirects to avoid
                    # being sent from careers.google.com -> www.google.com/about/careers/... which can break paths
                    resp = self.session.get(api_url, params=params, timeout=10, allow_redirects=False)
                    # If a redirect happened, follow the redirect target explicitly but preserve absolute path
                    if resp.status_code in (301, 302, 303, 307, 308) and 'Location' in resp.headers:
                        # Use the absolute location from headers
                        redirect_url = resp.headers['Location']
                        resp = self.session.get(redirect_url, params=params, timeout=10)

                    resp.raise_for_status()
                    response = resp
                    break
                except Exception as e:
                    last_exc = e
                    # try next endpoint
                    response = None

            if response is None:
                raise last_exc
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                # not JSON → nothing to parse
                print(f"{self.company_name}: response not JSON")
                return positions

            for job in data.get('jobs', []):
                title = job.get('title', '')
                if not self.is_internship(title):
                    continue

                # parse locations which may be a list or a string
                locs = job.get('locations') or job.get('location') or []
                if isinstance(locs, str):
                    loc_text = locs
                else:
                    loc_text = ', '.join(locs)

                # try multiple date formats - fallback to None
                posted_raw = job.get('posted_date') or job.get('posting_date') or job.get('date')
                posted_date = None
                if posted_raw:
                    parsed = None
                    if date_parser:
                        try:
                            parsed = date_parser.parse(posted_raw)
                        except Exception:
                            parsed = None

                    if parsed is None:
                        try:
                            parsed = datetime.fromisoformat(posted_raw)
                        except Exception:
                            parsed = None

                    posted_date = parsed

                url = job.get('apply_url') or job.get('url') or job.get('id')
                if url and not url.startswith('http'):
                    url = urljoin(self.careers_url, url)

                positions.append({
                    'title': title,
                    'location': loc_text,
                    'url': url,
                    'posted_date': posted_date,
                    'description': job.get('description', ''),
                    'requirements': job.get('qualifications', []) or job.get('requirements', [])
                })
        
        except Exception as e:
            print(f"Error scraping {self.company_name}: {e}")
        
        return positions