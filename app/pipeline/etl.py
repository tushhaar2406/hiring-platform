import requests
import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Job, PipelineLog
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

APP_ID  = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# ─── Step 1: Extract — fetch raw data from Adzuna API ──────

def fetch_jobs_from_api(keyword: str = "Python", location: str = "india", pages: int = 3) -> list:
    all_jobs = []

    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"

        params = {
            "app_id":           APP_ID,
            "app_key":          APP_KEY,
            "results_per_page": 20,
            "what":             keyword,
            "where":            location,
            "content-type":     "application/json"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()   # raises error if status is 4xx or 5xx
            data     = response.json()
            jobs     = data.get("results", [])
            all_jobs.extend(jobs)
            print(f"Page {page} — fetched {len(jobs)} jobs")

        except requests.exceptions.RequestException as e:
            print(f"API error on page {page}: {e}")
            break

    print(f"Total fetched from API: {len(all_jobs)}")
    return all_jobs

# ─── Step 2: Transform — clean data with Pandas ────────────

def transform_jobs(raw_jobs: list) -> pd.DataFrame:
    if not raw_jobs:
        return pd.DataFrame()

    df = pd.DataFrame(raw_jobs)

    # only keep columns that actually exist in the response
    required_columns = ["title", "company", "location", "description", "created"]
    optional_columns = ["salary_min", "salary_max"]

    # add optional columns with None if they don't exist in API response
    for col in optional_columns:
        if col not in df.columns:
            df[col] = None

    # now safely select all columns
    df = df[required_columns + optional_columns].copy()

    # clean company name — API returns dict {"display_name": "TCS"}
    df["company"] = df["company"].apply(
        lambda x: x.get("display_name", "Unknown") if isinstance(x, dict) else "Unknown"
    )

    # clean location — API returns dict {"display_name": "Pune"}
    df["location"] = df["location"].apply(
        lambda x: x.get("display_name", "Unknown") if isinstance(x, dict) else "Unknown"
    )

    # clean description
    df["description"] = df["description"].fillna("").str.strip()

    # clean salary
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # clean title
    df["title"] = df["title"].fillna("").str.strip()

    # add source
    df["source"] = "adzuna"

    # convert date
    df["posted_date"] = pd.to_datetime(df["created"], errors="coerce").dt.date

    # drop empty rows
    df = df[df["title"] != ""]
    df = df[df["company"] != "Unknown"]

    # drop duplicates
    df = df.drop_duplicates(subset=["title", "company"])
    df = df.reset_index(drop=True)

    print(f"After cleaning: {len(df)} jobs remaining")
    return df

# ─── Step 3: Load — insert clean data into PostgreSQL ──────

def load_jobs_to_db(df: pd.DataFrame, db: Session) -> dict:
    if df.empty:
        return {"inserted": 0, "skipped": 0}

    inserted = 0
    skipped  = 0

    for _, row in df.iterrows():
        # check if this job already exists — avoid duplicates
        existing = db.query(Job).filter(
            Job.title   == row["title"],
            Job.company == row["company"]
        ).first()

        if existing:
            skipped += 1
            continue

        # create new Job object
        new_job = Job(
            title       = row["title"],
            company     = row["company"],
            location    = row["location"],
            description = row["description"],
            salary_min  = None if pd.isna(row["salary_min"]) else row["salary_min"],
            salary_max  = None if pd.isna(row["salary_max"]) else row["salary_max"],
            source      = row["source"],
            posted_date = row["posted_date"]
        )

        db.add(new_job)
        inserted += 1

    db.commit()
    print(f"Inserted: {inserted} | Skipped: {skipped}")
    return {"inserted": inserted, "skipped": skipped}

# ─── Main pipeline function — runs all 3 steps ─────────────

def run_pipeline(keyword: str = "Python", location: str = "india"):
    db  = SessionLocal()
    log = PipelineLog(status="running")
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        print(f"\n{'='*50}")
        print(f"Pipeline started at {datetime.now()}")
        print(f"Keyword: {keyword} | Location: {location}")
        print(f"{'='*50}")

        # Step 1 — Extract
        raw_jobs = fetch_jobs_from_api(keyword=keyword, location=location)

        # Step 2 — Transform
        clean_df = transform_jobs(raw_jobs)

        # Step 3 — Load
        result = load_jobs_to_db(clean_df, db)

        # update log with results
        log.jobs_fetched  = len(raw_jobs)
        log.jobs_inserted = result["inserted"]
        log.jobs_skipped  = result["skipped"]
        log.status        = "success"
        db.commit()

        print(f"\nPipeline completed successfully")
        print(f"Fetched: {len(raw_jobs)} | Inserted: {result['inserted']} | Skipped: {result['skipped']}")

    except Exception as e:
        # if anything fails — log the error
        log.status        = "failed"
        log.error_message = str(e)
        db.commit()
        print(f"Pipeline failed: {e}")

    finally:
        db.close()

# run directly
if __name__ == "__main__":
    run_pipeline(keyword="Python developer", location="india")