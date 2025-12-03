#  Internship Crawler

> Automated Modular Web Crawler that tracks tech company internship postings and sends instant notifications when new positions go live.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Never miss an internship opportunity again! This tool automatically monitors career pages from top tech companies and notifies you the moment new positions are posted.


---

##  Features

-  **Smart Crawling** - Automatically detects internship positions across multiple companies
-  **Instant Notifications** - Email alerts with direct apply links when new positions drop
-  **Modular Architecture** - Add or remove companies with a single Python file
-  **Duplicate Prevention** - Never get notified twice about the same position
-  **User Preferences** - Filter by company, location, or keywords
-  **Database Tracking** - SQLite database tracks all positions and notification history
-  **Automated Scheduling** - Set it and forget it with cron jobs or Windows Task Scheduler
-  **Seed Mode** - Populate database initially without spamming users

---

## Table of Contents

- [Demo](#-demo)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Adding New Companies](#-adding-new-companies)
- [Architecture](#-architecture)
- [Deployment](#-deployment)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

##  Demo

**Email Notification Example:**

```
Subject: 🚀 3 New Internship(s) Posted!

Google - Software Engineering Intern, Summer 2025
Location: Mountain View, CA
Posted: 2024-12-03
[Apply Now]

Meta - Data Science Intern
Location: Menlo Park, CA  
Posted: 2024-12-03
[Apply Now]

Microsoft - PM Intern
Location: Redmond, WA
Posted: 2024-12-03
[Apply Now]
```

---

##  Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/internship-crawler.git
cd internship-crawler

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright (for JavaScript-heavy sites like Google)
playwright install chromium

# 5. Configure email settings
cp .env.example .env
# Edit .env with your email credentials

# 6. Setup test database
python test_setup.py

# 7. Run a test crawl
python main.py --dry-run

# 8. Do initial seed (saves all positions without notifying)
python main.py --seed

# 9. Run normal crawl (only notifies about NEW positions)
python main.py
```

---

##  Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Gmail account (for email notifications)

### Step-by-Step Installation

#### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/internship-crawler.git
cd internship-crawler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**For JavaScript-heavy sites (Google, Meta, Netflix):**
```bash
pip install playwright
playwright install chromium
```

#### 3. Verify Installation

```bash
python -c "import requests, bs4; print('✓ Basic dependencies OK')"
python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"
```

---

##  Configuration

### Email Setup (Gmail)

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**: 
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Create `.env` file**:

```bash
cp .env.example .env
```

4. **Edit `.env` file**:

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password

# Database
DATABASE_PATH=internships.db

# Scheduler
CRAWL_INTERVAL_HOURS=2
```

### Add Users

Edit `test_setup.py` to add your email:

```python
test_users = [
    ("your-email@gmail.com", "{'companies': [], 'locations': []}"),
]
```

Then run:
```bash
python test_setup.py
```

---

##  Usage

### Command Line Interface

```bash
# Normal crawl (notify about new positions)
python main.py

# Initial seed (save all without notifying)
python main.py --seed

# Test without saving/notifying
python main.py --dry-run

# Crawl without sending notifications
python main.py --no-notify

# Show database statistics
python main.py --stats

# Show recent internships (last 24 hours)
python main.py --recent 24

# Clear all internships
python main.py --clear
```

### Crawl Modes Explained

| Mode | Saves to DB | Sends Notifications | Use Case |
|------|-------------|---------------------|----------|
| `--seed` | ✅ | ❌ | First run to populate database |
| Normal | ✅ | ✅ | Daily/hourly scheduled runs |
| `--dry-run` | ❌ | ❌ | Testing new scrapers |
| `--no-notify` | ✅ | ❌ | Save data without emailing |

### Recommended Workflow

```bash
# Day 1: Initial setup
python main.py --seed

# Day 2+: Schedule to run every 2 hours
python main.py
```

---

##  Architecture

```
internship-crawler/
├── scrapers/              # Company-specific scrapers
│   ├── base_scraper.py   # Abstract base class
│   ├── google.py         # Google Careers scraper
│   ├── meta.py           # Meta Careers scraper
│   ├── microsoft.py      # Microsoft scraper
│   └── mock_*.py         # Test scrapers
├── models/               # Data models
│   ├── internship.py     # Internship model
│   └── user.py           # User model
├── services/             # Business logic
│   ├── notification_service.py
│   └── email_service.py
├── database/             # Database operations
│   └── db.py             # SQLite wrapper
├── config/               # Configuration
│   └── settings.py
├── main.py               # Entry point
├── test_setup.py         # Test data setup
├── test_runner.py        # Test suite
├── requirements.txt      # Dependencies
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

### Database Schema

**internships** table:
```sql
- id (PRIMARY KEY)
- company (TEXT)
- title (TEXT)
- location (TEXT)
- url (TEXT UNIQUE)
- posted_date (DATETIME)
- description (TEXT)
- requirements (TEXT)
- created_at (DATETIME)
- notified (BOOLEAN)
```

**users** table:
```sql
- id (PRIMARY KEY)
- email (TEXT UNIQUE)
- preferences (JSON)
- created_at (DATETIME)
```

---

## Adding New Companies

Adding a new company takes **less than 5 minutes**!

### Simple Example (HTML-based site)

Create `scrapers/your_company.py`:

```python
from typing import List, Dict
from datetime import datetime
from scrapers.base_scraper import BaseScraper
import requests
from bs4 import BeautifulSoup

class YourCompanyScraper(BaseScraper):
    
    def get_company_name(self) -> str:
        return "YourCompany"
    
    def get_careers_url(self) -> str:
        return "https://yourcompany.com/careers"
    
    def scrape(self) -> List[Dict]:
        positions = []
        
        try:
            response = requests.get(self.careers_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Adjust selectors based on actual website
            jobs = soup.select('.job-listing')
            
            for job in jobs:
                title = job.select_one('.title').text.strip()
                
                if self.is_internship(title):
                    positions.append({
                        'title': title,
                        'location': job.select_one('.location').text.strip(),
                        'url': job.select_one('a')['href'],
                        'posted_date': datetime.now(),
                        'description': '',
                        'requirements': []
                    })
        
        except Exception as e:
            print(f"Error: {e}")
        
        return positions
```

**That's it!** The system automatically discovers and loads your scraper.

### For JavaScript Sites (Requires Playwright)

```python
from playwright.sync_api import sync_playwright

class JavaScriptCompanyScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        positions = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.careers_url)
            
            # Wait for content to load
            page.wait_for_selector('.job-card')
            
            # Extract data
            jobs = page.query_selector_all('.job-card')
            # ... rest of scraping logic
            
            browser.close()
        
        return positions
```

---

##  Deployment

### Option 1: Local Machine with Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run every 2 hours
0 */2 * * * cd /path/to/internship-crawler && /path/to/venv/bin/python main.py
```

### Option 2: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 2 hours)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `C:\path\to\internship-crawler\main.py`

### Option 3: Cloud VM (AWS EC2, DigitalOcean, etc.)

```bash
# SSH into your server
ssh user@your-server-ip

# Clone and setup (follow installation steps)
# Setup cron job as above

# Keep running with screen
screen -S crawler
python schedule_example.py
# Ctrl+A then D to detach
```

### Option 4: Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["python", "schedule_example.py"]
```

```bash
docker build -t internship-crawler .
docker run -d --env-file .env internship-crawler
```

### Option 5: Serverless (AWS Lambda)

Use AWS Lambda with EventBridge for scheduled execution. Package your code with dependencies as a Lambda layer.

---

##  Testing

### Run All Tests

```bash
python test_runner.py
```

### Test Individual Components

```bash
# Test database
python -c "from database.db import Database; db = Database('test.db'); print(f'Users: {len(db.get_all_users())}')"

# Test email formatting
python -c "from services.email_service import EmailService; es = EmailService(); print('Email service OK')"

# Test specific scraper
python -c "from scrapers.google import GoogleScraper; g = GoogleScraper(); print(g.scrape())"
```

### Mock Scrapers for Testing

Use the included mock scrapers that generate fake data:
- `mock_google.py`
- `mock_meta.py`
- `mock_microsoft.py`

These don't make real HTTP requests and are perfect for testing the notification system.

---

##  Troubleshooting

### Email Not Sending

**Problem:** Notifications not arriving

**Solutions:**
- ✅ Verify Gmail App Password (not your regular password)
- ✅ Check 2FA is enabled on Google account
- ✅ Ensure firewall allows SMTP port 587
- ✅ Check spam folder
- ✅ Try with a test script:
  ```python
  from services.email_service import EmailService
  es = EmailService()
  # Check if credentials loaded
  print(f"Email: {es.sender_email}")
  ```

### Playwright Issues

**Problem:** `playwright: command not found`

**Solution:**
```bash
# Make sure you're in virtual environment
python -m playwright install chromium
```

**Problem:** `Browser not found`

**Solution:**
```bash
playwright install chromium
```

### No Jobs Found

**Problem:** Scraper returns 0 positions

**Solutions:**
- ✅ Website HTML structure may have changed
- ✅ Use `--dry-run` to see what's happening
- ✅ Check if site requires JavaScript (use Playwright)
- ✅ Verify URL is still valid
- ✅ Test with mock scrapers first

### Database Locked

**Problem:** `database is locked` error

**Solution:**
```bash
# Close any other processes using the database
# Or delete and recreate
rm internships.db
python test_setup.py
```

---


##  Contributing

Contributions are welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
   ```bash
   python test_runner.py
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Contribution Ideas

-  Add scrapers for more companies
-  Build a web dashboard
-  Add Slack/Discord notifications
-  Implement ML for position recommendations
-  Add internationalization
-  Create analytics dashboard
-  Improve test coverage

### Code Style

We use [Black](https://github.com/psf/black) for code formatting:

```bash
pip install black
black .
```

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- Built with [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Playwright](https://playwright.dev/) for JavaScript rendering
- Inspired by the job hunting struggles of CS students everywhere
- Thanks to all contributors who help maintain company scrapers

---

## Support

-  **Bug Reports**: [Open an issue](https://github.com/yourusername/internship-crawler/issues)
-  **Feature Requests**: [Open an issue](https://github.com/yourusername/internship-crawler/issues)
-  **Questions**: [Discussions](https://github.com/yourusername/internship-crawler/discussions)

---

## Roadmap

- [x] Core crawling functionality
- [x] Email notifications
- [x] Modular scraper architecture
- [x] Database persistence
- [ ] Web dashboard
- [ ] User authentication
- [ ] Advanced filtering
- [ ] Machine learning recommendations
- [ ] Mobile app
- [ ] Browser extension
- [ ] Support for 100+ companies
- [ ] Real-time notifications (WebSocket)
- [ ] Salary data tracking
- [ ] Application deadline reminders

---

## Star History

If this project helped you land an internship, consider giving it a star! ⭐

---
