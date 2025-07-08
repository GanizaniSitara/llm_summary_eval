"""
OE Classic Email Client Archive Operations

This module provides utilities for working with email archives from the OE Classic 
email client, particularly focusing on extracting article content and metadata.
"""

from typing import List, Tuple, Optional
import sqlite3
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import csv

class EmailStore:
    """Represents an OE Classic email archive (.mbx file)"""
    
    def __init__(self, mbx_path: str):
        self.mbx_path = mbx_path
        
    def get_message(self, message_id: int) -> Optional[Tuple[str, str]]:
        """
        Retrieve a specific email message by ID
        Returns tuple of (subject, html_body) or None if not found
        """
        with open(self.mbx_path, 'rb') as file:
            while True:
                line = file.readline()
                if not line:
                    break
                    
                # Parse header and content sections
                if line.strip() == '[hdr]':
                    mlen_line = file.readline()
                    if not mlen_line:
                        break
                        
                    mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
                    if mlen_str.startswith('mlen='):
                        try:
                            mlen = int(mlen_str[len('mlen='):], 16)
                        except ValueError:
                            continue                            
                        
                        msg_line = file.readline()
                        if not msg_line:
                            break
                            
                        if msg_line.strip() == '[msg]':
                            msg_content = file.read(mlen)
                            parser = BytesParser(policy=policy.default)
                            email_message = parser.parsebytes(msg_content)
                            
                            subject = email_message['subject']
                            html_body = self._extract_html_body(email_message)
                            return (subject, html_body)
    
    def _extract_html_body(self, message) -> str:
        """Extract HTML body from email message"""
        html_body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/html':
                    charset = part.get_content_charset()
                    html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
        elif message.get_content_type() == 'text/html':
            charset = message.get_content_charset()
            html_body = message.get_payload(decode=True).decode(charset, errors='replace')
            
        return html_body

class MessageParser:
    """Parses email content to extract article metadata"""
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def find_articles(self) -> List[Tuple[str, str]]:
        """
        Find all articles in the email content
        Returns list of (title, url) tuples
        """
        articles = []
        containers = self.soup.find_all('div', class_='cb cc cd ce cf cg ch ci cj')
        
        for container in containers:
            title_tag = container.find('b', id=True)
            if title_tag:
                title = title_tag.get_text(strip=True)
                link_tag = title_tag.find_parent('a', href=True)
                if link_tag and link_tag.has_attr('href'):
                    url = link_tag['href']
                    articles.append((title, url))
                    
        return articles

def save_articles_to_csv(articles: List[Tuple[str, str]], csv_path: str) -> None:
    """Save article metadata to CSV file"""
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'URL'])
        for title, url in articles:
            writer.writerow([title, url])

def extract_all_article_links_from_mbx(mbx_path: str, csv_path: str) -> List[Tuple[str, str]]:
    """
    Extract all article links from an OE Classic email archive
    Returns list of (title, url) tuples and saves to CSV
    """
    store = EmailStore(mbx_path)
    
    articles = []
    for message_id in range(1, 1000):  # Example iteration
        subject, html_body = store.get_message(message_id)
        if not html_body:
            continue
            
        parser = MessageParser(html_body)
        articles.extend(parser.find_articles())
        
    save_articles_to_csv(articles, csv_path)
    return articles

# Legacy compatibility functions
def analyze_db(db_path: str) -> Tuple[int, Optional[Tuple]]:
    """Legacy database analysis function"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM mbx")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, subjectStrip, size, uidl FROM mbx ORDER BY id LIMIT 1")
        email_data = cursor.fetchone()
        return (total_count, email_data)
    finally:
        conn.close()

"""
Would you like me to:

1. Create additional utility modules for different aspects of OE Classic processing?
2. Add more sophisticated error handling and logging?
3. Include type hints and docstrings throughout?

The current structure separates concerns into:
- EmailStore class for archive access
- MessageParser class for content extraction 
- Utility functions for CSV operations
- Legacy database analysis

Let me know if you want to add any of these improvements or see the full implementation details for any specific aspect.
"""
