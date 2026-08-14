"""
Report Generation Module (Phase 4).

Generates the "Weekly Product Pulse" report in Markdown and PDF formats.
Enforces the strictly < 250 words constraint.
Handles Unicode issues for PDF generation.
"""

import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config

def build_markdown_report(theme_counts: dict, quotes: list, recommendations: list) -> str:
    """Builds the report in Markdown format with rich PDF sections."""
    total_reviews = sum(theme_counts.values())
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    top_theme = list(theme_counts.keys())[0] if theme_counts else "Unknown"
    
    md = f"# Weekly Product Pulse ({date_str})\n\n"
    
    md += "## Executive Summary\n"
    md += f"This report provides an AI-driven analysis of recent user feedback. We processed {total_reviews} reviews to identify core user sentiment. The primary driver of user discussion this period is related to **{top_theme}**.\n\n"
    
    md += "## Overall Statistics\n"
    md += f"- **Total Reviews Analyzed**: {total_reviews}\n"
    md += f"- **Key Business Themes Identified**: {len(theme_counts)}\n\n"
    
    md += "## Category Breakdown\n"
    # Slice to only display the Top N themes as requested by config
    top_themes = list(theme_counts.items())[:config.REPORT_TOP_THEMES]
    for theme, count in top_themes:
        pct = (count / total_reviews) * 100 if total_reviews else 0
        md += f"- **{theme}**: {count} reviews ({pct:.1f}%)\n"
        
    md += "\n## Voice of the Customer\n"
    for q in quotes:
        md += f"- > \"{q['quote']}\"\n  — *{q['rating']} Stars ({q['theme']})*\n"
        
    md += "\n## Strategic Priorities\n"
    for i, rec in enumerate(recommendations, 1):
        md += f"{i}. {rec}\n"
        
    md += "\n## Key Insights\n"
    if recommendations:
        md += f"The data suggests an immediate focus on {recommendations[0].lower().strip('.')} to improve overall user satisfaction.\n"
    else:
        md += "No critical insights were generated for this period.\n"
        
    return md

def enforce_word_count(md_text: str) -> str:
    """Ensures the report is strictly under 250 words (Edge case #73)."""
    words = md_text.split()
    if len(words) <= config.REPORT_MAX_WORDS:
        return md_text
        
    print(f"[WARNING] Report exceeds {config.REPORT_MAX_WORDS} words. Trimming.")
    # We trim the text and append a notice.
    trimmed = " ".join(words[:config.REPORT_MAX_WORDS - 10])
    trimmed += "\n\n*(Report truncated to meet 250-word limit)*"
    return trimmed

def build_pdf_report(md_text: str, output_path: Path):
    """Converts the report content into a PDF."""
    print(f"Generating PDF report at {output_path}...")
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = styles['Heading1']
    title_style.textColor = HexColor("#00D09C") # Groww primary color
    
    h2_style = styles['Heading2']
    h2_style.textColor = HexColor("#444444")
    
    body_style = styles['Normal']
    body_style.fontSize = 11
    body_style.leading = 14
    
    quote_style = ParagraphStyle(
        'Quote',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=20,
        textColor=HexColor("#555555"),
        fontName="Helvetica-Oblique"
    )

    story = []
    
    # Very basic parsing of our specific markdown format
    lines = md_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Edge case #76: Handle Unicode characters that ReportLab standard fonts can't render
        # We replace emojis or complex unicode with ascii safely.
        line = line.encode('ascii', 'ignore').decode('ascii')
        
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
            story.append(Spacer(1, 6))
        elif line.startswith('- >'):
            story.append(Paragraph(line[3:].strip(), quote_style))
        elif line.startswith('- '):
            # Bold rendering for themes
            content = line[2:].replace('**', '<b>', 1).replace('**', '</b>', 1)
            story.append(Paragraph(content, body_style))
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
            story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph(line, body_style))
            
    doc.build(story)
    print("[OK] PDF generated successfully.")

def generate_reports(theme_counts: dict, quotes: list, recommendations: list):
    """Generates both Markdown and PDF reports."""
    md_text = build_markdown_report(theme_counts, quotes, recommendations)
    md_text = enforce_word_count(md_text)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_path = config.OUTPUT_DIR / f"weekly_pulse_{date_str}.md"
    pdf_path = config.OUTPUT_DIR / f"weekly_pulse_{date_str}.pdf"
    
    # Save MD
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_text)
        
    # Save PDF
    build_pdf_report(md_text, pdf_path)
    
    return md_path, pdf_path

if __name__ == "__main__":
    # Test
    counts = {"App Performance & UX": 45, "Payments": 20, "Customer Support": 10}
    qs = [
        {"theme": "App Performance & UX", "rating": 1, "quote": "App crashes constantly."},
        {"theme": "Payments", "rating": 2, "quote": "Money deducted but not invested."},
        {"theme": "Customer Support", "rating": 1, "quote": "No reply from support team."}
    ]
    recs = ["Fix crashes.", "Improve payment gateway.", "Hire more support staff."]
    generate_reports(counts, qs, recs)
