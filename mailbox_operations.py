import sqlite3
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import csv

def analyze_database(db_path):
    db_count, db_email = analyze_db(db_path)
    print(f"\nDatabase Analysis:")
    print(f"Total emails in DB: {db_count}")
    print("Top email from DB (id, subject, size, uidl):")
    print(db_email)

def analyze_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM mbx")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT id, subjectStrip, size, uidl FROM mbx ORDER BY id LIMIT 1")
    email_data = cursor.fetchone()

    conn.close()
    return total_count, email_data

def analyze_mbx(mbx_path):
    with open(mbx_path, 'rb') as file:
        while True:
            line = file.readline()
            if not line:
                break

            line_str = line.decode('utf-8', errors='ignore').strip()

            if line_str == '[hdr]':
                mlen_line = file.readline()
                if not mlen_line:
                    break

                mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
                if mlen_str.startswith('mlen='):
                    mlen_value = mlen_str[len('mlen='):]
                    try:
                        mlen = int(mlen_value, 16)
                    except ValueError:
                        print(f"Invalid mlen value: {mlen_value}")
                        continue

                    msg_line = file.readline()
                    if not msg_line:
                        break

                    msg_line_str = msg_line.decode('utf-8', errors='ignore').strip()
                    if msg_line_str == '[msg]':
                        msg_content = file.read(mlen)
                        if len(msg_content) < mlen:
                            print("Incomplete message content.")
                            break

                        parser = BytesParser(policy=policy.default)
                        try:
                            email_message = parser.parsebytes(msg_content)
                        except Exception as e:
                            print(f"Error parsing email: {e}")
                            return None, None

                        subject = email_message['subject']
                        html_body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    charset = part.get_content_charset()
                                    html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                                    break
                        else:
                            if email_message.get_content_type() == 'text/html':
                                charset = email_message.get_content_charset()
                                html_body = email_message.get_payload(decode=True).decode(charset, errors='replace')

                        return subject, html_body
                    else:
                        print(f"Expected '[msg]', but found: {msg_line_str}")
                        break
                else:
                    print(f"Expected 'mlen=', but found: {mlen_str}")
                    break
            else:
                continue

    return None, None

def extract_article_links_old(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []

    article_containers = soup.find_all('div', class_='cb cc cd ce cf cg ch ci cj')

    for container in article_containers:
        title_tag = container.find('b', id=True)
        if title_tag:
            title = title_tag.get_text(strip=True)
            link_tag = title_tag.find_parent('a', href=True)
            if link_tag:
                href = link_tag['href']
                articles.append((title, href))

    return articles


def extract_article_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []

    article_containers = soup.find_all('div', class_='cb cc cd ce cf cg ch ci cj')

    for container in article_containers:
        title_tag = container.find('b', id=True)
        if title_tag:
            title = title_tag.get_text(strip=True)
            link_tag = title_tag.find_parent('a', href=True)
            if link_tag:
                href = link_tag['href']

                # Target the second content element
                content_elements = container.contents
                if len(content_elements) > 1:
                    second_content = content_elements[1]
                    articles.append((title, href, title, 0))

                else:
                    print(f"Warning: Second content element not found for article '{title}'")


    return articles


def save_articles_to_csv(articles, csv_path):
    """
    Save article data to a CSV file.

    :param articles: List of tuples containing article data (title, like_count, link)
    :param csv_path: Path to the CSV file
    """
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Link', 'Like Count'])
        for article in articles:
            writer.writerow(article)


def extract_all_article_links_from_mbx(mbx_path, csv_path):
    all_article_links = []

    with open(mbx_path, 'rb') as file:
        while True:
            line = file.readline()
            if not line:
                break

            line_str = line.decode('utf-8', errors='ignore').strip()

            if line_str == '[hdr]':
                mlen_line = file.readline()
                if not mlen_line:
                    break

                mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
                if mlen_str.startswith('mlen='):
                    mlen_value = mlen_str[len('mlen='):]
                    try:
                        mlen = int(mlen_value, 16)
                    except ValueError:
                        print(f"Invalid mlen value: {mlen_value}")
                        continue

                    msg_line = file.readline()
                    if not msg_line:
                        break

                    msg_line_str = msg_line.decode('utf-8', errors='ignore').strip()
                    if msg_line_str == '[msg]':
                        msg_content = file.read(mlen)
                        if len(msg_content) < mlen:
                            print("Incomplete message content.")
                            break

                        parser = BytesParser(policy=policy.default)
                        try:
                            email_message = parser.parsebytes(msg_content)
                        except Exception as e:
                            print(f"Error parsing email: {e}")
                            continue

                        subject = email_message['subject']
                        html_body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    charset = part.get_content_charset()
                                    html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                                    break
                        else:
                            if email_message.get_content_type() == 'text/html':
                                charset = email_message.get_content_charset()
                                html_body = email_message.get_payload(decode=True).decode(charset, errors='replace')

                        article_links = extract_article_links(html_body)
                        all_article_links.extend(article_links)
                    else:
                        print(f"Expected '[msg]', but found: {msg_line_str}")
                        break
                else:
                    print(f"Expected 'mlen=', but found: {mlen_str}")
                    break
            else:
                continue

    save_articles_to_csv(all_article_links, csv_path)
    return all_article_links