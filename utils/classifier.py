import pandas as pd

def classify_and_filter_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out jobs that are not entry-level or internships based on job titles.

    Args:
        df: DataFrame with job listings, must include a 'title' column.

    Returns:
        DataFrame with non-entry-level jobs removed.
    """
    if 'title' not in df.columns:
        raise ValueError("DataFrame must have a 'title' column.")

    seniority_keywords = [
        'sr.', 'senior', 'staff', 'director', 'manager', 'lead', 'principal', 'vp', 'president', 'expert', 'head of'
    ]
    
    # Ensure title column is string and handle missing values
    df['title'] = df['title'].astype(str).fillna('')

    # Create a boolean mask for rows to be removed
    mask = df['title'].str.contains('|'.join(seniority_keywords), case=False)

    filtered_df = df[~mask].copy()

    print(f"✓ Filtered by title: {len(df)} → {len(filtered_df)} ({len(df) - len(filtered_df)} jobs removed)")

    return filtered_df
