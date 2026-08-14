"""
Pipeline package for App Review Insights Analyzer.

Modules:
    clean         — Data cleaning, deduplication, PII scrubbing
    classify      — LLM-based theme classification (Groq API)
    group_quotes  — Theme grouping and representative quote selection
    insights      — LLM-based recommendation generation (Groq API)
    report        — Weekly Pulse report builder (Markdown + PDF)
    email_sender  — SMTP email delivery (Gmail App Password)
"""
