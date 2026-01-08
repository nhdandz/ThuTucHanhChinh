"""
Antibot Crawler
===============

Advanced crawler for anti-bot protected websites with news and file download support.

Features:
- Playwright Stealth mode for anti-bot bypass
- News article extraction with metadata
- Multi-level file download
- Exponential backoff retry logic
- Error screenshots for debugging
- Comprehensive file logging

Author: Claude
Date: 2026-01-02
"""

# Standard library imports
import asyncio
import json
import logging
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional
from urllib.parse import urljoin, urlparse, unquote
from logging.handlers import RotatingFileHandler

# Third-party imports
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

# Type definitions
CrawlMode = Literal['one_level', 'two_level', 'multi_level', 'news']
WebType = Literal['ssr', 'csr', 'antibot']

# Constants
WORK_DIR = Path(__file__).parent
DOWNLOAD_DIR = WORK_DIR / 'downloaded_files'
NEWS_DIR = WORK_DIR / 'news_articles'
LOG_DIR = WORK_DIR / 'logs'
SCREENSHOT_DIR = LOG_DIR / 'screenshots'

# Files
INPUT_FILE = WORK_DIR / 'antibot_urls.json'
OUTPUT_FILE = WORK_DIR / 'output_antibot.json'

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CrawlerConfig:
    """Configuration for a single URL to crawl."""
    url: str
    crawl_mode: CrawlMode = 'one_level'
    levels: Optional[List[Dict[str, Any]]] = None
    file_extensions: Optional[List[str]] = None
    web_type: WebType = 'antibot'
    max_pages: int = 100

    # Legacy support
    level1_selector: Optional[Dict[str, str]] = None
    level2_selector: Optional[Dict[str, str]] = None
    region_selector: Optional[Dict[str, str]] = None
    max_detail_pages: Optional[int] = None


@dataclass
class CrawlerOptions:
    """Global crawler options."""
    timeout: int = 30
    delay_between_requests: float = 2.0
    max_files: int = 0  # 0 = unlimited
    headless: bool = True
    retry_enabled: bool = True
    screenshot_on_error: bool = True
    log_level: str = 'INFO'


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    initial_delay: float = 2.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0


# ============================================================================
# Utility Functions
# ============================================================================

def setup_logger(
    name: str = 'antibot_crawler',
    log_dir: Path = LOG_DIR,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup logger with file and console handlers.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # File handler with rotation
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / f'{name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s | %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """
    Clean filename by removing special characters.

    Args:
        title: Original filename/title
        max_length: Maximum length

    Returns:
        Sanitized filename
    """
    filename = re.sub(r'[^\w\s-]', '', title)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename[:max_length]


def get_filename(url: str) -> str:
    """
    Extract filename from URL.

    Args:
        url: File URL

    Returns:
        Filename
    """
    path = urlparse(url).path
    filename = unquote(os.path.basename(path))
    if not filename or filename == '/':
        filename = f'file_{hash(url) % 100000}'
    if '.' not in filename:
        filename = filename + '.bin'
    return filename


def is_downloadable(url: str, exts: List[str]) -> bool:
    """
    Check if URL has downloadable extension.

    Args:
        url: URL to check
        exts: List of extensions (e.g. ['.pdf', '.docx'])

    Returns:
        True if URL ends with any extension
    """
    return any(urlparse(url.lower()).path.endswith(e) for e in exts)


def is_same_domain(url: str, base: str) -> bool:
    """
    Check if URLs are from same domain.

    Args:
        url: URL to check
        base: Base URL

    Returns:
        True if same domain
    """
    return urlparse(base).netloc == urlparse(url).netloc


def extract_links(
    html: str,
    base: str,
    selector: Optional[Dict[str, str]] = None,
    exts: Optional[List[str]] = None,
    require_ext: bool = False
) -> List[str]:
    """
    Extract links from HTML using BeautifulSoup.

    Args:
        html: HTML content
        base: Base URL for joining relative links
        selector: CSS selector dict with 'type' and 'selector' keys
        exts: File extensions to filter
        require_ext: If True, only return links with specified extensions

    Returns:
        List of absolute URLs
    """
    soup = BeautifulSoup(html, 'lxml')
    links, seen = [], set()

    if selector and selector.get('selector') and selector.get('type') == 'css':
        for elem in soup.select(selector['selector']):
            if elem.name == 'a' and elem.get('href'):
                u = urljoin(base, elem['href'])
                if u not in seen:
                    seen.add(u)
                    links.append(u)
            for a in elem.find_all('a', href=True):
                u = urljoin(base, a['href'])
                if u not in seen:
                    seen.add(u)
                    links.append(u)
    else:
        for a in soup.find_all('a', href=True):
            u = urljoin(base, a['href'])
            if u not in seen:
                if require_ext and exts:
                    if is_downloadable(u, exts):
                        seen.add(u)
                        links.append(u)
                else:
                    seen.add(u)
                    links.append(u)

    return links


# ============================================================================
# Retry and Screenshot Logic
# ============================================================================

async def retry_with_backoff(
    func: Callable,
    *args,
    config: RetryConfig = RetryConfig(),
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        config: Retry configuration
        logger: Logger instance
        *args, **kwargs: Arguments for func

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    delay = config.initial_delay
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < config.max_retries:
                if logger:
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                await asyncio.sleep(delay)
                delay = min(delay * config.backoff_factor, config.max_delay)
            else:
                if logger:
                    logger.error(f"All {config.max_retries} retries failed")
                raise

    raise last_exception


async def capture_screenshot(
    page: Page,
    name: str,
    logger: Optional[logging.Logger] = None,
    screenshot_dir: Path = SCREENSHOT_DIR
) -> Optional[str]:
    """
    Capture screenshot with error handling.

    Args:
        page: Playwright Page instance
        name: Screenshot name description
        logger: Logger instance
        screenshot_dir: Directory to save screenshots

    Returns:
        Path to screenshot or None if failed
    """
    try:
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{sanitize_filename(name)}_{timestamp}.png"
        filepath = screenshot_dir / filename

        await page.screenshot(path=str(filepath), full_page=True)

        if logger:
            logger.info(f"Screenshot saved: {filepath}")

        return str(filepath)

    except Exception as e:
        if logger:
            logger.error(f"Screenshot failed: {e}")
        return None


# ============================================================================
# Main Crawler Class
# ============================================================================

class AntibotCrawler:
    """
    Main crawler class for anti-bot protected websites.

    Supports:
    - News extraction with stealth mode
    - Multi-level file download
    - Retry logic with exponential backoff
    - Screenshot capture on errors
    - Comprehensive logging
    """

    def __init__(
        self,
        config: CrawlerConfig,
        options: CrawlerOptions,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize crawler.

        Args:
            config: URL configuration
            options: Global options
            logger: Logger instance
        """
        self.config = config
        self.options = options
        self.logger = logger or logging.getLogger(__name__)

        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright_instance = None

        self.results: Dict[str, Any] = {
            'url': config.url,
            'status': 'pending',
            'articles': [],
            'files': [],
            'levels': []
        }

        self.retry_config = RetryConfig()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def setup_browser(self) -> None:
        """Initialize Playwright browser with stealth mode."""
        self.logger.info("Setting up browser with stealth mode...")

        self.playwright_instance = await async_playwright().start()

        self.browser = await self.playwright_instance.chromium.launch(
            headless=self.options.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )

        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(USER_AGENTS),
            locale='vi-VN',
            timezone_id='Asia/Ho_Chi_Minh'
        )

        self.page = await self.context.new_page()

        # Apply stealth - playwright-stealth v2 API
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)

        self.logger.info("Browser ready with stealth mode")

    async def cleanup(self) -> None:
        """Cleanup browser resources."""
        if self.browser:
            await self.browser.close()
            self.logger.info("Browser closed")
        if self.playwright_instance:
            await self.playwright_instance.stop()

    async def crawl(self) -> Dict[str, Any]:
        """
        Main entry point - route based on crawl_mode.

        Returns:
            Results dictionary
        """
        self.logger.info(f"Starting crawl: {self.config.url}")
        self.logger.info(f"Mode: {self.config.crawl_mode}")

        try:
            if self.config.crawl_mode == 'news':
                return await self.crawl_news()
            elif self.config.crawl_mode == 'multi_level':
                return await self.crawl_multi_level()
            elif self.config.crawl_mode == 'two_level':
                return await self.crawl_two_level()
            else:
                return await self.crawl_one_level()

        except Exception as e:
            self.logger.error(f"Crawl failed: {e}", exc_info=True)
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            return self.results

    async def crawl_news(self) -> Dict[str, Any]:
        """
        News extraction mode.

        Flow:
        1. Visit homepage first (anti-bot evasion)
        2. Navigate to news listing
        3. Extract article links
        4. For each article: crawl content
        5. Handle pagination

        Returns:
            Results dictionary with articles
        """
        url = self.config.url
        max_pages = 1000
        max_articles = 10000000000
        delay = self.options.delay_between_requests

        self.logger.info(f"News mode: max_pages={max_pages}, max_articles={max_articles}")

        NEWS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Visit homepage first (anti-bot evasion strategy from CSR crawler cell 10)
            self.logger.info("Step 1: Visiting homepage to avoid anti-bot...")
            base_domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

            await retry_with_backoff(
                self.page.goto,
                base_domain,
                wait_until='domcontentloaded',
                timeout=self.options.timeout * 1000,
                config=self.retry_config,
                logger=self.logger
            )
            await self.page.wait_for_timeout(3000)

            # Step 2: Navigate to news page
            self.logger.info("Step 2: Navigating to news page...")
            await retry_with_backoff(
                self.page.goto,
                url,
                wait_until='domcontentloaded',
                timeout=self.options.timeout * 1000,
                config=self.retry_config,
                logger=self.logger
            )
            await self.page.wait_for_timeout(5000)

            # Check for anti-bot protection
            html_check = await self.page.content()
            if '403 Forbidden' in html_check or 'Access Denied' in html_check:
                self.logger.error("Anti-bot detected: 403 Forbidden")
                await capture_screenshot(
                    self.page,
                    "error_403_forbidden",
                    self.logger
                )
                self.results['status'] = 'failed'
                self.results['error'] = '403 Forbidden - Anti-bot protection'
                return self.results

            # Scroll to load content (simulate human behavior)
            for _ in range(3):
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(2000)
            await self.page.evaluate('window.scrollTo(0, 0)')
            await self.page.wait_for_timeout(2000)

            current_page = 1

            # Step 3: Pagination loop
            while current_page <= max_pages:
                self.logger.info(f"=== Page {current_page} ===")
                await self.page.wait_for_timeout(int(delay * 1000))

                # Store the current listing page URL BEFORE extracting articles
                listing_page_url = self.page.url
                self.logger.debug(f"Current listing URL: {listing_page_url[:80]}...")

                # Wait for pagination to load (dynamic JS)
                try:
                    # Wait for any pagination element to appear
                    await self.page.wait_for_selector('div.page, div[class*="page"]', timeout=10000)
                except Exception:
                    self.logger.warning("Pagination selector not found after 10s")

                # Extract with BeautifulSoup
                html = await self.page.content()
                soup = BeautifulSoup(html, 'lxml')

                # Find articles
                article_items = soup.select('div.itemnew-inlist')
                item_count = len(article_items)
                self.logger.info(f"Found {item_count} articles")

                if item_count == 0:
                    self.logger.warning("No articles found - check selectors or anti-bot")
                    await capture_screenshot(
                        self.page,
                        f"no_articles_page_{current_page}",
                        self.logger
                    )
                    break

                # Process each article
                for i, item in enumerate(article_items):
                    if max_articles > 0 and len(self.results['articles']) >= max_articles:
                        self.logger.info(f"Reached max articles: {max_articles}")
                        break

                    try:
                        link_tag = item.select_one('h5.titleLeftNews a')
                        if link_tag and link_tag.get('href'):
                            article_url = link_tag['href']
                            article_title = link_tag.get_text(strip=True)

                            time_tag = item.select_one('div.time-post')
                            article_time = time_tag.get_text(strip=True) if time_tag else ''

                            self.logger.info(f"[{i+1}] {article_title[:50]}...")

                            # Crawl article detail
                            article_data = await self.crawl_news_article(
                                article_url,
                                url
                            )
                            article_data['time_post'] = article_time
                            article_data['title_from_list'] = article_title

                            self.results['articles'].append(article_data)

                            # Return to listing page using the stored URL
                            self.logger.debug(f"Returning to listing page...")
                            await self.page.goto(
                                listing_page_url,
                                wait_until='domcontentloaded',
                                timeout=30000
                            )
                            await self.page.wait_for_timeout(int(delay * 1000))

                    except Exception as e:
                        self.logger.error(f"Error at article {i+1}: {e}")

                if max_articles > 0 and len(self.results['articles']) >= max_articles:
                    break

                # Handle pagination - try to find and click the next page link
                try:
                    next_page_num = current_page + 1
                    next_link = None

                    self.logger.debug(f"Looking for page {next_page_num}...")

                    # Strategy 1: Look for any <a> tag with text matching next page number
                    # This works for most pagination structures
                    all_page_links = self.page.locator('a')
                    link_count = await all_page_links.count()

                    for i in range(link_count):
                        try:
                            link = all_page_links.nth(i)
                            link_text = await link.inner_text()
                            link_text_stripped = link_text.strip()

                            # Check if this is the next page number
                            if link_text_stripped == str(next_page_num):
                                # Verify it's not already active
                                parent_classes = await link.evaluate('el => el.parentElement ? el.parentElement.className : ""')

                                if 'active' not in parent_classes:
                                    next_link = link
                                    self.logger.info(f"Found next page link (text: '{link_text_stripped}')")
                                    break
                        except Exception:
                            continue

                    # Strategy 2: If not found, try finding by title attribute
                    if not next_link:
                        title_link = self.page.locator(f'a[title*="page {next_page_num}"]')
                        if await title_link.count() > 0:
                            next_link = title_link.first
                            self.logger.info(f"Found next page link (by title)")

                    # Strategy 3: Try common pagination class patterns
                    if not next_link:
                        patterns = [
                            f'a.page-link:has-text("{next_page_num}")',
                            f'a.pagination-link:has-text("{next_page_num}")',
                            f'li:not(.active) a:has-text("{next_page_num}")',
                        ]
                        for pattern in patterns:
                            loc = self.page.locator(pattern)
                            if await loc.count() > 0:
                                next_link = loc.first
                                self.logger.info(f"Found next page link (pattern: {pattern})")
                                break

                    if next_link:
                        self.logger.info(f"Navigating to page {next_page_num}...")

                        # Click and wait for navigation
                        await next_link.click()
                        await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                        await self.page.wait_for_timeout(5000)

                        # Scroll to load content
                        for _ in range(3):
                            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            await self.page.wait_for_timeout(2000)
                        await self.page.evaluate('window.scrollTo(0, 0)')
                        await self.page.wait_for_timeout(2000)

                        # Log current URL after navigation
                        current_url = self.page.url
                        self.logger.info(f"Current URL after navigation: {current_url[:100]}...")

                        # Wait for articles to appear after page change
                        try:
                            await self.page.wait_for_selector('div.itemnew-inlist', timeout=15000)
                            self.logger.debug("Articles loaded on new page")
                        except Exception as e:
                            self.logger.warning(f"Articles selector not found after page change: {e}")
                            # Save HTML for debugging
                            debug_html = await self.page.content()
                            debug_path = WORK_DIR / f'debug_page_{next_page_num}_failed.html'
                            with open(debug_path, 'w', encoding='utf-8') as f:
                                f.write(debug_html)
                            self.logger.info(f"Saved failed page HTML: {debug_path}")

                        current_page += 1
                    else:
                        self.logger.info(f"No link found for page {next_page_num} - end of pagination")
                        break

                except Exception as e:
                    self.logger.warning(f"Pagination error: {e}")
                    if self.options.screenshot_on_error:
                        await capture_screenshot(
                            self.page,
                            f"pagination_error_page_{current_page}",
                            self.logger
                        )
                    break

            self.results['status'] = 'success'
            self.results['total_pages'] = current_page

            success_count = sum(
                1 for a in self.results['articles']
                if a.get('status') == 'success'
            )
            self.logger.info(
                f"Completed: {success_count}/{len(self.results['articles'])} articles"
            )

        except Exception as e:
            self.logger.error(f"News crawl failed: {e}", exc_info=True)
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            await capture_screenshot(self.page, "error_news_crawl", self.logger)

        return self.results

    async def crawl_news_article(
        self,
        article_url: str,
        base_url: str
    ) -> Dict[str, Any]:
        """
        Extract single news article.

        Args:
            article_url: Relative or absolute article URL
            base_url: Base URL for joining

        Returns:
            Dictionary with article data
        """
        result = {'url': article_url, 'status': 'pending'}

        try:
            full_url = urljoin(base_url, article_url)
            self.logger.debug(f"Opening article: {full_url}")

            # Navigate with retry
            await retry_with_backoff(
                self.page.goto,
                full_url,
                wait_until='domcontentloaded',
                timeout=self.options.timeout * 1000,
                config=self.retry_config,
                logger=self.logger
            )
            await self.page.wait_for_timeout(3000)

            # Extract title
            title_elem = self.page.locator('h1.titleHotNews span')
            if await title_elem.count() > 0:
                result['title'] = await title_elem.first.inner_text()
            else:
                self.logger.warning("Title selector not found, using fallback")
                result['title'] = 'No title'

            # Extract content
            content_elem = self.page.locator('div.contentDetail')
            if await content_elem.count() > 0:
                result['content'] = await content_elem.first.inner_text()
                result['content_html'] = await content_elem.first.inner_html()
            else:
                self.logger.warning("Content selector not found")
                result['content'] = ''
                result['content_html'] = ''

            # Extract author
            author_elem = self.page.locator('p.author.text-right')
            if await author_elem.count() > 0:
                result['author'] = await author_elem.first.inner_text()
            else:
                result['author'] = ''

            result['status'] = 'success'
            result['crawled_at'] = datetime.now().isoformat()

            # Save to .txt file
            filename = sanitize_filename(result['title'])
            txt_path = NEWS_DIR / f'{filename}.txt'

            counter = 1
            while txt_path.exists():
                txt_path = NEWS_DIR / f'{filename}_{counter}.txt'
                counter += 1

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"TIÊU ĐỀ: {result['title']}\n")
                f.write(f"URL: {full_url}\n")
                f.write(f"TÁC GIẢ: {result['author']}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(result['content'])

            result['saved_file'] = str(txt_path)
            self.logger.info(f"[OK] Saved: {filename[:40]}.txt")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"Article extraction failed: {e}")

            if self.options.screenshot_on_error:
                await capture_screenshot(
                    self.page,
                    f"error_article_{sanitize_filename(article_url[:30])}",
                    self.logger
                )

        return result

    async def crawl_multi_level(self) -> Dict[str, Any]:
        """
        Multi-level file download mode.

        Adapted from 4_antibot_crawler.ipynb cell 6.

        Returns:
            Results dictionary with downloaded files
        """
        url = self.config.url
        levels = self.config.levels or []
        exts = self.config.file_extensions or ['.pdf']
        max_files = self.options.max_files or 0

        self.results['url'] = url

        try:
            current_urls = [url]
            cookies = []

            for level_idx, level_cfg in enumerate(levels):
                level_name = level_cfg.get('name', f'Level {level_idx+1}')
                is_download = level_cfg.get('is_download', False)
                selector = level_cfg.get('selector')
                max_pages = level_cfg.get('max_pages', 30)

                self.logger.info(f'\n  Level {level_idx+1}: {level_name} ({len(current_urls)} urls)')

                all_links, crawled = [], []

                for i, u in enumerate(current_urls[:max_pages], 1):
                    self.logger.info(f'  [{i}/{min(len(current_urls), max_pages)}] {u[:50]}...')

                    try:
                        await asyncio.sleep(random.uniform(2, 4))
                        await self.page.goto(u, wait_until='domcontentloaded', timeout=60000)
                        await self.page.wait_for_timeout(3000)
                        await self.page.mouse.wheel(0, random.randint(100, 300))

                        html = await self.page.content()
                        cookies = await self.context.cookies()

                        links = extract_links(html, u, selector, exts, require_ext=is_download and not selector)

                        if not is_download:
                            links = [l for l in links if is_same_domain(l, url) and l != u]

                        self.logger.info(f'      -> {len(links)} links')
                        crawled.append({'url': u, 'links_found': len(links), 'status': 'success'})
                        all_links.extend(links)

                    except Exception as e:
                        self.logger.error(f'      Error: {str(e)[:40]}')
                        crawled.append({'url': u, 'status': 'failed', 'error': str(e)})

                # Remove duplicates
                seen = set()
                unique = [l for l in all_links if l not in seen and not seen.add(l)]

                self.results['levels'].append({
                    'name': level_name,
                    'pages_crawled': len(crawled),
                    'links_found': len(unique)
                })

                self.logger.info(f'  Total: {len(unique)} links')

                if is_download:
                    if max_files > 0:
                        unique = unique[:max_files]
                        self.logger.info(f'  Limited to {max_files} files')

                    self.logger.info(f'\n  Downloading {len(unique)} files...')
                    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

                    for i, dl_url in enumerate(unique):
                        await asyncio.sleep(random.uniform(1, 3))
                        dl = await self.download_with_cookies(
                            dl_url,
                            DOWNLOAD_DIR,
                            get_filename(dl_url),
                            cookies
                        )
                        self.results['files'].append(dl)
                        status = 'OK' if dl['status']=='success' else 'FAIL'
                        self.logger.info(f'    [{i+1}] [{status}] {dl["filename"][:40]}')

                    break
                else:
                    current_urls = unique
                    if not current_urls:
                        self.logger.info('  No more URLs')
                        break

            self.results['status'] = 'success'

        except Exception as e:
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            self.logger.error(f"Multi-level crawl failed: {e}", exc_info=True)

        return self.results

    async def crawl_two_level(self) -> Dict[str, Any]:
        """Two-level crawl (legacy support)."""
        self.config.levels = [
            {
                'name': 'Detail pages',
                'selector': self.config.level1_selector,
                'max_pages': self.config.max_detail_pages or 30
            },
            {
                'name': 'Download links',
                'selector': self.config.level2_selector,
                'is_download': True
            }
        ]
        return await self.crawl_multi_level()

    async def crawl_one_level(self) -> Dict[str, Any]:
        """One-level crawl (legacy support)."""
        self.config.levels = [
            {
                'name': 'Download',
                'selector': self.config.region_selector or self.config.level2_selector,
                'is_download': True
            }
        ]
        return await self.crawl_multi_level()

    async def download_with_cookies(
        self,
        url: str,
        folder: Path,
        fname: str,
        cookies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Download file with cookie persistence.

        Adapted from 4_antibot_crawler.ipynb cell 5.

        Args:
            url: File URL
            folder: Download folder
            fname: Filename
            cookies: Cookies from browser context

        Returns:
            Download result dictionary
        """
        r = {'url': url, 'filename': fname, 'status': 'pending'}

        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Cookie': '; '.join([f"{c['name']}={c['value']}" for c in cookies])
            }

            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=headers, timeout=aiohttp.ClientTimeout(120)) as resp:
                    if resp.status == 200:
                        # Extract filename from Content-Disposition
                        if 'Content-Disposition' in resp.headers:
                            for p in [r"filename\*=UTF-8''(.+)", r'filename="(.+)"', r"filename='(.+)'", r'filename=([^;\s]+)']:
                                m = re.search(p, resp.headers['Content-Disposition'])
                                if m:
                                    r['filename'] = unquote(m.group(1).strip())
                                    break

                        path = folder / r['filename']

                        # Handle duplicates
                        c = 1
                        b, ext = os.path.splitext(str(path))
                        while path.exists():
                            path = Path(f'{b}_{c}{ext}')
                            c += 1

                        content = await resp.read()

                        with open(path, 'wb') as f:
                            f.write(content)

                        r['status'] = 'success'
                        r['size'] = len(content)
                        r['path'] = str(path)

                    else:
                        r['status'] = 'failed'
                        r['error'] = f'HTTP {resp.status}'

        except Exception as e:
            r['status'] = 'failed'
            r['error'] = str(e)

        return r


# ============================================================================
# Configuration and Main Entry Point
# ============================================================================

def load_config(filepath: Path) -> tuple[List[CrawlerConfig], CrawlerOptions]:
    """
    Load crawler configuration from JSON file.

    Args:
        filepath: Path to JSON config file

    Returns:
        Tuple of (configs_list, options)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    urls = data.get('urls', [])
    options_dict = data.get('options', {})

    # Filter out extra fields from web_classifier output
    valid_config_fields = {
        'url', 'crawl_mode', 'levels', 'file_extensions', 'web_type', 'max_pages',
        'level1_selector', 'level2_selector', 'region_selector', 'max_detail_pages'
    }

    configs = []
    for url_cfg in urls:
        filtered_cfg = {k: v for k, v in url_cfg.items() if k in valid_config_fields}
        configs.append(CrawlerConfig(**filtered_cfg))

    options = CrawlerOptions(**options_dict)

    return configs, options


def save_results(results: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save results to JSON file.

    Args:
        results: List of result dictionaries
        filepath: Output JSON file path
    """
    output = {
        'results': results,
        'summary': {
            'urls': len(results),
            'total_articles': sum(len(r.get('articles', [])) for r in results),
            'total_files': sum(len(r.get('files', [])) for r in results),
            'successful_articles': sum(
                sum(1 for a in r.get('articles', []) if a.get('status') == 'success')
                for r in results
            ),
            'downloaded_files': sum(
                sum(1 for f in r.get('files', []) if f.get('status') == 'success')
                for r in results
            )
        },
        'crawled_at': datetime.now().isoformat()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


async def main() -> List[Dict[str, Any]]:
    """
    Main entry point.

    1. Load configuration
    2. Setup logger
    3. Initialize results
    4. For each URL: crawl
    5. Save output
    6. Print summary

    Returns:
        List of result dictionaries
    """
    # Create directories
    for directory in [DOWNLOAD_DIR, NEWS_DIR, LOG_DIR, SCREENSHOT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # Load config
    configs, options = load_config(INPUT_FILE)

    # Setup logger
    logger = setup_logger(
        level=getattr(logging, options.log_level.upper())
    )

    logger.info("="*50)
    logger.info("ANTIBOT CRAWLER STARTED")
    logger.info("="*50)
    logger.info(f"URLs to crawl: {len(configs)}")

    # Crawl each URL
    results = []
    for i, config in enumerate(configs, 1):
        logger.info(f"\n[{i}/{len(configs)}] {config.url}")

        try:
            async with AntibotCrawler(config, options, logger) as crawler:
                result = await crawler.crawl()
                results.append(result)

        except Exception as e:
            logger.error(f"Crawler failed for {config.url}: {e}", exc_info=True)
            results.append({
                'url': config.url,
                'status': 'failed',
                'error': str(e)
            })

        # Delay between URLs
        if i < len(configs):
            delay = random.uniform(5, 10)
            logger.info(f"Waiting {delay:.1f}s before next URL...")
            await asyncio.sleep(delay)

    # Save results
    save_results(results, OUTPUT_FILE)
    logger.info(f"\nResults saved: {OUTPUT_FILE}")

    # Print summary
    logger.info("\n" + "="*50)
    logger.info("SUMMARY")
    logger.info("="*50)

    for r in results:
        logger.info(f"\n{r['url']}")
        logger.info(f"  Status: {r['status']}")

        if 'articles' in r and r['articles']:
            success = sum(1 for a in r['articles'] if a.get('status') == 'success')
            logger.info(f"  Articles: {success}/{len(r['articles'])}")

        if 'files' in r and r['files']:
            downloaded = sum(1 for f in r['files'] if f.get('status') == 'success')
            logger.info(f"  Files: {downloaded}/{len(r['files'])}")

    logger.info("\n" + "="*50)
    logger.info("DONE!")
    logger.info("="*50)

    return results


if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
