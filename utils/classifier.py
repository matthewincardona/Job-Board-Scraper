import re
import pandas as pd
import hashlib

# ============================================================================
# HELPERS
# ============================================================================

def clean(text):
    """Normalize text to lowercase and strip whitespace."""
    if not isinstance(text, str):
        return ""
    return text.lower().strip()


def slug_hash(text):
    """Generate a short hash for job ID."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


# ============================================================================
# KEYWORD DEFINITIONS
# ============================================================================

# UX-related keywords for relevance scoring
UX_TITLE_KEYWORDS = [
    "ux designer", "ux/ui designer", "ui/ux designer",
    "product designer", "interaction designer", "experience designer",
    "ui designer", "user interface designer", "visual designer",
    "ux research", "user experience designer", "service designer",
    "design systems designer"
]

UX_LOOSE_KEYWORDS = [
    "ux", "ui", "interface", "wireframe", "wireframing",
    "prototyping", "figma", "sketch", "adobe xd",
    "user research", "usability", "user testing",
    "information architecture", "ia",
    "design system", "user centered", "human centered", "hcd",
    "accessibility", "responsive design"
]

# Senior/experienced role indicators (for exclusion)
SENIOR_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", 
    "staff", "director", "manager", "head of", "chief",
    "vp", "vice president", "executive", "architect",
    r"\biv\b", r"\bv\b",  # Roman numerals for levels
]

# Entry-level indicators
ENTRY_KEYWORDS = [
    r"\bentry[\s-]?level\b",
    r"\bjunior\b", 
    r"\bjr\.?\s+designer\b",
    r"\bassociate\s+(ux|ui|product|designer)\b",  # More specific
    r"\bnew\s+grad(uate)?\b", 
    r"\brecent\s+grad(uate)?\b",
    r"\bearly\s+career\b"
]

# Internship indicators
INTERN_KEYWORDS = [
    "intern", "internship", "apprentice", "co-op", 
    "coop", "fellowship", "trainee"
]

# ============================================================================
# REGEX PATTERNS
# ============================================================================

# Matches 0-2 years experience (entry-level friendly)
ENTRY_EXPERIENCE_REGEX = re.compile(
    r"\b(0\s*[-–to]*\s*[12]|0\+|1\+|1[\s-]?2|0[\s-]?1|less\s+than\s+2)\s*years?\b", 
    re.IGNORECASE
)

# Matches 3+ years experience (excludes entry-level)
EXCLUDE_EXPERIENCE_REGEX = re.compile(
    r"\b([3-9]|[1-9][0-9])\s*\+?\s*years?\b", 
    re.IGNORECASE
)

# Matches senior-level experience requirements
SENIOR_EXPERIENCE_REGEX = re.compile(
    r"\b(5\+|5-|[5-9]\+|10\+|extensive|proven\s+track|several\s+years)\b",
    re.IGNORECASE
)


# ============================================================================
# CLASSIFICATION FUNCTIONS
# ============================================================================

def has_senior_indicators(title, description=""):
    """
    Check if job has senior-level indicators.
    Returns True if this is clearly a senior/experienced role.
    """
    title_clean = clean(title)
    text = title_clean + " " + clean(description)
    
    # Check title for senior keywords (weighted heavily)
    for kw in SENIOR_KEYWORDS:
        if isinstance(kw, str):
            if kw in title_clean:
                return True
        else:  # regex pattern
            if kw.search(title_clean):
                return True
    
    # Check for senior experience requirements
    if SENIOR_EXPERIENCE_REGEX.search(text):
        return True
    
    # Check for 3+ years anywhere in posting
    if EXCLUDE_EXPERIENCE_REGEX.search(text):
        return True
        
    return False


def compute_ux_score(title, description=""):
    """
    Calculate UX relevance score (0-100).
    Higher scores indicate stronger UX design relevance.
    """
    title_clean = clean(title)
    desc_clean = clean(description)
    
    score = 0
    
    # Check for senior indicators first - they zero out the score
    if has_senior_indicators(title, description):
        return 0
    
    # Strong UX keywords in title (heavily weighted)
    for kw in UX_TITLE_KEYWORDS:
        if kw in title_clean:
            score += 50
            break  # Only count once from this category
    
    # Strong UX keywords in description (less weight)
    if score == 0:  # Only check if not already found in title
        for kw in UX_TITLE_KEYWORDS:
            if kw in desc_clean:
                score += 25
                break
    
    # Loose UX keywords (small increments)
    ux_keyword_count = sum(1 for kw in UX_LOOSE_KEYWORDS if kw in title_clean)
    score += min(ux_keyword_count * 3, 15)  # Cap at 15 points
    
    ux_desc_count = sum(1 for kw in UX_LOOSE_KEYWORDS if kw in desc_clean)
    score += min(ux_desc_count * 1, 10)  # Cap at 10 points
    
    # Boost for entry/intern indicators (only if no senior indicators)
    text = title_clean + " " + desc_clean
    
    # Check for intern keywords in title
    if any(kw in title_clean for kw in INTERN_KEYWORDS):
        score += 20
    
    # Check for entry-level keywords in title
    for pattern in ENTRY_KEYWORDS:
        if re.search(pattern, title_clean):
            score += 15
            break
    
    # Boost for explicit 0-2 years experience
    if ENTRY_EXPERIENCE_REGEX.search(text):
        score += 10
    
    return max(0, min(score, 100))


def classify_ux_category(score):
    """
    Classify job as UX or non-UX based on score.
    Threshold of 30 balances precision and recall.
    """
    if score >= 40:
        return "ux_designer"
    elif score >= 25:
        return "ux_possible"  # Borderline cases for review
    else:
        return "not_ux"


def classify_seniority(title, description=""):
    """
    Classify seniority level: intern, entry, or other.
    Only returns intern/entry for confirmed junior roles.
    """
    title_clean = clean(title)
    text = title_clean + " " + clean(description)
    
    # Exclude senior roles immediately
    if has_senior_indicators(title, description):
        return "senior"
    
    # Check for intern indicators (highest priority)
    for kw in INTERN_KEYWORDS:
        if kw in title_clean:
            return "intern"
    
    # Check for entry-level patterns in title
    for pattern in ENTRY_KEYWORDS:
        if re.search(pattern, title_clean):
            return "entry"
    
    # Check for 0-2 years experience mentioned anywhere
    if ENTRY_EXPERIENCE_REGEX.search(text):
        return "entry"
    
    # Default to unknown if no clear indicators
    return "unknown"


def generate_job_id(title, company, date_posted):
    """Generate unique job ID from key fields."""
    key = f"{clean(title)}|{clean(str(company))}|{clean(str(date_posted))}"
    return slug_hash(key)


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

def classify_jobs(df: pd.DataFrame, verbose=True) -> pd.DataFrame:
    """
    Main classification pipeline.
    
    Args:
        df: DataFrame with at minimum 'title' column
        verbose: Print progress/stats
        
    Returns:
        Classified DataFrame with new columns:
        - ux_score: 0-100 relevance score
        - ux_category: ux_designer, ux_possible, or not_ux
        - seniority: intern, entry, senior, or unknown
        - is_senior: boolean flag
        - id: unique job identifier
    """
    df = df.copy()
    
    # Ensure required columns exist
    required_cols = ["title", "company", "description", "date_posted"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    
    if verbose:
        print(f"Classifying {len(df)} jobs...")
    
    # Step 1: Compute UX relevance score
    df["ux_score"] = df.apply(
        lambda row: compute_ux_score(row["title"], row["description"]),
        axis=1
    )
    
    # Step 2: Classify UX category
    df["ux_category"] = df["ux_score"].apply(classify_ux_category)
    
    # Step 3: Classify seniority
    df["seniority"] = df.apply(
        lambda row: classify_seniority(row["title"], row["description"]),
        axis=1
    )
    
    # Step 4: Add senior flag for easy filtering
    df["is_senior"] = df.apply(
        lambda row: has_senior_indicators(row["title"], row["description"]),
        axis=1
    )
    
    # Step 5: Generate unique job IDs
    df["id"] = df.apply(
        lambda row: generate_job_id(row["title"], row["company"], row["date_posted"]),
        axis=1
    )
    
    if verbose:
        # Print summary stats
        print("\n" + "="*60)
        print("CLASSIFICATION SUMMARY")
        print("="*60)
        
        ux_jobs = df[df.ux_category == "ux_designer"]
        possible = df[df.ux_category == "ux_possible"]
        
        print(f"Total jobs: {len(df)}")
        print(f"UX Designer: {len(ux_jobs)} ({len(ux_jobs)/len(df)*100:.1f}%)")
        print(f"UX Possible: {len(possible)} ({len(possible)/len(df)*100:.1f}%)")
        print(f"Not UX: {len(df) - len(ux_jobs) - len(possible)}")
        
        print("\nSeniority Breakdown (UX roles only):")
        if len(ux_jobs) > 0:
            seniority_counts = ux_jobs["seniority"].value_counts()
            for level, count in seniority_counts.items():
                print(f"  {level}: {count} ({count/len(ux_jobs)*100:.1f}%)")
        
        print("="*60 + "\n")
    
    return df


def filter_entry_and_intern(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to filter for only entry-level and intern UX roles.
    
    Args:
        df: Classified DataFrame
        
    Returns:
        Filtered DataFrame with only entry/intern UX positions
    """
    return df[
        (df.ux_category == "ux_designer") & 
        (df.seniority.isin(["entry", "intern"]))
    ].copy()