# Implementation Plan — App Review Insights Analyzer (Groww)

> Derived from [prob_statement.md](file:///c:/Users/hardi/OneDrive/Desktop/app_analysis/PROB_statement.md)
> **Deadline:** Aug 16, 11:59 PM IST

---

## 0. Build Order & Phasing

All work is split into **7 phases**. Each phase is self-contained with clear entry/exit criteria. Finish and verify each phase before starting the next.

| # | Phase | Scope | Est. Time | Key Output |
|---|-------|-------|-----------|------------|
| 1 | **Project Setup & Environment** | Scaffold, dependencies, env vars, git init | ~30 min | Runnable project skeleton |
| 2 | **Review Scraper (Offline)** | `scripts/get_reviews.py` + generate `data/reviews.csv` | ~1 hr | CSV with 200+ Groww reviews |
| 3 | **Pipeline Core (Clean + Classify)** | `pipeline/clean.py` + `pipeline/classify.py` + Groq integration | ~2 hrs | Cleaned, theme-tagged DataFrame |
| 4 | **Pipeline Output (Quotes + Insights + Report)** | `pipeline/group_quotes.py` + `pipeline/insights.py` + `pipeline/report.py` | ~2 hrs | Weekly Pulse MD + PDF |
| 5 | **Web Application & UI** | FastAPI app, Jinja2 template, static assets, `/analyze` route | ~2 hrs | Working local web UI |
| 6 | **Email Integration** | `pipeline/email_sender.py`, Gmail SMTP setup, `/send-email` route, end-to-end CORE flow | ~1.5 hrs | Email received in inbox |
| 7 | **Deployment, README & STRETCH** | Render deploy, keep-alive GH Action, README.md, screenshots, STRETCH features | ~2 hrs | Live public URL + deliverables |

---

### Phase 1 — Project Setup & Environment (~30 min)

**Goal:** Runnable project skeleton with all dependencies installable.

**Tasks:**
1. Create the full directory structure (see §1 Project Scaffold below)
2. Initialize git repo, create `.gitignore`
3. Create `.env.example` with placeholder values
4. Create `requirements.txt` with all dependencies
5. Set up Python virtual environment and install deps
6. Create `pipeline/__init__.py` (empty, makes it a package)
7. Verify: `uvicorn --version` and `python -c "import groq"` both succeed

**Files created:**
- `requirements.txt`, `.env.example`, `.gitignore`, `pipeline/__init__.py`
- All empty directories: `app/`, `app/templates/`, `app/static/`, `scripts/`, `data/`, `output/`, `keepalive/`, `docs/screenshots/`

**Exit criteria:** `pip install -r requirements.txt` succeeds with no errors.

---

### Phase 2 — Review Scraper (Offline Script) (~1 hr)

**Goal:** Working script that pulls real Groww reviews into a CSV.

**Tasks:**
1. Write `scripts/get_reviews.py`:
   - Use `google-play-scraper` for app ID `com.nextbillion.groww`
   - Accept `--weeks` CLI arg (default: 8)
   - Filter reviews to the specified date window
   - Map to schema: `rating, title, text, date`
   - De-duplicate on `(text, date)`
   - Write to `data/reviews.csv` (UTF-8 with headers)
2. Run the script and verify the output CSV
3. Spot-check: open CSV, confirm ~200+ reviews, correct date range, valid ratings

**Files created:**
- `scripts/get_reviews.py`
- `data/reviews.csv` (generated output)

**Exit criteria:** `data/reviews.csv` exists with 200+ rows, correct columns, dates within 8–12 weeks.

---

### Phase 3 — Pipeline Core: Clean + Classify (~2 hrs)

**Goal:** Reviews are cleaned (PII-scrubbed, deduped) and classified into max 5 themes via Groq.

**Tasks:**
1. Write `pipeline/clean.py`:
   - `clean_reviews(df)` → drop empty rows, normalize dates, dedupe, PII regex scrub
   - Test PII regex against sample strings (emails, phone numbers, Aadhaar-like patterns)
2. Write `pipeline/classify.py`:
   - Define `DEFAULT_THEMES` (5 themes)
   - Implement batched Groq API calls (25 reviews/batch)
   - Force JSON response format
   - Post-call validation: reject themes not in allow-list
   - Exponential backoff on 429 errors
3. Write a quick test script to verify:
   - Load CSV → clean → classify → print theme distribution

**Files created:**
- `pipeline/clean.py`
- `pipeline/classify.py`

**Exit criteria:**
- PII regex catches test emails/phones/IDs
- All reviews classified into exactly the 5 allowed themes
- No invented themes in output
- Runs in <40s for 500 reviews

---

### Phase 4 — Pipeline Output: Quotes + Insights + Report (~2 hrs)

**Goal:** Full pipeline produces a complete Weekly Pulse report (MD + PDF).

**Tasks:**
1. Write `pipeline/group_quotes.py`:
   - Group by theme, compute frequency %
   - Select top 3 themes, pick 1 representative quote per theme
   - PII re-check on selected quotes
   - Truncate quotes to max 50 words
2. Write `pipeline/insights.py`:
   - Single Groq API call for 3 recommendations
   - System prompt enforces grounding (no hallucination)
   - Validate JSON response has exactly 3 items
3. Write `pipeline/report.py`:
   - Fill Weekly Pulse Markdown template
   - Enforce ≤250 words programmatically
   - Generate PDF via `reportlab`
   - Save to `output/weekly_pulse_{date}.pdf` and `.md`
4. Run full pipeline end-to-end:
   - CSV → clean → classify → group_quotes → insights → report
   - Inspect the output MD and PDF manually

**Files created:**
- `pipeline/group_quotes.py`
- `pipeline/insights.py`
- `pipeline/report.py`
- `output/weekly_pulse_*.pdf` and `.md` (generated)

**Exit criteria:**
- Report has exactly 3 themes, 3 quotes, 3 recommendations
- Word count ≤ 250
- PDF renders correctly, single page
- No PII in any output

---

### Phase 5 — Web Application & UI (~2 hrs)

**Goal:** Working FastAPI web app with a UI that runs the pipeline and displays results.

**Tasks:**
1. Write `app/main.py`:
   - FastAPI app with Jinja2 templates + static file serving
   - `GET /` → render `index.html`
   - `POST /analyze` → run full pipeline on `data/reviews.csv`, return results
   - `GET /report/download` → serve latest PDF
   - `GET /health` → return `{"status": "ok"}`
2. Write `app/templates/index.html`:
   - Header with project title and description
   - "Run Analysis" button (triggers `/analyze`)
   - Loading spinner during pipeline execution
   - Report display area (rendered inline)
   - Download PDF link
3. Write `app/static/style.css`:
   - Clean, professional styling
   - Responsive layout
   - Loading animation
4. Verify locally:
   - Run `uvicorn app.main:app --reload`
   - Click "Run Analysis" → see report rendered in browser
   - Click download → get PDF

**Files created:**
- `app/main.py`
- `app/templates/index.html`
- `app/static/style.css`

**Exit criteria:**
- App starts with `uvicorn`, serves UI at `localhost:8000`
- "Run Analysis" triggers pipeline and displays report in browser
- PDF download works
- `/health` returns 200

---

### Phase 6 — Email Integration (~1.5 hrs)

**Goal:** CORE email flow works end-to-end — report lands in your inbox.

**Tasks:**
1. **Gmail setup (one-time manual):**
   - Enable 2-Step Verification on Gmail account
   - Generate App Password (Google Account → Security → App Passwords)
   - Add to `.env`: `SMTP_EMAIL`, `SMTP_APP_PASSWORD`, `RECIPIENT_EMAIL`
2. Write `pipeline/email_sender.py`:
   - `send_report(recipient, subject, body_html, pdf_path) -> bool`
   - Build MIME email: HTML body + PDF attachment
   - Connect via `SMTP_SSL` to `smtp.gmail.com:465`
   - Error handling with meaningful messages
3. Add `POST /send-email` route to `app/main.py`:
   - CORE: reads `RECIPIENT_EMAIL` from env
   - Calls `send_report()` with latest generated report
   - Returns success/failure JSON
4. Update UI (`index.html`):
   - Add "Send Email" button (appears after report is generated)
   - Show success/failure confirmation message
5. **End-to-end CORE test:**
   - Run analysis → Send email → Check inbox → Take screenshot

**Files created:**
- `pipeline/email_sender.py`

**Files modified:**
- `app/main.py` (add `/send-email` route)
- `app/templates/index.html` (add email button + confirmation)

**Exit criteria:**
- Email received in inbox with correct subject, HTML body, and PDF attachment
- Screenshot taken as deliverable proof
- Error case (wrong password) shows meaningful message in UI

---

### Phase 7 — Deployment, README & STRETCH (~2 hrs)

**Goal:** Live public URL, complete documentation, all deliverables ready.

**Sub-phase 7A — Render Deployment (~45 min):**
1. Create Render account (free, no credit card)
2. Connect GitHub repo
3. Configure Web Service:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables in Render dashboard:
   - `GROQ_API_KEY`, `SMTP_EMAIL`, `SMTP_APP_PASSWORD`, `RECIPIENT_EMAIL`
5. Deploy and verify: hit public URL → run CORE flow → email received

**Sub-phase 7B — Keep-Alive (~15 min):**
1. Write `keepalive/ping.yml` (GitHub Actions cron every 10 min)
2. Add `RENDER_URL` as GitHub Actions secret
3. Push and verify: Actions tab shows successful pings

**Sub-phase 7C — README & Deliverables (~30 min):**
1. Write `README.md` with:
   - Project overview, data source, workflow explanation
   - Mermaid pipeline + deployment diagrams
   - Installation steps, tech stack table
   - Re-run instructions (swap CSV, re-run)
   - Theme legend (5 themes + descriptions)
   - Known limitations
2. Take screenshots of deployed website → save in `docs/screenshots/`
3. Embed screenshots in README
4. Prepare deliverable checklist:
   - Working Render URL
   - Weekly Pulse note (PDF/MD)
   - Email screenshot
   - Reviews CSV

**Sub-phase 7D — STRETCH features (only if time remains):**
1. CSV upload (`POST /analyze/upload` + drag-and-drop UI)
2. "Try with sample data" button + `data/sample_reviews.csv`
3. Custom email recipient input field + validation
4. Basic rate limiting on email sends
5. Create `render.yaml` blueprint (optional)

**Files created:**
- `keepalive/ping.yml`
- `README.md`
- `docs/screenshots/*.png`
- `data/sample_reviews.csv` (STRETCH)
- `render.yaml` (optional)

**Exit criteria:**
- Public Render URL is accessible and functional
- CORE flow works end-to-end on deployed site
- Keep-alive pings are running in GitHub Actions
- All deliverables from §9 are ready

---

## 1. Project Scaffold

```
app-review-insights/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point + routes
│   ├── templates/
│   │   └── index.html            # Jinja2 UI template
│   └── static/
│       └── style.css             # Minimal custom styling
├── pipeline/
│   ├── __init__.py
│   ├── clean.py                  # Step 2 — dedupe, PII strip, date normalize
│   ├── classify.py               # Step 3 — Groq batched classification
│   ├── group_quotes.py           # Step 4 — theme grouping + quote selection
│   ├── insights.py               # Step 5 — Groq recommendation generation
│   ├── report.py                 # Step 6 — Weekly Pulse builder (MD + PDF)
│   └── email_sender.py           # Step 7 — SMTP send
├── scripts/
│   └── get_reviews.py            # Offline scraper → CSV
├── tests/
│   ├── __init__.py
│   └── ...                       # Unit tests per module
├── data/
│   ├── reviews.csv               # Current week's Groww reviews (CORE)
│   └── sample_reviews.csv        # STRETCH — bundled sample
├── output/                       # Generated reports land here (gitignored except samples)
├── keepalive/
│   └── ping.yml                  # GH Actions keep-alive workflow
├── docs/
│   └── screenshots/              # Post-deploy screenshots for README
├── config.py                     # ★ Centralized config, constants, PII patterns, validation
├── requirements.txt
├── .env.example
├── .gitignore
├── render.yaml                   # Optional Render blueprint
└── README.md
```

---

## 2. Module-Level Design

### 2.1 `scripts/get_reviews.py` — Offline Review Scraper

**Purpose:** Run locally/manually to pull fresh Groww reviews and write `data/reviews.csv`.

**Libraries:** `google-play-scraper` (PyPI: `google-play-scraper`), optionally `app-store-scraper`.

**Logic:**
1. Use `google_play_scraper.reviews_all()` or paginated `reviews()` for app ID `com.nextbillion.groww`.
2. Filter to last 8–12 weeks by `at` (review date).
3. Map fields to output schema: `rating, title, text, date`.
4. De-duplicate on `(text, date)` before writing.
5. Write to `data/reviews.csv` (UTF-8, with header row).

**Output CSV schema:**

| Column | Type | Notes |
|--------|------|-------|
| `rating` | int (1–5) | Star rating |
| `title` | str \| empty | Review title (may be blank) |
| `text` | str | Review body — required, drop rows where empty |
| `date` | str `YYYY-MM-DD` | Normalized date |

**Invocation:**
```bash
python scripts/get_reviews.py            # defaults to last 8 weeks
python scripts/get_reviews.py --weeks 12 # override window
```

---

### 2.2 `pipeline/clean.py` — Data Cleaning

**Function:** `clean_reviews(df: pd.DataFrame) -> pd.DataFrame`

**Steps (in order):**
1. **Drop empty reviews** — remove rows where `text` is NaN / empty string after stripping whitespace.
2. **Normalize dates** — parse `date` column to `datetime`, drop rows outside the 8–12 week window, re-format to `YYYY-MM-DD`.
3. **De-duplicate** — drop exact duplicates on `text` (case-insensitive, stripped).
4. **PII scrub** — apply regex replacements **before** any LLM call:
   - Email: `r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'` → `[EMAIL REDACTED]`
   - Phone (Indian): `r'(\+91[\s-]?)?[6-9]\d{9}'` → `[PHONE REDACTED]`
   - Phone (generic): `r'\b\d{10,12}\b'` → `[PHONE REDACTED]`
   - Aadhaar-like: `r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'` → `[ID REDACTED]`
5. Return cleaned DataFrame.

---

### 2.3 `pipeline/classify.py` — LLM Theme Classification

**Function:** `classify_reviews(df: pd.DataFrame, themes: list[str]) -> pd.DataFrame`

**Theme allow-list (default — adjustable):**
```python
DEFAULT_THEMES = [
    "Onboarding & KYC",
    "Payments & Transactions",
    "Mutual Funds & Investments",
    "App Performance & UX",
    "Customer Support",
]
```

**Batching strategy:**
- Batch size: **25 reviews per API call** (tuneable constant).
- For 500 reviews → 20 API calls → ~20–40 sec on Groq free tier.

**Groq API call details:**
- Model: `llama-3.1-8b-instant` (fast, free-tier friendly) — fall back to `llama3-70b-8192` if quality is poor.
- Temperature: `0.0` (deterministic classification).
- `response_format`: `{ "type": "json_object" }` (force JSON mode).

**System prompt (exact):**
```
You are a product review classifier. You will receive a batch of app reviews.
For EACH review, assign exactly ONE theme from this list:
{themes_json}

Respond with a JSON object: {"results": [{"index": 0, "theme": "..."}, ...]}
Use the EXACT theme names from the list. Do NOT invent new themes.
```

**Post-call validation:**
1. Parse JSON response.
2. For each result, check `theme in allowed_themes`.
3. If an invalid theme appears → assign `"Other"` or retry that subset (max 1 retry).
4. Add `theme` column to DataFrame.

**Rate-limit handling:**
- Catch `429` / `RateLimitError` → exponential backoff (1s, 2s, 4s), max 3 retries per batch.

---

### 2.4 `pipeline/group_quotes.py` — Theme Grouping & Quote Selection

**Function:** `select_quotes(df: pd.DataFrame, top_n_themes: int = 3, quotes_per_report: int = 3) -> dict`

**Logic:**
1. Group by `theme`, compute `count` and `percentage` (of total reviews).
2. Sort descending by count → take top `top_n_themes` themes.
3. For each top theme, pick the most "representative" quote:
   - Filter reviews for that theme.
   - Prefer medium-length reviews (30–150 words) — too short is vague, too long is unwieldy.
   - Prefer 1–3 star ratings (pain points are more actionable).
   - Pick 1 quote per top theme (3 themes → 3 quotes).
4. **PII re-check** — run the same regex patterns from `clean.py` on each selected quote.
5. Truncate quotes to max 50 words each for report brevity.

**Return structure:**
```python
{
    "themes": [
        {"name": "Payments & Transactions", "count": 87, "pct": 34.5, "description": "..."},
        ...
    ],
    "quotes": [
        {"theme": "...", "text": "...", "rating": 2},
        ...
    ]
}
```

---

### 2.5 `pipeline/insights.py` — Recommendation Generation

**Function:** `generate_insights(themes: list[dict], quotes: list[dict]) -> list[str]`

**Groq API call:**
- Model: `llama-3.1-8b-instant`
- Temperature: `0.3` (slight creativity for actionable language, but grounded)
- `response_format`: `{ "type": "json_object" }`

**System prompt:**
```
You are a senior product manager analyzing app review data.
Given the top themes and representative user quotes below, generate exactly 3
concise, actionable product recommendations.

Rules:
- Each recommendation must be 1–2 sentences.
- Only reference information present in the provided data. Do NOT hallucinate
  causes, features, user segments, or statistics not shown.
- Be specific and actionable (e.g., "Reduce KYC verification time by..." not
  "Improve the app").

Respond as JSON: {"recommendations": ["...", "...", "..."]}
```

**Post-call validation:**
- Parse JSON, assert exactly 3 strings in `recommendations`.
- If fewer/more → retry once; if still wrong → truncate/pad with a generic fallback.

---

### 2.6 `pipeline/report.py` — Weekly Pulse Report Builder

**Function:** `build_report(themes, quotes, recommendations, review_count, date_range) -> tuple[str, bytes]`

Returns `(markdown_str, pdf_bytes)`.

**Markdown template:**
```markdown
# 📊 Weekly Product Pulse — Groww

**Period:** {start_date} – {end_date}
**Reviews analyzed:** {review_count}

---

## Top 3 Themes

| # | Theme | Share | Snapshot |
|---|-------|-------|----------|
| 1 | {theme_1_name} | {theme_1_pct}% | {theme_1_desc} |
| 2 | {theme_2_name} | {theme_2_pct}% | {theme_2_desc} |
| 3 | {theme_3_name} | {theme_3_pct}% | {theme_3_desc} |

## User Voices (verbatim, PII-scrubbed)

> "{quote_1}" — ⭐ {rating_1}

> "{quote_2}" — ⭐ {rating_2}

> "{quote_3}" — ⭐ {rating_3}

## Recommended Actions

1. {rec_1}
2. {rec_2}
3. {rec_3}

---

*Auto-generated by App Review Insights Analyzer. Data source: Google Play Store public reviews.*
```

**Word count enforcement (in code):**
```python
def enforce_word_limit(md: str, limit: int = 250) -> str:
    words = md.split()
    if len(words) > limit:
        # Trim the summary/description sections first, keep structure
        # If still over, hard-truncate and append "..."
        ...
    return trimmed_md
```

**PDF generation:**
- Use `reportlab` or `weasyprint` (if HTML-to-PDF preferred).
- Render the Markdown to a styled single-page PDF.
- Save to `output/weekly_pulse_{date}.pdf`.

---

### 2.7 `pipeline/email_sender.py` — SMTP Email

**Function:** `send_report(recipient: str, subject: str, body_html: str, pdf_path: str) -> bool`

**Implementation:**
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_report(recipient, subject, body_html, pdf_path):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("SMTP_EMAIL")
    msg["To"] = recipient
    msg["Subject"] = subject

    # HTML body (rendered report)
    msg.attach(MIMEText(body_html, "html"))

    # PDF attachment
    with open(pdf_path, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
        pdf_part.add_header("Content-Disposition", "attachment", filename="weekly_pulse.pdf")
        msg.attach(pdf_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_APP_PASSWORD"))
        server.send_message(msg)
    return True
```

**Pre-requisites:**
- Gmail account with **2-Step Verification** enabled.
- Generate an **App Password** (Google Account → Security → App Passwords).
- Store in `.env` as `SMTP_APP_PASSWORD`.

---

### 2.8 `app/main.py` — FastAPI Web Application

**Framework choice: FastAPI** — async-friendly, auto-docs, clean routing.

**Routes:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Serve main UI page |
| `POST` | `/analyze` | CORE: Run pipeline on `data/reviews.csv`, return report |
| `POST` | `/analyze/upload` | STRETCH: Accept uploaded CSV, run pipeline |
| `POST` | `/send-email` | Send last generated report via SMTP |
| `GET` | `/report/download` | Download latest PDF |
| `GET` | `/health` | Health check (for keep-alive ping) |

**UI (`templates/index.html`):**
- Single-page layout with sections:
  1. **Header** — title, brief description.
  2. **Analyze button** (CORE) — "Run Analysis on Groww Reviews".
  3. **Upload CSV** (STRETCH) — drag-and-drop zone + "Try with sample data" button.
  4. **Loading indicator** — spinner + progress text during pipeline execution.
  5. **Report display** — rendered Markdown report inline.
  6. **Email section** — CORE: "Send to preset email" button. STRETCH: email input field + send button.
  7. **Download** — PDF download link.

**Template engine:** Jinja2 (via `fastapi.templating`).

**Static files:** Serve from `app/static/`.

---

## 3. Environment & Secrets

### `.env.example`
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
SMTP_EMAIL=your-email@gmail.com
SMTP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
RECIPIENT_EMAIL=your-inbox@gmail.com
```

### `.gitignore`
```
.env
__pycache__/
*.pyc
output/*.pdf
data/reviews.csv
venv/
.venv/
```

> **Note:** `data/reviews.csv` is gitignored for safety (may contain real data). Ship `data/sample_reviews.csv` in the repo instead, and include `data/reviews.csv` only as a deliverable artifact (zip/upload separately).

---

## 4. Key Dependencies (`requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
jinja2>=3.1.3
python-multipart>=0.0.9
pandas>=2.2.0
groq>=0.5.0
reportlab>=4.1.0
python-dotenv>=1.0.1
google-play-scraper>=1.2.7
```

---

## 5. LLM Prompt Design — Summary

| Call | Model | Temp | Format | Batching | Retries |
|------|-------|------|--------|----------|---------|
| Classification (Step 3) | `llama-3.1-8b-instant` | 0.0 | JSON | 25 reviews/call | 3 (exp. backoff) |
| Insights (Step 5) | `llama-3.1-8b-instant` | 0.3 | JSON | Single call | 2 |

**Prompt guardrails applied:**
- Explicit allowed-theme list in classification prompt.
- "Only use information present in the provided reviews" in insight prompt.
- All outputs validated structurally in code post-call (not trusted blindly).

---

## 6. Deployment — Render

### 6.1 Render Configuration

- **Service type:** Web Service (free tier).
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** Set `GROQ_API_KEY`, `SMTP_EMAIL`, `SMTP_APP_PASSWORD`, `RECIPIENT_EMAIL` in the Render dashboard.

### 6.2 `render.yaml` (optional Blueprint)
```yaml
services:
  - type: web
    name: app-review-insights
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: SMTP_EMAIL
        sync: false
      - key: SMTP_APP_PASSWORD
        sync: false
      - key: RECIPIENT_EMAIL
        sync: false
    plan: free
```

### 6.3 `keepalive/ping.yml` — GitHub Actions Keep-Alive
```yaml
name: Keep Render Alive

on:
  schedule:
    - cron: '*/10 * * * *'   # Every 10 minutes
  workflow_dispatch:          # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render
        run: curl -fsS --max-time 30 "${{ secrets.RENDER_URL }}/health" || true
```

Store `RENDER_URL` as a GitHub Actions secret (e.g., `https://app-review-insights.onrender.com`).

---

## 7. STRETCH Features (build only after CORE is verified)

### 7.1 CSV Upload
- Add a `POST /analyze/upload` route accepting `multipart/form-data`.
- Validate file: must be `.csv`, must have required columns (`rating`, `text`, `date`), max 5 MB.
- Run the same pipeline on the uploaded file instead of `data/reviews.csv`.

### 7.2 "Try with Sample Data" Button
- Ship `data/sample_reviews.csv` (50–100 synthetic/anonymized reviews).
- Button triggers `POST /analyze` with a query param `?sample=true` → pipeline reads `data/sample_reviews.csv`.

### 7.3 Custom Email Recipient
- Add an email input field in the UI.
- Validate format with regex: `r'^[\w.-]+@[\w.-]+\.\w{2,}$'`.
- Basic rate limiting: max 5 emails per IP per hour (in-memory counter or simple middleware).

---

## 8. Testing & Verification Plan

### 8.1 Unit Tests (Local)
| Test | What it verifies |
|------|------------------|
| `test_clean.py` | PII regex catches emails, phones, Aadhaar; empty rows dropped; dates normalized |
| `test_classify.py` | Mock Groq response → valid themes only; invalid theme → fallback works |
| `test_report.py` | Generated report ≤ 250 words; has exactly 3 themes, 3 quotes, 3 recs |
| `test_email.py` | SMTP call made with correct args (mock `smtplib`) |

### 8.2 Integration / Manual Checks
- [ ] Run full pipeline locally on `data/reviews.csv` → verify report output
- [ ] Send email to own inbox → verify receipt + formatting
- [ ] Deploy to Render → hit public URL → run CORE flow end-to-end
- [ ] Verify keep-alive ping is working (check GH Actions run logs)
- [ ] Swap in a different CSV → re-run → confirm fresh report with zero code changes
- [ ] STRETCH: upload a CSV via UI → verify pipeline runs
- [ ] STRETCH: enter email in UI → verify email received

### 8.3 Constraint Checklist
- [ ] Max 5 themes — validated in code after every LLM call
- [ ] Report ≤ 250 words — word count enforced programmatically
- [ ] Exactly 3 themes, 3 quotes, 3 recommendations in output
- [ ] No PII in any output — regex scrub in `clean.py` + re-check in `group_quotes.py`
- [ ] Swapping CSV produces fresh report with zero code changes

---

## 9. Deliverables Mapping

| Deliverable | Source |
|-------------|--------|
| Working prototype link | Render deployment URL |
| Weekly Pulse note | `output/weekly_pulse_{date}.pdf` + `.md` |
| Email proof | Screenshot of received email in inbox |
| Reviews CSV | `data/reviews.csv` (or redacted version) |
| README.md | Includes: overview, data source, Mermaid diagrams, install steps, tech stack, re-run instructions, theme legend, known limitations, screenshots |

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Groq free-tier rate limits | Exponential backoff + batch size tuning; fallback: reduce batch to 15 |
| Groq model returns invalid JSON | Force `response_format: json_object`; parse with `try/except`; retry once |
| LLM invents a 6th theme | Hard-coded allow-list validated in code; reject + re-classify |
| Report exceeds 250 words | Programmatic word count; trim descriptions first, then hard-truncate |
| Gmail SMTP blocks send | Pre-test with App Password locally; have backup: use a second Gmail account |
| Render free tier sleeps | GitHub Actions keep-alive pings every 10 min |
| Deadline pressure | CORE fully verified before any STRETCH work begins |

## Cinematic Frontend & Keep-alive Update
* A new frontend is scaffolded in `stitch_rapid_action_engine/frontend` using Next.js, Framer, GSAP, and Three.js.
* A Render keep-alive polling script is deployed at `app-review-insights/keepalive/ping.js`.
