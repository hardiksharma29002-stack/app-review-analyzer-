# Edge Cases & Defensive Handling — App Review Insights Analyzer

> Cross-referenced with [architecture.md](file:///c:/Users/hardi/OneDrive/Desktop/app_analysis/architecture.md) and [implementation.md](file:///c:/Users/hardi/OneDrive/Desktop/app_analysis/implementation.md)

---

## 1. Review Scraper (`scripts/get_reviews.py`)

### 1.1 Network & API Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 1 | **No internet connection** | `google-play-scraper` throws `ConnectionError` | Catch exception, print clear message: "No internet. Connect and retry." Exit with code 1. |
| 2 | **Google Play blocks requests** | Scraper gets HTTP 429 or CAPTCHA | Implement retry with 5s backoff (max 3 retries). If still blocked, print "Google Play rate-limited. Wait 10 min and retry." |
| 3 | **App ID changed/delisted** | `com.nextbillion.groww` returns 404 or empty | Check response before processing. If empty: "App not found. Verify the app ID." |
| 4 | **Scraper library breaks** | `google-play-scraper` API changes between versions | Pin version in `requirements.txt`. Wrap call in try/except with a clear "Scraper library error" message. |
| 5 | **Timeout on large fetch** | `reviews_all()` hangs on slow networks | Set a timeout (120s). If exceeded: "Scraper timed out. Try with `--weeks 4` for fewer reviews." |

### 1.2 Data Quality Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 6 | **Zero reviews in date window** | `--weeks 1` during a quiet period → empty CSV | Check row count after filtering. If 0: "No reviews found in the last {weeks} weeks. Try a larger window." Don't write an empty CSV. |
| 7 | **Reviews with no text (rating-only)** | Some Google Play reviews have only a star rating, no text body | Filter out rows where `text` is `None`/empty. Log count: "Dropped {n} rating-only reviews." |
| 8 | **Reviews in non-English languages** | Hindi, Marathi, etc. reviews in text field | Keep them — the LLM handles multilingual. Don't filter by language. Note: PII regex may miss non-Latin phone formats. |
| 9 | **Duplicate reviews from pagination** | `reviews()` pagination returns overlapping pages | Dedupe on `(text, date)` after collection, before writing CSV. |
| 10 | **Extremely long reviews** | Single review with 2000+ words | Don't truncate at scraper stage — let `clean.py` handle. But log a warning if any review > 500 words. |
| 11 | **Special characters in text** | Emojis, HTML entities (`&amp;`), newlines in review text | Normalize: strip HTML entities (`html.unescape()`), preserve emojis (they're valid text), replace newlines with spaces. |
| 12 | **Date format inconsistencies** | `google-play-scraper` returns `datetime` objects, not strings | Always convert to `YYYY-MM-DD` string format via `strftime('%Y-%m-%d')`. |
| 13 | **Future-dated reviews** | Timezone issues could show reviews with tomorrow's date | Filter: `date <= today`. Log if any future dates are dropped. |

### 1.3 File System Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 14 | **`data/` directory doesn't exist** | `FileNotFoundError` when writing CSV | `os.makedirs('data', exist_ok=True)` before writing. |
| 15 | **CSV write permission denied** | File is locked by another process (Excel has it open) | Catch `PermissionError`: "Cannot write reviews.csv — close any programs using it." |
| 16 | **Existing CSV overwrite** | Running script again overwrites previous data | Add `--append` flag option, or timestamp the filename. Default: overwrite with warning logged. |

---

## 2. Data Cleaning (`pipeline/clean.py`)

### 2.1 Input DataFrame Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 17 | **Empty DataFrame** | CSV exists but has 0 data rows (only header) | Check `len(df) == 0` at start. Return empty DF with a flag: `{"status": "empty", "message": "No reviews to analyze."}` |
| 18 | **Missing required columns** | CSV has `rating` and `text` but no `date` column | Check for required columns (`rating`, `text`, `date`) at start. Raise `ValueError("Missing columns: {missing}")` with clear column names. |
| 19 | **Extra unexpected columns** | CSV has extra columns like `user_name`, `thumbs_up` | Ignore extra columns — only read `rating`, `title`, `text`, `date`. Don't fail. |
| 20 | **Wrong column data types** | `rating` stored as string `"five"` instead of `5` | Attempt `pd.to_numeric(df['rating'], errors='coerce')`. Drop rows where rating is NaN after coercion. Log count dropped. |
| 21 | **Rating out of range** | `rating` value is 0, 6, or negative | Filter to `1 <= rating <= 5`. Drop and log rows outside range. |
| 22 | **All reviews identical** | 500 rows but only 1 unique review (spam/bot) | After dedup, if < 5 unique reviews remain, warn: "Very few unique reviews ({n}). Results may not be meaningful." |
| 23 | **CSV encoding issues** | File saved as Latin-1 or Windows-1252 instead of UTF-8 | Try reading with `encoding='utf-8'`, fall back to `encoding='latin-1'`, then `encoding='cp1252'`. |
| 24 | **Very large CSV (10k+ rows)** | Memory or processing time issues | Cap at 2000 most recent reviews. Log: "Trimmed to 2000 most recent reviews for processing." |

### 2.2 PII Scrubbing Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 25 | **Email in unusual format** | `user+tag@sub.domain.co.in` or `"quoted"@domain.com` | Use a broad regex that catches most formats. Accept occasional false negatives over false positives. Test against edge cases. |
| 26 | **Phone number embedded in text** | "call 9876543210 for help" vs "order #9876543210" | Regex `[6-9]\d{9}` will catch both. Acceptable — better to over-redact than leak a phone number. Order numbers getting redacted is a minor cosmetic issue. |
| 27 | **Phone with country code variations** | `+91-98765-43210`, `091 9876543210`, `+919876543210` | Regex: `r'(\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}'` — handle spaces, hyphens, optional +91/091. |
| 28 | **Aadhaar-like number that isn't Aadhaar** | "Version 1234-5678-9012" matches Aadhaar regex | Accept false positives — redacting a version number is harmless. PII safety > cosmetic perfection. |
| 29 | **PAN card number** | `ABCDE1234F` format (Indian tax ID) | Add regex: `r'[A-Z]{5}\d{4}[A-Z]'` → `[ID REDACTED]`. |
| 30 | **Name mentioned in review** | "my friend Rahul also faced this" | Names are not reliably detectable via regex. Acknowledge this limitation in README. LLM prompt says "do not include names" but this is a best-effort, not guaranteed. |
| 31 | **URL in review text** | "see proof at http://imgur.com/abc123" | Add regex: `r'https?://\S+'` → `[URL REDACTED]`. URLs can contain tracking info or personal pages. |
| 32 | **UPI ID in review** | "send to user@oksbi" or "pay via 9876543210@paytm" | UPI IDs look like emails. The email regex will catch `user@oksbi`. For phone@upi: the phone regex catches the number, and the email regex catches `number@upi`. Double-redaction is fine. |
| 33 | **No PII in any review** | All reviews are clean | PII scrub runs and finds nothing — this is fine. No special handling needed. Don't warn about "no PII found." |
| 34 | **Entire review is PII** | "My number is 9876543210 and email is a@b.com" | After redaction, text becomes "[PHONE REDACTED] and email is [EMAIL REDACTED]". Still valid for classification — LLM will classify based on remaining context or mark it generically. |

### 2.3 Date Handling Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 35 | **Mixed date formats** | Some rows `2026-08-01`, others `01/08/2026` or `Aug 1, 2026` | Use `pd.to_datetime(df['date'], infer_datetime_format=True, errors='coerce')`. Drop rows where date is NaT. |
| 36 | **Dates far in the past** | A review from 2019 somehow in the CSV | Filter to `date >= (today - 12 weeks)`. Drop and log old reviews. |
| 37 | **All dates are the same** | Scraper bug returns same date for all reviews | The pipeline still works — date range in report will show a single day. Log warning: "All reviews have the same date." |
| 38 | **Timezone-aware vs naive datetimes** | Mixing `datetime` objects with and without tzinfo | Normalize all to naive UTC: `df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)`. |

---

## 3. LLM Classification (`pipeline/classify.py`)

### 3.1 Groq API Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 39 | **GROQ_API_KEY missing** | `os.getenv("GROQ_API_KEY")` returns `None` | Check at module import / app startup. Raise `EnvironmentError("GROQ_API_KEY not set. Add it to .env")` immediately. Don't wait until first API call. |
| 40 | **GROQ_API_KEY invalid/expired** | API returns 401 Unauthorized | Catch `AuthenticationError`. Return clear message: "Groq API key is invalid. Generate a new one at console.groq.com." |
| 41 | **Groq API is down** | 500/502/503 from Groq servers | Retry with exponential backoff (1s, 2s, 4s). After 3 retries: "Groq API is currently unavailable. Try again in a few minutes." |
| 42 | **Rate limit hit (429)** | Free tier: 30 requests/min, 6000 tokens/min | Exponential backoff. Also: add `time.sleep(2)` between batches to stay under rate. If persistent: reduce batch size from 25 → 15. |
| 43 | **Token limit exceeded** | Single batch too large for model's context window | If batch of 25 reviews exceeds token limit (8192 for llama-3.1-8b): reduce batch size dynamically. Estimate ~50 tokens/review avg. If `batch_tokens > 6000`, split the batch. |
| 44 | **Model not available** | `llama-3.1-8b-instant` removed from Groq | Fallback chain: `llama-3.1-8b-instant` → `llama3-8b-8192` → `mixtral-8x7b-32768`. Try next model on `ModelNotFoundError`. |

### 3.2 LLM Response Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 45 | **Response is not valid JSON** | Model returns markdown or plain text despite `response_format: json_object` | Wrap `json.loads()` in try/except. On `JSONDecodeError`: retry the batch once. If still fails: try extracting JSON from response with regex `r'\{.*\}'` (greedy). |
| 46 | **JSON valid but wrong structure** | Returns `{"themes": [...]}` instead of `{"results": [...]}` | Check for expected key `"results"`. If missing, check for common alternatives (`"themes"`, `"classifications"`, `"data"`). Normalize to expected format. |
| 47 | **LLM invents a 6th theme** | Model returns `"UI Bugs"` instead of `"App Performance & UX"` | Post-validation: `if theme not in ALLOWED_THEMES`. Try fuzzy matching (e.g., "UI Bugs" → closest match "App Performance & UX" via string similarity). If no close match: assign to an `"Other"` bucket (but `"Other"` must not appear in final report — redistribute to largest theme). |
| 48 | **LLM returns empty results** | `{"results": []}` | Retry once. If still empty: fall back to keyword-based classification (simple regex matching on theme keywords). |
| 49 | **LLM skips some reviews in batch** | Sent 25 reviews, got back 20 results | Check `len(results) == len(batch)`. If mismatch: identify missing indices, re-send only those reviews in a follow-up call. |
| 50 | **LLM assigns same theme to ALL reviews** | Every review classified as "App Performance & UX" | Check theme distribution. If one theme has > 80% of reviews: log warning. Don't override — the data might genuinely be skewed. But consider re-running with a rephrased prompt. |
| 51 | **LLM returns theme with different casing** | `"onboarding & kyc"` vs `"Onboarding & KYC"` | Case-insensitive comparison: `theme.strip().lower()` matched against `[t.lower() for t in ALLOWED_THEMES]`. Map back to canonical casing. |
| 52 | **LLM returns index out of range** | `{"index": 30}` when batch only had 25 items | Validate `0 <= index < len(batch)`. Discard out-of-range entries. Re-send orphaned reviews. |
| 53 | **Response truncated** | Model hits max_tokens mid-JSON | Set `max_tokens` generously (2000 for 25-review batch). If response ends mid-JSON: retry with smaller batch (15). |
| 54 | **Duplicate indices in response** | Two results both claim `"index": 5` | Deduplicate: keep first occurrence. Re-request missing indices. |

---

## 4. Quote Selection (`pipeline/group_quotes.py`)

### 4.1 Theme Distribution Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 55 | **Fewer than 3 themes have reviews** | Only 2 themes have any reviews (3 themes have 0) | Show all themes that have reviews (even if < 3). If only 2 themes: show 2 themes, pick 2 quotes, note in report "Only 2 themes identified." |
| 56 | **All reviews in one theme** | 100% of reviews classified under "Customer Support" | Show 1 theme (100%), pick 3 quotes from that theme instead of 1 each from 3 themes. Adjust report template to handle gracefully. |
| 57 | **Theme with only 1 review** | "Onboarding & KYC" has exactly 1 review | That single review becomes the quote for that theme. No selection logic needed. |
| 58 | **Tie in theme frequency** | Two themes each have exactly 47 reviews | Break tie consistently: alphabetical order of theme name. Deterministic output. |

### 4.2 Quote Selection Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 59 | **No medium-length reviews (30–150 words)** | All reviews in a theme are very short (< 30 words) | Relax length filter: if no medium-length reviews, accept any length. Pick the longest available review. |
| 60 | **No negative reviews (1–3 stars)** | A theme only has 4–5 star reviews | Accept positive reviews as quotes. Pain points aren't the only insights — positive quotes show what's working. |
| 61 | **Quote contains only redacted PII** | After PII scrub: `"[PHONE REDACTED] [EMAIL REDACTED]"` | Skip this quote — pick the next best review for that theme. Check `len(text.replace('[', '').replace(']', '').strip()) > 20` after redaction. |
| 62 | **Quote exceeds 50-word truncation** | Quote is 200 words, needs truncation to 50 | Truncate at 50 words at a sentence boundary if possible. If no sentence boundary in first 50 words, hard-truncate at 50 words + `"..."`. |
| 63 | **Quote has offensive language** | Profanity in a user review | Don't filter — real user quotes are verbatim (the brief says "verbatim, PII-scrubbed"). Profanity is not PII. If needed, add an optional profanity filter as a future enhancement. |
| 64 | **Duplicate quote selected** | Same review text appears in two themes (classification edge case) | Check for quote uniqueness across selected quotes. If duplicate: pick next-best review from that theme. |

---

## 5. Insight Generation (`pipeline/insights.py`)

### 5.1 LLM Recommendation Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 65 | **LLM returns fewer than 3 recommendations** | `{"recommendations": ["Fix KYC", "Improve payments"]}` — only 2 | If 2: retry once. If still 2: pad with a generic recommendation derived from the least-addressed theme: "Investigate {theme_name} issues reported by users." |
| 66 | **LLM returns more than 3 recommendations** | `{"recommendations": [...5 items...]}` | Truncate to first 3. Log warning. |
| 67 | **LLM hallucinated features/stats** | "42% of users in Tier-2 cities reported..." (made-up stat) | Hard to detect programmatically. Mitigation: system prompt explicitly forbids it. Manual spot-check during testing. Add a disclaimer in the report footer: "Recommendations based on review analysis." |
| 68 | **LLM returns vague recommendations** | "Improve the app experience" | Hard to detect programmatically. Mitigation: system prompt says "Be specific and actionable." Test with different prompt wordings during Phase 4. |
| 69 | **Recommendations are duplicates** | All 3 recommendations say the same thing differently | Check pairwise similarity (simple word overlap). If > 70% overlap between any two: retry with explicit instruction "Each recommendation must address a DIFFERENT theme." |
| 70 | **Very few reviews as input** | Only 5–10 reviews → insights are unreliable | Add a minimum threshold: if < 10 reviews after cleaning, warn in report: "⚠️ Low sample size ({n} reviews). Insights may not be representative." |

---

## 6. Report Generation (`pipeline/report.py`)

### 6.1 Word Count Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 71 | **Report naturally under 250 words** | Short themes + short quotes = 180 words | Fine — no trimming needed. 250 is a max, not a target. |
| 72 | **Report is 251–300 words** | Slightly over limit | Trim description fields first (theme one-liners). Shorten from longest description. Re-count. |
| 73 | **Report is 500+ words** | Long quotes + long recommendations | Aggressive trimming: truncate each quote to 30 words, each recommendation to 1 sentence. If still over: drop the summary paragraph. |
| 74 | **Word count after trimming is 0** | Bug in trimming logic strips everything | Safety: if word count < 50 after trimming, fall back to un-trimmed version with a warning logged. |
| 75 | **Markdown formatting affects word count** | `| # | Theme |` table syntax inflates word count | Count words only in content cells, not in Markdown syntax. Strip `|`, `#`, `---`, `>` before counting. Or: count words in a "rendered text" version (strip all markdown). |

### 6.2 PDF Generation Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 76 | **Unicode characters in PDF** | Emojis (📊, ⭐) or Hindi text crash `reportlab` | Use a Unicode-capable font (e.g., `DejaVuSans`). If emoji still fails: strip emojis from PDF version only (keep in Markdown). |
| 77 | **PDF exceeds one page** | Long report spills to page 2 | Reduce font size or trim content. Alternatively: allow 2 pages but log a warning. |
| 78 | **`output/` directory doesn't exist** | `FileNotFoundError` when saving PDF | `os.makedirs('output', exist_ok=True)` before saving. |
| 79 | **PDF file locked** | Previous PDF open in a viewer | Timestamp filenames: `weekly_pulse_2026-08-14.pdf`. Never overwrite a locked file. |
| 80 | **reportlab not installed** | Import error on deployment | It's in `requirements.txt` — but check at startup. If missing, fall back to Markdown-only output with a warning. |

---

## 7. Email Sending (`pipeline/email_sender.py`)

### 7.1 SMTP Authentication Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 81 | **SMTP_EMAIL not set** | `os.getenv("SMTP_EMAIL")` returns `None` | Check all 3 env vars (`SMTP_EMAIL`, `SMTP_APP_PASSWORD`, `RECIPIENT_EMAIL`) before attempting send. Return `{"success": false, "message": "Email not configured. Set SMTP_EMAIL in environment."}` |
| 82 | **App Password wrong** | Gmail returns `SMTPAuthenticationError` | Catch error. Return: "Gmail authentication failed. Verify your App Password is correct and 2-Step Verification is enabled." |
| 83 | **App Password has spaces/dashes** | Google shows App Password as `xxxx xxxx xxxx xxxx` | Strip spaces: `password.replace(' ', '')`. Google accepts with or without spaces, but be safe. |
| 84 | **2-Step Verification not enabled** | App Passwords option not available in Google Account | This is a pre-requisite, not a runtime error. Document clearly in README and `.env.example`. |
| 85 | **Gmail "Less Secure Apps" confusion** | User enables "Less Secure Apps" instead of App Password | Different thing. Document: "Do NOT use Less Secure Apps. Use App Passwords instead." |
| 86 | **Google blocks sign-in from new location** | Render server IP triggers "suspicious sign-in" alert | Pre-authorize: send a test email from local machine first. If Render is blocked, user must approve the sign-in attempt from their Gmail security alerts. |

### 7.2 Email Delivery Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 87 | **Recipient email invalid** | `not-an-email` or `user@` | Validate with regex before sending: `r'^[\w.-]+@[\w.-]+\.\w{2,}$'`. Return "Invalid email format" if fails. |
| 88 | **Recipient inbox full** | SMTP returns 552 (mailbox full) | Catch and return: "Recipient's mailbox is full. Try a different email address." |
| 89 | **Email goes to spam** | Gmail-to-Gmail works, but Gmail-to-Outlook lands in spam | Can't control this. Add to README as known limitation. Tip: "Check spam folder if email doesn't arrive within 5 minutes." |
| 90 | **PDF attachment too large** | Generated PDF is > 25MB (Gmail limit) | Check file size before attaching. If > 20MB: compress or skip attachment, include report in body only. In practice, a 1-page PDF will be ~50KB. |
| 91 | **SMTP timeout** | Render can't reach `smtp.gmail.com` (firewall/DNS issue) | Set timeout: `smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)`. On timeout: "Could not connect to Gmail. This may be a temporary network issue." |
| 92 | **Multiple rapid sends** | User clicks "Send Email" 10 times fast | Debounce on frontend (disable button after click, re-enable after response). Backend: track last send timestamp, reject if < 10 seconds since last send. |
| 93 | **Email body has unescaped HTML** | Review quotes contain `<script>` or `<img>` tags | Sanitize all user-generated content with `html.escape()` before embedding in HTML email body. |
| 94 | **Gmail daily send limit (500)** | Unlikely for this app, but possible if abused | Track daily send count (in-memory counter, resets daily). After 400: warn. After 480: refuse to send. |

### 7.3 STRETCH: Custom Recipient Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 95 | **User enters their own email as recipient** | Valid use case — no issue | Works fine. No special handling. |
| 96 | **User enters a distribution list** | `team@company.com` that forwards to 50 people | Works fine via SMTP. No special handling needed. |
| 97 | **User enters attacker-controlled email** | Phishing: attacker gets a "from: your-gmail" email | This is a real risk. Mitigate: add a footer to every email: "This report was auto-generated by App Review Insights Analyzer. The sender did not compose this email personally." |
| 98 | **Email injection attack** | User enters `victim@evil.com\r\nBCC: spam-list@evil.com` | SMTP header injection. Mitigation: validate email has NO `\r`, `\n`, or control characters. Use `email.utils.parseaddr()` to extract only the address part. |
| 99 | **Rate limiting bypass** | Attacker rotates IP to bypass IP-based rate limiting | IP-based limiting is best-effort. Add a global rate limit too: max 20 emails/hour total across all users. |

---

## 8. Web Application (`app/main.py`)

### 8.1 Route Handling Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 100 | **`/analyze` called before CSV exists** | First deploy — no `data/reviews.csv` yet | Check file existence before running pipeline. Return 400: "No reviews file found. Run the scraper first or upload a CSV." |
| 101 | **`/analyze` called while pipeline is running** | User clicks "Run Analysis" twice | Disable button on first click (frontend). Backend: use a simple lock/flag — if pipeline is running, return 409: "Analysis already in progress." |
| 102 | **`/send-email` called before `/analyze`** | No report generated yet | Check if `latest_report` exists in memory/disk. Return 400: "No report generated yet. Run analysis first." |
| 103 | **`/report/download` with no PDF** | PDF hasn't been generated | Return 404: "No report available for download. Run analysis first." |
| 104 | **`/health` returns but app is unhealthy** | App is up but Groq key is invalid | `/health` should do a lightweight check: verify env vars are set, `data/` directory exists. Return `{"status": "ok", "checks": {"env_vars": true, "data_dir": true}}`. |
| 105 | **Concurrent requests** | Multiple visitors trigger `/analyze` simultaneously | FastAPI is async — but the pipeline is CPU-bound. Use a global `asyncio.Lock()` so only one pipeline runs at a time. Queue others with "Analysis in progress, please wait." |

### 8.2 STRETCH: File Upload Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 106 | **Uploaded file is not CSV** | User uploads `.xlsx`, `.pdf`, or `.exe` | Check file extension AND content type. Reject non-`.csv` with: "Please upload a CSV file." |
| 107 | **CSV has wrong columns** | Uploaded CSV has `score` instead of `rating` | Check for required columns. Return: "CSV must contain columns: rating, text, date. Found: {actual_columns}." |
| 108 | **CSV is empty (0 rows)** | Header row only | Return: "Uploaded CSV has no data rows." |
| 109 | **CSV too large (>5MB)** | Massive file upload | Check `Content-Length` or read up to 5MB. Return 413: "File too large. Maximum size is 5MB (~5000 reviews)." |
| 110 | **Malicious CSV (CSV injection)** | Cell starts with `=`, `+`, `-`, `@` (formula injection) | Not a risk for this app (we don't open CSVs in Excel server-side). But sanitize: strip leading `=`, `+`, `@` from text fields as a precaution. |
| 111 | **CSV with BOM (Byte Order Mark)** | UTF-8 BOM (`\xef\xbb\xbf`) at start of file | Use `encoding='utf-8-sig'` when reading, which handles BOM transparently. |
| 112 | **Binary file renamed to .csv** | Upload a `.jpg` renamed to `.csv` | `pd.read_csv()` will raise `ParserError`. Catch it: "File does not appear to be a valid CSV." |

### 8.3 UI / Frontend Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 113 | **JavaScript disabled** | Fetch API calls won't work | Use `<noscript>` tag: "This app requires JavaScript. Please enable it." |
| 114 | **Mobile viewport** | UI layout breaks on phone screens | Responsive CSS: `max-width`, `@media` queries, flexible grid. Test at 375px width. |
| 115 | **Long report overflows container** | Report div has fixed height | Use `overflow-y: auto` or no fixed height — let content expand. |
| 116 | **Network error during analysis** | User loses connection mid-pipeline | Frontend: catch `fetch()` rejection. Show: "Network error. Check your connection and try again." Don't leave spinner running forever — add a 120s timeout. |
| 117 | **Browser back button during analysis** | Navigation interrupts the pipeline | The pipeline runs server-side — browser navigation doesn't cancel it. But the user loses the result. Consider storing last result in session/file so a refresh can retrieve it. |
| 118 | **Mobile OS file picker greys out CSV** | Android/iOS blocks selection of `.csv` due to MIME mismatch | Remove `accept=".csv"` from `<input type="file">` so users can pick any file, then validate `.csv` extension strictly in Javascript onChange handler. |

---

## 9. Deployment (Render)

### 9.1 Build & Runtime Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 118 | **Build fails on Render** | Dependency version conflict or missing system package | Pin all versions in `requirements.txt`. Test locally with `pip install -r requirements.txt` in a clean venv first. |
| 119 | **`$PORT` not set** | Render provides port via env var; local dev doesn't | Default: `port = int(os.getenv("PORT", 8000))`. Works both locally and on Render. |
| 120 | **Free tier cold start** | First request after sleep takes 30–60 seconds | Keep-alive mitigates this. For users hitting a cold instance: show loading state. The health ping should keep it warm. |
| 121 | **Free tier memory limit** | Render free tier has 512MB RAM | Pandas DataFrame for 2000 reviews ≈ 5MB. Groq responses ≈ 1MB. PDF generation ≈ 10MB. Total well under 512MB. But monitor for leaks. |
| 122 | **Render outage** | Render itself is down | Nothing to do — external dependency. Document in README: "If the app is down, it may be a Render outage. Check status.render.com." |
| 123 | **Disk storage on free tier** | Generated PDFs accumulate | Render free tier has ephemeral storage — files are lost on redeploy. This is actually fine: PDFs are re-generated on each analysis run. Don't rely on persistent file storage. |
| 124 | **Environment variable not set on Render** | Deployed but forgot to set `GROQ_API_KEY` | App should check all required env vars at startup. If any missing: log error and show a clear message on the UI: "Server misconfigured. Contact the administrator." |

### 9.2 Keep-Alive Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 125 | **GitHub Actions cron not firing** | GH Actions can delay cron jobs by minutes | Acceptable — a 10-min cron might fire every 12–15 min. Render sleeps after 15 min, so this is borderline. Consider 8-min cron: `*/8 * * * *`. |
| 126 | **GitHub Actions free tier exhausted** | 2000 min/month limit | 6 pings/hour × 24 hours × 30 days = 4320 runs. Each run ≈ 5 seconds. Total ≈ 6 hours/month. Well under 2000 min. Safe. |
| 127 | **RENDER_URL secret not set** | Ping job runs but URL is empty | `curl` will fail silently (`|| true`). Add a check: `if [ -z "$RENDER_URL" ]; then echo "RENDER_URL not set"; exit 1; fi` |
| 128 | **Render URL changes** | Re-deploy with a new service name | Update the `RENDER_URL` GitHub secret. Old pings will 404 harmlessly. |

---

## 10. End-to-End Flow Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 129 | **First-ever run (fresh deploy)** | No CSV, no reports, no previous state | App should show a clear "getting started" state. CORE: "Click 'Run Analysis' to analyze Groww reviews." STRETCH: "Upload a CSV or try with sample data." |
| 130 | **Pipeline succeeds but email fails** | Report displays correctly but SMTP throws error | Show report to user (it's the primary deliverable). Show email error separately: "Report generated successfully. Email failed: {reason}." Don't treat email failure as total failure. |
| 131 | **Pipeline fails midway** | Classification succeeds but insight generation fails | Return partial results if possible: "Classification completed. Insight generation failed. Showing partial report." This is better than showing nothing. |
| 132 | **CSV swapped between runs** | User runs analysis, swaps CSV, runs again | Each run should be stateless — read CSV fresh, run entire pipeline, generate new report. No stale caching. |
| 133 | **Multiple users on deployed app** | Two visitors click "Analyze" simultaneously | Global lock (Edge Case #105). Second user gets "Analysis in progress." Alternatively: queue requests. For a graded project, single-user is acceptable. |
| 134 | **Groq free tier runs out of credits** | All API calls fail with billing error | Catch and surface: "LLM service quota exhausted. The free tier has been exceeded for today. Try again tomorrow." |

---

## 11. Security Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 135 | **`.env` committed to git** | Secrets exposed in public repo | `.gitignore` must include `.env`. Add a pre-commit check or use `git-secrets`. Verify before first push. |
| 136 | **Secrets visible in Render logs** | App logs print API key or password | Never `print()` or `logging.info()` env var values. Log only: "GROQ_API_KEY: set" (boolean, not value). |
| 137 | **XSS in report display** | User review contains `<script>alert('xss')</script>` | All user content must be HTML-escaped when rendered in Jinja2 template. Jinja2 auto-escapes by default — verify `autoescape=True` is on. |
| 138 | **Path traversal in file upload** | Filename: `../../etc/passwd` | Use `werkzeug.utils.secure_filename()` or equivalent. Never use the uploaded filename directly for file system paths. Generate a UUID-based temp filename. |
| 139 | **Denial of Service** | Attacker sends 1000 concurrent requests | Not a priority for a graded project. Basic mitigation: global rate limit of 10 requests/min on `/analyze`. |
| 140 | **Server error leaks stack trace** | Unhandled exception shows internal paths | Add FastAPI exception handler that returns generic error JSON in production. Only show stack traces when `DEBUG=true`. |

---

## 12. Data Integrity Edge Cases

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 141 | **CSV modified while pipeline is reading** | Another process updates the CSV mid-read | Read entire CSV into memory at pipeline start. Don't stream. Single `pd.read_csv()` call is atomic enough. |
| 142 | **Report references stale data** | Report says "Week of Aug 1–7" but CSV has Aug 8–14 data | Compute date range from actual data: `min(df['date'])` to `max(df['date'])`. Don't hardcode or infer dates. |
| 143 | **Theme distribution doesn't sum to 100%** | Rounding errors: `33.3% + 33.3% + 33.3% = 99.9%` | Show individual percentages rounded to 1 decimal. Don't force sum to 100%. Or: show the largest theme's % as `100 - sum(others)`. |
| 144 | **Review count mismatch** | Report says "500 reviews analyzed" but only 450 were classified | Track counts at each stage. Report the count AFTER cleaning (what was actually processed), not the raw CSV row count. |

---

## Summary: Edge Case Coverage by Module

| Module | Edge Cases Covered | Critical Ones |
|--------|-------------------|---------------|
| **Scraper** | #1–#16 | #6 (zero reviews), #7 (no text), #14 (missing dir) |
| **Cleaner** | #17–#38 | #17 (empty DF), #18 (missing columns), #25–#32 (PII patterns) |
| **Classifier** | #39–#54 | #39 (missing key), #42 (rate limit), #45 (invalid JSON), #47 (6th theme) |
| **Quotes** | #55–#64 | #55 (< 3 themes), #61 (all-redacted quote) |
| **Insights** | #65–#70 | #65 (< 3 recs), #70 (low sample size) |
| **Report** | #71–#80 | #73 (word count overflow), #76 (Unicode in PDF) |
| **Email** | #81–#99 | #81 (env vars missing), #82 (auth failure), #98 (injection) |
| **Web App** | #100–#117 | #100 (no CSV), #101 (double-click), #105 (concurrency) |
| **Deployment** | #118–#128 | #119 (PORT env), #123 (ephemeral storage), #124 (env vars) |
| **End-to-End** | #129–#134 | #130 (partial failure), #132 (stateless runs) |
| **Security** | #135–#140 | #135 (.env in git), #137 (XSS), #138 (path traversal) |
| **Data Integrity** | #141–#144 | #142 (stale dates), #144 (count mismatch) |
| **Environment Setup** | #145–#148 | #145 (Windows encoding), #146 (pip path), #147 (OneDrive sync) |

---

## 13. Environment Setup Edge Cases (Discovered During Phase 1)

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 145 | **Windows console Unicode encoding** | `print("✓")` crashes with `UnicodeEncodeError` on Windows cp1252 console | Use ASCII alternatives: `[OK]`/`[FAIL]` instead of `✓`/`✗`. Discovered when `config.py` self-check crashed. |
| 146 | **`pip.exe` resolves to wrong Python** | Windows has multiple Python versions; `.\venv\Scripts\pip.exe install` installs to global Python instead of venv | Always use `venv\Scripts\python.exe -m pip install` — this guarantees the correct pip for the venv's Python. |
| 147 | **OneDrive sync conflicts** | Project is in OneDrive folder; large `venv/` causes sync issues or file locks | `venv/` is gitignored, but OneDrive still syncs it. Potential fix: add `venv/` to OneDrive's skip list, or create venv outside OneDrive. For now: acceptable since venv is recreatable. |
| 148 | **Config validation at startup vs lazy** | Checking all env vars at import time might crash the app if ANY var is missing | Config uses lazy validation via `validate_all_config()` — doesn't crash at import, only reports missing vars. The `/health` endpoint calls this function. Individual modules check their own vars before use. |

**Total: 151 edge cases documented across 14 categories.**

### 14. Cinematic Frontend & Render Deployment

| # | Edge Case | What Goes Wrong | Handling |
|---|-----------|-----------------|----------|
| 149 | **Render Spin-Down** | Free instances sleep after 15 mins. | Implement `keepalive/ping.js` running every 5 mins to hit the server. |
| 150 | **WebGL Context Loss** | Mobile browsers kill WebGL tabs. | Use `useFrame` cleanup and react-three-fiber's native fallback rendering. |
| 151 | **Frame Rate Drops** | Heavy shaders lag old devices. | Implement frame-rate monitoring; degrade gracefully by disabling post-processing passes. |
| 152 | **Empty Email Field Submission** | User clicks "Send" in Next.js UI without entering an email. | Handled client-side in `ReportView.tsx` (`if (!email) { setStatus("Please enter an email"); return; }`). |
| 153 | **No Report Generated Yet (Email Request)** | User calls `/send-email` before running `/analyze`. | Handled in `email_sender.py` by `get_latest_report_paths()` which raises `FileNotFoundError("No reports found to send")` mapped to a 500 error in `main.py` which displays nicely in the UI. |
