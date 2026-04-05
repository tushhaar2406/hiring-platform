from groq import Groq
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

# ─── Helper — call Groq ────────────────────────────────────
def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model    = MODEL,
        messages = [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ─── Helper — parse JSON ───────────────────────────────────
def parse_json_response(text: str) -> any:
    try:
        clean = re.sub(r"```json|```", "", text).strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        json_match = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return None
        return None

# ─── Extract skills from resume ────────────────────────────
def extract_skills_from_resume(resume_text: str) -> dict:
    prompt = f"""
You are an expert technical recruiter. Analyse this resume.

RESUME:
{resume_text}

Return ONLY a JSON object — no other text, no markdown:
{{
    "summary": "2-3 sentence summary of the candidate",
    "skills": ["python", "fastapi", "postgresql"],
    "experience_years": 1,
    "current_role": "Python Backend Developer"
}}

Extract all technical skills as simple lowercase words.
"""

    result = parse_json_response(call_groq(prompt))

    if not result:
        return {
            "summary":          "Could not parse resume",
            "skills":           [],
            "experience_years": 0,
            "current_role":     ""
        }

    return result

# ─── Match resume against ALL jobs in one API call ─────────
def match_resume_to_all_jobs(resume_skills: list, jobs: list) -> list:
    jobs_text = ""
    for i, job in enumerate(jobs):
        jobs_text += f"""
Job {i+1}:
  id: {job['id']}
  title: {job['title']}
  company: {job['company']}
  description: {job['description'][:200]}
---"""

    prompt = f"""
You are a technical recruiter matching a candidate to jobs.

CANDIDATE SKILLS: {', '.join(resume_skills)}

JOBS:
{jobs_text}

For each job return a match score and skills analysis.
Return ONLY a JSON array — no other text, no markdown:
[
  {{
    "job_id": 1,
    "match_score": 75,
    "matching_skills": ["python", "sql"],
    "missing_skills": ["docker"]
  }}
]

Rules:
- match_score: 0-100 based on skill match
- Include ALL {len(jobs)} jobs in the response
- Keep skills as simple lowercase words
"""

    result = parse_json_response(call_groq(prompt))

    if not result or not isinstance(result, list):
        return [
            {
                "job_id":          job["id"],
                "match_score":     0,
                "matching_skills": [],
                "missing_skills":  []
            }
            for job in jobs
        ]

    return result

# ─── Generate career advice ────────────────────────────────
def generate_career_advice(resume_summary: str, top_matches: list) -> str:
    matched_roles = [m.get("title", "") for m in top_matches[:3]]

    prompt = f"""
You are a senior career advisor for tech professionals in India.

CANDIDATE SUMMARY: {resume_summary}
TOP MATCHING ROLES: {', '.join(matched_roles)}

Give 3-4 sentences of specific, actionable career advice.
Focus on: what to learn next, which roles to target, how to improve their profile.
Be direct and practical — no generic advice.
"""

    return call_groq(prompt).strip()