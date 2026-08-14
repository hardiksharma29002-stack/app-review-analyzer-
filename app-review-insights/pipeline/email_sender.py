"""
Email Sender Module (Phase 6).

Sends the Weekly Product Pulse report via SMTP with a PDF attachment.
"""

import sys
from pathlib import Path
import markdown
import os
import requests
import base64

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
    Sends the latest report to the given recipient via Resend API.
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

    # Read and encode PDF
    with open(latest_pdf, "rb") as f:
        pdf_bytes = f.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Build the Resend API payload
    headers = {
        "Authorization": f"Bearer {config.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": "onboarding@resend.dev", # Resend's free tier sandbox domain
        "to": [recipient],
        "subject": config.EMAIL_SUBJECT,
        "html": html_body,
        "attachments": [
            {
                "filename": latest_pdf.name,
                "content": pdf_b64
            }
        ]
    }

    try:
        response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        if response.status_code not in (200, 201):
            raise ValueError(f"Resend API Error: {response.text}")
        return True
    except Exception as e:
        raise ValueError(f"Failed to send email via Resend: {str(e)}")
