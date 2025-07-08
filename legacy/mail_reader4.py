from email.parser import BytesParser
from email import policy
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def normalize_date(dt):
    if dt is None:
        return datetime.min
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def extract_body(email_msg):
    body = ""
    if email_msg.is_multipart():
        for part in email_msg.walk():
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset() or 'utf-8'
                try:
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                except Exception:
                    body = "[Error decoding text/plain]"
                if body:
                    break
        if not body:
            for part in email_msg.walk():
                if part.get_content_type() == 'text/html':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception:
                        body = "[Error decoding text/html]"
                    if body:
                        break
    else:
        content_type = email_msg.get_content_type()
        charset = email_msg.get_content_charset() or 'utf-8'
        try:
            body = email_msg.get_payload(decode=True).decode(charset, errors='replace')
        except Exception:
            body = f"[Error decoding {content_type}]"
    return body

def process_linkedin_email(body):
    # Split the email body by the separator that divides job blocks.
    blocks = body.split("---------------------------------------------------------")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Only process blocks that have a "View job:" line.
        if "View job:" not in block:
            continue
        # Break the block into non-empty lines.
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        # Assume the first three lines are: Title, Company, Location.
        title = lines[0]
        company = lines[1]
        location = lines[2]
        # Check if the job location is London or Milton Keynes.
        if location.lower() in ["london", "milton keynes"]:
            # Look for the "View job:" line to extract the link.
            job_link = None
            for line in lines:
                if line.startswith("View job:"):
                    job_link = line[len("View job:"):].strip()
                    break
            print("Job Posting:")
            print("  Title:  ", title)
            print("  Company:", company)
            print("  Location:", location)
            print("  Link:   ", job_link if job_link else "Not found")
            print()
        else:
            # For jobs not in London or Milton Keynes, just output SKIPPING.
            print("SKIPPING: Title:", title, "| Location:", location)
            print()

def iterate_emails(mbx_path, limit=10):
    emails = []
    with open(mbx_path, 'rb') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if line.decode('utf-8', errors='ignore').strip() != '[hdr]':
                continue

            mlen_line = f.readline()
            if not mlen_line:
                break
            mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
            if not mlen_str.startswith('mlen='):
                continue
            try:
                mlen = int(mlen_str[len('mlen='):], 16)
            except ValueError:
                continue

            msg_line = f.readline()
            if not msg_line:
                break
            if msg_line.decode('utf-8', errors='ignore').strip() != '[msg]':
                continue

            msg_content = f.read(mlen)
            if len(msg_content) < mlen:
                print("Incomplete message content.")
                break

            try:
                email_msg = BytesParser(policy=policy.default).parsebytes(msg_content)
            except Exception:
                continue

            subject = email_msg.get('subject', '(No Subject)')
            date_str = email_msg.get('date', None)
            dt = None
            if date_str:
                try:
                    dt = parsedate_to_datetime(date_str)
                except Exception:
                    dt = None

            body = extract_body(email_msg)
            emails.append({
                'subject': subject,
                'date': dt,
                'raw_date': date_str,
                'body': body
            })

    # Sort emails from most recent to least recent.
    emails.sort(key=lambda x: normalize_date(x['date']), reverse=True)

    for i, email in enumerate(emails[:limit], 1):
        print("=" * 80)
        # Identify LinkedIn emails by checking for "linkedin.com" in the body.
        if "linkedin.com" in email['body'].lower():
            print(f"Email #{i} (LinkedIn):")
            print("Subject:", email['subject'])
            print("Date:   ", email['raw_date'] if email['raw_date'] else "(No Date)")
            print()
            process_linkedin_email(email['body'])
        else:
            print(f"NOT LINKED IN Email #{i}:")
            print("Subject:", email['subject'])
            print("Date:   ", email['raw_date'] if email['raw_date'] else "(No Date)")
            print()
    print("=" * 80)
    print(f"Total emails processed: {len(emails)}")

if __name__ == "__main__":
    mbx_path = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\JobSearch.mbx'
    iterate_emails(mbx_path, limit=10)
