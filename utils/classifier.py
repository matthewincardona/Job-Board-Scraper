import re
import pandas as pd
import hashlib

# ============================================================================
# HELPERS
# ============================================================================

def clean(text):
    if not isinstance(text, str):
        return ""
    return text.lower().strip()

def normalize_slashes(text):
    """Normalize UI/UX variations to 'ui ux'"""
    return re.sub(r'ui\s*/\s*ux|ux\s*/\s*ui', 'ui ux', text.lower())

def slug_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

# ============================================================================
# KEYWORDS
# ============================================================================

UX_TITLE_KEYWORDS = [
    "ux designer", "ui ux designer", "ui ux",
    "product designer", "interaction designer", "experience designer",
    "ui designer", "user interface designer", "visual designer",
    "ux research", "user experience designer", "service designer",
    "design systems designer"
]

# Negative context phrases (job mentions UX but isn't a UX role)
NEGATIVE_CONTEXT = [
    "collaborate with ux",
    "work with ux", 
    "working with ux designers",
    "partner with ux",
    "alongside ux",
    "support ux team",
    "assist ux designers",
    "in collaboration with ux"
]

# Non-UX role indicators
NON_UX_ROLES = [
    "full stack", "full-stack", "fullstack",
    "software engineer", "backend engineer", "frontend engineer",
    "data scientist", "data analyst", "data engineer",
    "project manager", "product manager",
    "marketing", "content writer", "copywriter"
]

UX_LOOSE_KEYWORDS = [
    "wireframe", "wireframing", "prototyping", "figma", "sketch", "adobe xd",
    "user research", "usability", "user testing",
    "information architecture",
    "design system", "user centered", "human centered",
    "accessibility", "responsive design"
]

SENIOR_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", 
    "staff", "director", "manager", "head of", "chief",
    "vp", "vice president", "executive"
]

ENTRY_KEYWORDS = [
    r"\bentry[\s-]?level\b",
    r"\bjunior\b", 
    r"\bjr\.?\s+designer\b",
    r"\bassociate\s+(ux|ui|product|designer)\b",
    r"\bnew\s+grad(uate)?\b", 
    r"\brecent\s+grad(uate)?\b",
    r"\bearly\s+career\b"
]

INTERN_KEYWORDS = [
    "intern", "internship", "apprentice", "co-op", 
    "coop", "fellowship", "trainee"
]

# ============================================================================
# REGEX
# ============================================================================

ENTRY_EXPERIENCE_REGEX = re.compile(
    r"\b(0\s*[-–to]*\s*[12]|0\+|1\+|1[\s-]?2|0[\s-]?1|less\s+than\s+2)\s*years?\b", 
    re.IGNORECASE
)

EXCLUDE_EXPERIENCE_REGEX = re.compile(
    r"\b([3-9]|[1-9][0-9])\s*\+?\s*years?\b", 
    re.IGNORECASE
)

SENIOR_EXPERIENCE_REGEX = re.compile(
    r"\b(5\+|5-|[5-9]\+|10\+|extensive|proven\s+track|several\s+years)\b",
    re.IGNORECASE
)

# ============================================================================
# CLASSIFICATION
# ============================================================================

def has_senior_indicators(title, description=""):
    title_clean = clean(title)
    text = title_clean + " " + clean(description)
    
    for kw in SENIOR_KEYWORDS:
        if isinstance(kw, str):
            if kw in title_clean:
                return True
        else:
            if kw.search(title_clean):
                return True
    
    if SENIOR_EXPERIENCE_REGEX.search(text):
        return True
    
    if EXCLUDE_EXPERIENCE_REGEX.search(text):
        return True
        
    return False


def is_ux_role_in_title(title):
    """
    Check if title explicitly indicates a UX/UI/Product design role.
    This is the most important signal.
    """
    title_normalized = normalize_slashes(clean(title))
    
    # Direct title matches (highest confidence)
    for kw in UX_TITLE_KEYWORDS:
        if kw in title_normalized:
            return True
    
    return False


def has_negative_context(description):
    """
    Check if UX is mentioned in a 'working with' context rather than 'is a' context.
    """
    desc_clean = clean(description)
    
    for phrase in NEGATIVE_CONTEXT:
        if phrase in desc_clean:
            return True
    
    return False


def is_non_ux_role(title):
    """Check if this is clearly a non-UX role."""
    title_clean = clean(title)
    
    for role in NON_UX_ROLES:
        if role in title_clean:
            return True
    
    return False


def compute_ux_score(title, description=""):
    """Calculate UX relevance score with better context awareness."""
    
    title_clean = clean(title)
    title_normalized = normalize_slashes(title_clean)
    desc_clean = clean(description)
    
    score = 0
    
    # Immediate exclusions
    if has_senior_indicators(title, description):
        return 0
    
    if is_non_ux_role(title):
        # If it's clearly a non-UX role, heavily penalize
        # but allow some score if description is VERY UX-heavy (might be mislabeled)
        score = -30
    
    # TITLE ANALYSIS (most important)
    if is_ux_role_in_title(title):
        score += 60  # Strong signal
    
    # DESCRIPTION ANALYSIS
    # Check for negative context first
    if has_negative_context(description):
        score -= 20  # Big penalty for "working with UX" context
    
    # Count UX keywords in description (less weight than title)
    ux_desc_count = 0
    for kw in UX_TITLE_KEYWORDS:
        # Don't double count if already in title
        if kw in desc_clean and kw not in title_normalized:
            ux_desc_count += 1
    
    score += min(ux_desc_count * 8, 20)  # Cap at 20 points
    
    # Loose UX keywords (tools, methods)
    ux_tools_count = sum(1 for kw in UX_LOOSE_KEYWORDS if kw in desc_clean)
    score += min(ux_tools_count * 2, 15)  # Cap at 15 points
    
    # Boost for entry/intern in title (only if UX role)
    if score > 0:  # Only boost if already looks like UX role
        text = title_clean + " " + desc_clean
        
        if any(kw in title_clean for kw in INTERN_KEYWORDS):
            score += 15
        
        for pattern in ENTRY_KEYWORDS:
            if re.search(pattern, title_clean):
                score += 10
                break
        
        if ENTRY_EXPERIENCE_REGEX.search(text):
            score += 5
    
    return max(0, min(score, 100))


def classify_ux_category(score):
    if score >= 50:
        return "ux_designer"
    elif score >= 35:
        return "ux_possible"
    else:
        return "not_ux"


def classify_seniority(title, description=""):
    title_clean = clean(title)
    text = title_clean + " " + clean(description)
    
    if has_senior_indicators(title, description):
        return "senior_or_mid"
    
    for kw in INTERN_KEYWORDS:
        if kw in title_clean:
            return "intern"
    
    for pattern in ENTRY_KEYWORDS:
        if re.search(pattern, title_clean):
            return "entry"
    
    if ENTRY_EXPERIENCE_REGEX.search(text):
        return "entry"
    
    return "unknown"


def generate_job_id(title, company, date_posted):
    key = f"{clean(title)}|{clean(str(company))}|{clean(str(date_posted))}"
    return slug_hash(key)


def classify_jobs(df: pd.DataFrame, verbose=True) -> pd.DataFrame:
    df = df.copy()
    
    required_cols = ["title", "company", "description", "date_posted"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    
    if verbose:
        print(f"Classifying {len(df)} jobs...")
    
    df["ux_score"] = df.apply(
        lambda row: compute_ux_score(row["title"], row["description"]),
        axis=1
    )
    
    df["ux_category"] = df["ux_score"].apply(classify_ux_category)
    
    df["seniority"] = df.apply(
        lambda row: classify_seniority(row["title"], row["description"]),
        axis=1
    )
    
    df["is_senior"] = df.apply(
        lambda row: has_senior_indicators(row["title"], row["description"]),
        axis=1
    )
    
    df["id"] = df.apply(
        lambda row: generate_job_id(row["title"], row["company"], row["date_posted"]),
        axis=1
    )
    
    if verbose:
        print("\n" + "="*60)
        print("CLASSIFICATION SUMMARY")
        print("="*60)
        
        ux_jobs = df[df.ux_category == "ux_designer"]
        possible = df[df.ux_category == "ux_possible"]
        
        print(f"Total jobs: {len(df)}")
        print(f"UX Designer: {len(ux_jobs)} ({len(ux_jobs)/len(df)*100:.1f}%)")
        print(f"UX Possible: {len(possible)} ({len(possible)/len(df)*100:.1f}%)")
        
        if len(ux_jobs) > 0:
            print("\nSeniority (UX roles only):")
            for level, count in ux_jobs["seniority"].value_counts().items():
                print(f"  {level}: {count}")
        
        print("="*60 + "\n")
    
    return df