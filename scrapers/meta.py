from datetime import datetime
from typing import Dict, List
import json
from urllib.parse import urljoin

try:
    from dateutil import parser as date_parser
except Exception:
    date_parser = None

from scrapers.base_scraper import BaseScraper
class MetaScraper(BaseScraper):
    
    def get_company_name(self) -> str:
        return "Meta"
    
    def get_careers_url(self) -> str:
        return "https://www.metacareers.com/jobs"
    
    def scrape(self) -> List[Dict]:
        """Scrape Meta's careers page"""
        positions = []
        
        try:
            # Meta uses a GraphQL backend (POST to /api/graphql/)
            api_url = 'https://www.metacareers.com/api/graphql/'

            # GraphQL query - filters can be customized
            query = '''
            query($search: String, $location: String) {
              jobs(filters: {search_term: $search, location: $location}) {
                id
                title
                location
                apply_url
                posted_date
                description
              }
            }
            '''

            # Try variables named to match service schema (e.g., search_term)
            payload = {'query': query, 'variables': {'search_term': 'intern', 'location': ''}}

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': self.session.headers.get('User-Agent'),
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://www.metacareers.com'
            }

            # Try initial GraphQL POST
            response = None
            last_exc = None
            try:
                response = self.session.post(api_url, data=json.dumps(payload), headers=headers, timeout=10)
                response.raise_for_status()
            except Exception as e:
                last_exc = e

                # Try a different payload style (inline query) and include common needed headers
                inline_query = '''{ jobs(filters: {search_term: "intern", location: ""}) { id title location apply_url posted_date description } }'''
                headers['Referer'] = self.careers_url
                try:
                    response = self.session.post(api_url, data=json.dumps({'query': inline_query}), headers=headers, timeout=10)
                    response.raise_for_status()
                except Exception as e2:
                    last_exc = e2
                    response = None

            if response is None:
                # Give a helpful error message but don't crash the whole crawler
                print(f"{self.company_name}: GraphQL query failed: {last_exc}")
                # Fallback: attempt to scrape the careers URL HTML (best-effort)
                try:
                    html_resp = self.session.get(f"{self.careers_url}?q=intern", timeout=10)
                    html_resp.raise_for_status()
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_resp.text, 'html.parser')
                    # heuristics: try a few common selectors
                    possible_cards = soup.select('.job-card, .job-list-item, .search-result, li.job')
                    for card in possible_cards:
                        title_el = card.select_one('.job-title, .title, h3, h2')
                        if not title_el:
                            continue
                        title = title_el.text.strip()
                        if not self.is_internship(title):
                            continue
                        url_el = card.select_one('a')
                        url = url_el['href'] if url_el and url_el.get('href') else ''
                        if url and not url.startswith('http'):
                            url = urljoin(self.careers_url, url)
                        loc_el = card.select_one('.job-location, .location')

                        positions.append({
                            'title': title,
                            'location': loc_el.text.strip() if loc_el else '',
                            'url': url,
                            'posted_date': None,
                            'description': (card.select_one('.job-description').text.strip() if card.select_one('.job-description') else ''),
                            'requirements': []
                        })

                except Exception as html_err:
                    print(f"{self.company_name}: HTML fallback failed: {html_err}")
                return positions

            try:
                result = response.json()
            except ValueError:
                print(f"{self.company_name}: GraphQL response not JSON")
                return positions

            jobs = result.get('data', {}).get('jobs', [])

            for job in jobs:
                title = job.get('title', '')
                if not self.is_internship(title):
                    continue

                posted_date = None
                if job.get('posted_date'):
                    parsed = None
                    if date_parser:
                        try:
                            parsed = date_parser.parse(job['posted_date'])
                        except Exception:
                            parsed = None

                    if parsed is None:
                        try:
                            parsed = datetime.fromisoformat(job['posted_date'])
                        except Exception:
                            parsed = None

                    posted_date = parsed

                url = job.get('apply_url') or job.get('url') or job.get('id')
                if url and not url.startswith('http'):
                    url = urljoin(self.careers_url, url)

                positions.append({
                    'title': title,
                    'location': job.get('location', ''),
                    'url': url,
                    'posted_date': posted_date,
                    'description': job.get('description', '') or '',
                    'requirements': []
                })
        
        except Exception as e:
            print(f"Error scraping {self.company_name}: {e}")
        
        return positions