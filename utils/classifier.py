import re
import pandas as pd
import hashlib

# --- Helpers ---

def clean(text):
    if not isinstance(text, str):
        return ""
    return text.lower().strip()

def slug_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

# --- UX scoring model ---

UX_TITLE_KEYWORDS = [
    "ux designer", "ux/ui designer", "ui/ux designer",
    "product designer", "interaction designer",
    "experience designer", "ui designer",
    "experience design", "visual designer",
    "ux research", "user experience"
]

UX_LOOSE_KEYWORDS = [
    "ux", "ui", "interface", "wireframe",
    "prototyping", "figma", "user research",
    "information architecture", "design system",
    "human centered", "hcd"
]

SENIOR_PENALTIES = [
    "senior", "sr ", "sr.", "lead", "manager",
    "director", "principal", "staff", "vp", "head of"
]

ENTRY_BONUS = [
    "entry level", "junior", "jr ", "jr.",
    "assistant", "associate", "new grad",
    "recent grad", "0 1 years", "0 2 years"
]

def compute_ux_score(title, description=""):
    text = clean(title) + " " + clean(description)
    score = 0

    for kw in UX_TITLE_KEYWORDS:
        if kw in text:
            score += 40

    for kw in UX_LOOSE_KEYWORDS:
        if kw in text:
            score += 2

    for kw in ENTRY_BONUS:
        if kw in text:
            score += 20

    for kw in SENIOR_PENALTIES:
        if kw in text:
            score -= 10

    return max(0, min(score, 100))

def classify_ux_category(score):
    return "ux_designer" if score >= 30 else "not_ux"

def classify_seniority(title, description=""):
    text = clean(title) + " " + clean(description)

    if any(w in text for w in ["intern", "internship", "apprentice", "co-op", "fellowship"]):
        return "intern"

    if any(w in text for w in ["entry level", "junior", "jr ", "jr.", "associate", "new grad", "recent grad"]):
        return "entry"

    if any(w in text for w in ["senior", "sr ", "sr.", "lead", "manager", "director", "principal", "staff"]):
        return "senior"

    if re.search(r"\b([2-4])\s*[\-to]*\s*[4-5]\s+years\b", text):
        return "mid"

    return "unknown"

def generate_job_id(title, company, date_posted):
    key = f"{clean(title)}|{clean(company)}|{clean(str(date_posted))}"
    return slug_hash(key)

def classify_jobs(df):
    df = df.copy()

    for col in ["title", "company", "description", "date_posted"]:
        if col not in df.columns:
            df[col] = ""

    df["ux_score"] = df.apply(
        lambda row: compute_ux_score(row["title"], row["description"]),
        axis=1
    )

    df["ux_category"] = df["ux_score"].apply(classify_ux_category)

    df["seniority"] = df.apply(
        lambda row: classify_seniority(row["title"], row["description"]),
        axis=1
    )

    df["id"] = df.apply(
        lambda row: generate_job_id(row["title"], row["company"], row["date_posted"]),
        axis=1
    )

    return df
