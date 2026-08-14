"""
Email Sender Module (Phase 6).

Sends the Weekly Product Pulse report via SMTP with a PDF attachment.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import sys
from pathlib import Path
import markdown
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config

def get_latest_report_paths() -> tuple[Path, Path]:
    """Finds the most recently generated Markdown and PDF reports in output/."""
    md_files = list(config.OUTPUT_DIR.glob("weekly_pulse_*.md"))
    pdf_files = list(config.OUTPUT_DIR.glob("weekly_pulse_*.pdf"))
    
    if not md_files or not pdf_files:
        raise FileNotFoundError("No reports found to send.")
        
    # Sort by modification time to get the latest
    latest_md = max(md_files, key=os.path.getmtime)
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    return latest_md, latest_pdf

def send_report_email(recipient: str = None) -> bool:
    """
    Sends the latest report to the given recipient via email.
    If no recipient is given, defaults to config.RECIPIENT_EMAIL.
    """
    is_valid, msg = config.validate_email_config()
    if not is_valid:
        raise ValueError(msg)
        
    recipient = recipient or config.RECIPIENT_EMAIL
    if not recipient:
        raise ValueError("Recipient email not provided and not set in .env")

    latest_md, latest_pdf = get_latest_report_paths()
    
    with open(latest_md, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    # Convert MD to HTML for the email body
    html_body = markdown.markdown(md_text)

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = config.SMTP_EMAIL
    msg["To"] = recipient
    msg["Subject"] = config.EMAIL_SUBJECT

    msg.attach(MIMEText(html_body, "html"))

    with open(latest_pdf, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
        pdf_part.add_header(
            "Content-Disposition", 
            "attachment", 
            filename=latest_pdf.name
        )
        msg.attach(pdf_part)

    try:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.login(config.SMTP_EMAIL, config.SMTP_APP_PASSWORD)
            server.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        raise ValueError("Gmail authentication failed. Verify your App Password and 2-Step Verification.")
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")
