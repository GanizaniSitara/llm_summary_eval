"""
Web Fetching Pipeline for LLM Summary Evaluation Tool.

This module handles fetching content from web URLs, including Medium articles via Freedium.
"""

import urllib.parse
from typing import List, Optional
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup


class WebFetcher:
    """Handles fetching content from web URLs."""
    
    def __init__(self, settings):
        self.settings = settings
        
    def get_urls(self) -> List[str]:
        """
        Get URLs from file or user input.
        Returns list of URLs to process.
        """
        print("\\n--- URL Source ---")
        print("1. Load from file")
        print("2. Enter URLs manually")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            return self._load_urls_from_file()
        elif choice == "2":
            return self._get_urls_from_input()
        else:
            print("Invalid choice.")
            return []
            
    def _load_urls_from_file(self) -> List[str]:
        """Load URLs from the configured file."""
        if not Path(self.settings.urls_file).exists():
            print(f"URL file not found: {self.settings.urls_file}")
            return []
            
        try:
            with open(self.settings.urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                
            print(f"Loaded {len(urls)} URLs from {self.settings.urls_file}")
            return urls
            
        except Exception as e:
            print(f"Error reading URL file: {e}")
            return []
            
    def _get_urls_from_input(self) -> List[str]:
        """Get URLs from user input."""
        urls = []
        print("Enter URLs (one per line, empty line to finish):")
        
        while True:
            url = input().strip()
            if not url:
                break
            urls.append(url)
            
        return urls
        
    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL using Playwright.
        Handles Medium URLs by redirecting to Freedium.
        """
        # Transform Medium URLs to Freedium
        processed_url = self._process_medium_url(url)
        
        print(f"Fetching content from: {processed_url}")
        
        try:
            content = self._fetch_with_playwright(processed_url)
            if content:
                print(f"Successfully fetched content ({len(content)} characters)")
                return content
            else:
                print("No content retrieved")
                return None
                
        except Exception as e:
            print(f"Error fetching content: {e}")
            return None
            
    def _process_medium_url(self, url: str) -> str:
        """
        Transform Medium URLs to use Freedium for better access.
        """
        if 'medium.com' in url:
            # Parse the original URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Extract the path and query
            path_and_query = parsed_url.path
            if parsed_url.query:
                path_and_query += f"?{parsed_url.query}"
                
            # Construct the Freedium URL
            freedium_url = f"https://freedium.cfd/https://medium.com{path_and_query}"
            print(f"Transformed Medium URL to Freedium: {freedium_url}")
            return freedium_url
            
        return url
        
    def _fetch_with_playwright(self, url: str, timeout: int = 10000) -> Optional[str]:
        """
        Fetch content using Playwright with popup handling.
        """
        with sync_playwright() as p:
            # Launch browser in non-headless mode for better content access
            browser = p.chromium.launch_persistent_context('playwright', headless=False)
            page = browser.new_page()
            
            try:
                # Navigate to the URL
                page.goto(url, timeout=timeout)
                page.wait_for_load_state('networkidle', timeout=timeout)
                
            except TimeoutError:
                print(f"Timeout: Failed to load page within {timeout}ms")
                browser.close()
                return None
                
            # Handle common popup/modal patterns
            self._handle_popups(page)
            
            # Wait a bit for any dynamic content
            page.wait_for_timeout(1000)
            
            # Force reload to ensure content is fresh
            page.reload()
            page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Extract content
            content = self._extract_content(page)
            browser.close()
            
            return content
            
    def _handle_popups(self, page):
        """Handle common popup and modal patterns."""
        popup_selectors = [
            'button:text("Close")',
            'button:text("Accept")',
            'button:text("Continue")',
            'button:text("Got it")',
            '[aria-label="Close"]',
            '[aria-label="Dismiss"]',
            '.modal-close',
            '.popup-close',
            'button.close',
            '.cookie-banner button',
            '.consent-banner button',
        ]
        
        for selector in popup_selectors:
            try:
                popup = page.locator(selector).first
                if popup.is_visible():
                    popup.click()
                    page.wait_for_timeout(500)  # Brief pause after clicking
                    break
            except Exception:
                # Continue trying other selectors
                continue
                
    def _extract_content(self, page) -> Optional[str]:
        """Extract readable content from the page."""
        try:
            # Try to get main content area first
            main_content = None
            
            # Common content selectors
            content_selectors = [
                '.main-content',
                'main',
                'article',
                '.post-content',
                '.article-content',
                '[role="main"]',
                '.content',
            ]
            
            for selector in content_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        main_content = element.inner_html()
                        break
                except Exception:
                    continue
                    
            # Fallback to body if no main content found
            if not main_content:
                main_content = page.inner_html('body')
                
            if not main_content:
                return None
                
            # Parse with BeautifulSoup to extract clean text
            soup = BeautifulSoup(main_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
                
            # Extract text from relevant elements
            text_elements = soup.select('p, h1, h2, h3, h4, h5, h6, blockquote, li')
            text_content = ' '.join([elem.get_text(strip=True) for elem in text_elements])
            
            return text_content if text_content else None
            
        except Exception as e:
            print(f"Error extracting content: {e}")
            return None
            
    def batch_fetch(self, urls: List[str]) -> List[Tuple[str, str]]:
        """
        Fetch content from multiple URLs.
        Returns list of (url, content) tuples.
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\\nProcessing URL {i}/{len(urls)}: {url}")
            content = self.fetch_content(url)
            if content:
                results.append((url, content))
            else:
                print(f"Failed to fetch content from {url}")
                
        return results