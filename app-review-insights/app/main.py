import os
import sys
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import config  # type: ignore
from pipeline.clean import clean_reviews  # type: ignore
from pipeline.classify import classify_reviews  # type: ignore
from pipeline.group_quotes import select_top_quotes  # type: ignore
from pipeline.insights import generate_insights  # type: ignore
from pipeline.report import generate_reports
from pipeline.email_sender import send_report_email

app = FastAPI(title="App Review Insights API", version="1.0.0")

# Allow CORS for Next.js frontend and Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allowing all for now to unblock frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Endpoint for keep-alive pings and basic health verification."""
    return {"status": "ok", "message": "Pulse Engine is running"}

@app.post("/analyze")
def analyze_default_csv():
    """Runs the pipeline on the default data/reviews.csv file."""
    csv_path = config.DATA_DIR / "reviews.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Default reviews.csv not found. Scrape reviews first.")
    
    df = pd.read_csv(csv_path)
    return _run_pipeline(df)

@app.post("/analyze/upload")
async def analyze_uploaded_csv(file: UploadFile = File(...)):
    """Runs the pipeline on an uploaded CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
        
    # 1. Normalize column names (lowercase, strip whitespace, spaces to underscores)
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]

    # 2. Auto-map common alias/synonym column names
    alias_map = {
        "review": "text",
        "review_text": "text",
        "reviewtext": "text",
        "feedback": "text",
        "comment": "text",
        "comments": "text",
        "description": "text",
        "body": "text",
        "content": "text",
        "score": "rating",
        "stars": "rating",
        "star_rating": "rating",
        "name": "title",
        "headline": "title",
        "subject": "title"
    }
    # Iteratively rename columns, ensuring no duplicates are created
    new_cols = []
    seen = set()
    for col in df.columns:
        mapped_col = alias_map.get(col, col)
        if mapped_col not in seen:
            new_cols.append(mapped_col)
            seen.add(mapped_col)
        else:
            new_cols.append(col) # Keep original if mapped target already exists
    df.columns = new_cols

    # 3. Aggressive auto-fill for missing columns to ensure the analysis NEVER fails
    # If there's no 'text', we HAVE to fail because NLP needs text.
    if "text" not in df.columns:
        # Final fallback: if there's only 1 column, assume it's the text
        if len(df.columns) == 1:
            df["text"] = df.iloc[:, 0]
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required column(s): {{'text'}}. Available columns were: {set(df.columns)}."
            )

    # Auto-fill missing rating with neutral score
    if "rating" not in df.columns:
        df["rating"] = 3
        
    # Auto-fill missing title with empty string
    if "title" not in df.columns:
        df["title"] = ""

    if "date" not in df.columns:
        from datetime import date
        df["date"] = str(date.today())

    print("Columns before pipeline:", df.columns.tolist())
    return _run_pipeline(df)

class EmailRequest(BaseModel):
    email: str

@app.post("/send-email")
def send_email(req: EmailRequest):
    """Sends the latest generated PDF report via email."""
    try:
        # STRETCH feature implementation (Phase 6/7D)
        send_report_email(req.email)
        return {"status": "ok", "message": f"Report emailed to {req.email}"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/download")
def download_report():
    """Downloads the latest generated PDF report."""
    try:
        from pipeline.email_sender import get_latest_report_paths
        _, latest_pdf = get_latest_report_paths()
        return FileResponse(
            path=latest_pdf, 
            filename="weekly_pulse.pdf", 
            media_type="application/pdf"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="No report found. Run analysis first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _run_pipeline(df: pd.DataFrame):
    """Helper to run the core ML pipeline and return JSON structured data."""
    # 1. Clean
    df_clean = clean_reviews(df)
    
    # 2. Classify (using config limit for speed)
    df_classified = classify_reviews(df_clean)
    
    # 3. Group and Select Quotes
    grouped_data = select_top_quotes(df_classified)
    
    # 4. Generate Insights
    recommendations = generate_insights(grouped_data["theme_counts"], grouped_data["quotes"])
    
    # 5. Generate Markdown and PDF Reports
    generate_reports(grouped_data["theme_counts"], grouped_data["quotes"], recommendations)
    
    # Structure the response for Next.js frontend
    # Next.js expects specific keys to render the ReportView
    
    # Convert theme_counts dict to list of objects
    themes_list = []
    total_reviews = sum(grouped_data["theme_counts"].values())
    for name, count in grouped_data["theme_counts"].items():
        pct = (count / total_reviews) * 100 if total_reviews > 0 else 0
        themes_list.append({
            "title": name,
            "value": f"{int(pct)}%",
            "trend": "up" if pct > 20 else "down", # mock trend logic
            "color": "text-primary" if pct > 20 else "text-red-400"
        })
        
    return {
        "metrics": themes_list[:3], # Top 3
        "recommendations": recommendations,
        "quotes": [
            {
                "text": q["quote"],
                "stars": q.get("rating", 3)
            } for q in grouped_data["quotes"]
        ]
    }
