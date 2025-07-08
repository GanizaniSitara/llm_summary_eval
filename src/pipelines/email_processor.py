"""
Email Processing Pipeline for LLM Summary Evaluation Tool.

This module handles extraction of articles from OE Classic email archives.
"""

import csv
from typing import List, Tuple, Optional
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path


class EmailStore:
    """Manages access to OE Classic email archive (.mbx file)."""
    
    def __init__(self, mbx_path: str):
        self.mbx_path = mbx_path
        
    def get_all_messages(self) -> List[Tuple[str, str]]:
        """
        Retrieve all email messages from the archive.
        Returns list of (subject, html_body) tuples.
        """
        messages = []
        
        if not Path(self.mbx_path).exists():
            print(f"Email archive not found: {self.mbx_path}")
            return messages
            
        try:
            with open(self.mbx_path, 'rb') as file:
                while True:
                    line = file.readline()
                    if not line:
                        break
                        
                    # Parse header and content sections
                    if line.strip() == b'[hdr]':
                        message_data = self._parse_message(file)
                        if message_data:
                            messages.append(message_data)
                            
        except Exception as e:
            print(f"Error reading email archive: {e}")
            
        return messages
        
    def _parse_message(self, file) -> Optional[Tuple[str, str]]:
        """Parse a single message from the file."""
        try:
            mlen_line = file.readline()
            if not mlen_line:
                return None
                
            mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
            if not mlen_str.startswith('mlen='):
                return None
                
            mlen = int(mlen_str[len('mlen='):], 16)
            
            msg_line = file.readline()
            if not msg_line or msg_line.strip() != b'[msg]':
                return None
                
            msg_content = file.read(mlen)
            parser = BytesParser(policy=policy.default)
            email_message = parser.parsebytes(msg_content)
            
            subject = email_message.get('subject', 'No Subject')
            html_body = self._extract_html_body(email_message)
            
            return (subject, html_body)
            
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def _extract_html_body(self, message) -> str:
        """Extract HTML body from email message."""
        html_body = ""
        
        try:
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == 'text/html':
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                        break
            elif message.get_content_type() == 'text/html':
                charset = message.get_content_charset() or 'utf-8'
                html_body = message.get_payload(decode=True).decode(charset, errors='replace')
                
        except Exception as e:
            print(f"Error extracting HTML body: {e}")
            
        return html_body


class ArticleParser:
    """Parses email content to extract article metadata."""
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def extract_articles(self) -> List[Tuple[str, str]]:
        """
        Extract articles from email content.
        Returns list of (title, url) tuples.
        """
        articles = []
        
        # Look for common article container patterns
        containers = self._find_article_containers()
        
        for container in containers:
            article_data = self._extract_article_from_container(container)
            if article_data:
                articles.append(article_data)
                
        return articles
        
    def _find_article_containers(self):
        """Find potential article containers in the HTML."""
        # Multiple patterns to catch different email formats
        patterns = [
            ('div', {'class': 'cb cc cd ce cf cg ch ci cj'}),
            ('div', {'class': lambda x: x and 'article' in x.lower()}),
            ('a', {'href': lambda x: x and 'medium.com' in x}),
        ]
        
        containers = []
        for tag, attrs in patterns:
            found = self.soup.find_all(tag, attrs)
            containers.extend(found)
            
        return containers
        
    def _extract_article_from_container(self, container) -> Optional[Tuple[str, str]]:
        """Extract title and URL from a container element."""
        try:
            title = None
            url = None
            
            # Look for title in various elements
            title_elements = container.find_all(['b', 'strong', 'h1', 'h2', 'h3'])
            for elem in title_elements:
                if elem.get_text(strip=True):
                    title = elem.get_text(strip=True)
                    break
                    
            # Look for URL
            link_elem = container.find('a', href=True)
            if not link_elem:
                link_elem = container.find_parent('a', href=True)
                
            if link_elem and link_elem.get('href'):
                url = link_elem['href']
                
            # If container itself is a link
            if container.name == 'a' and container.get('href'):
                url = container['href']
                if not title:
                    title = container.get_text(strip=True)
                    
            return (title, url) if title and url else None
            
        except Exception as e:
            print(f"Error extracting article: {e}")
            return None


class EmailProcessor:
    """Main email processing pipeline."""
    
    def __init__(self, settings):
        self.settings = settings
        self.email_store = EmailStore(settings.mbx_path)
        
    def extract_articles(self) -> List[Tuple[str, str]]:
        """
        Extract all articles from the email archive.
        Returns list of (title, url) tuples.
        """
        print("Extracting articles from email archive...")
        
        messages = self.email_store.get_all_messages()
        if not messages:
            print("No messages found in email archive.")
            return []
            
        print(f"Processing {len(messages)} messages...")
        
        all_articles = []
        for subject, html_body in messages:
            if html_body:
                parser = ArticleParser(html_body)
                articles = parser.extract_articles()
                all_articles.extend(articles)
                
        # Remove duplicates while preserving order
        unique_articles = []
        seen = set()
        for title, url in all_articles:
            if url not in seen:
                unique_articles.append((title, url))
                seen.add(url)
                
        print(f"Found {len(unique_articles)} unique articles.")
        
        # Save to CSV
        self._save_to_csv(unique_articles)
        
        return unique_articles
        
    def _save_to_csv(self, articles: List[Tuple[str, str]]):
        """Save articles to CSV file."""
        try:
            with open(self.settings.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Title', 'Link'])
                for title, url in articles:
                    writer.writerow([title, url])
                    
            print(f"Articles saved to {self.settings.csv_path}")
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            
    def get_articles_subset(self, start_row: int = None, num_records: int = None) -> List[Tuple[str, str]]:
        """
        Get a subset of articles based on settings.
        Used for processing only a portion of extracted articles.
        """
        articles = self.extract_articles()
        
        start_row = start_row or self.settings.mail_start_row
        num_records = num_records or self.settings.mail_num_records
        
        if start_row >= len(articles):
            return []
            
        end_row = start_row + num_records if num_records else len(articles)
        return articles[start_row:end_row]