import csv
from jobspy import scrape_jobs
import pandas as pd
import re


def run_multiple_searches():
    """Run several role-based searches (all entry level), combine results, and save to CSV."""

    roles = [
        "graphic designer",
        "ux designer",
        "ux engineer",
        "web designer",
        "web developer",
        "frontend developer",
    ]

    # Default exclusions that must apply to ALL searches
    default_exclusions = ["-internship", "-intern", "-senior", "-manager", "-director", "-lead"]

    # Role-specific exclusions. Items already include leading '-'
    role_exclusions = {
        "graphic designer": ["-landscape", "-packaging", "-web", "-architecture", "-industrial", "-fashion", "-video", "-motion", "-ui", "-ux"],
        "ux designer": ["-landscape", "-packaging", "-web", "-architecture", "-industrial", "-fashion", "-video", "-motion"],
        "ux engineer": ["-graphic", "-landscape", "-packaging", "-fashion", "-video", "-motion"],
        "web designer": ["-landscape", "-packaging", "-industrial", "-fashion", "-video", "-motion"],
        "web developer": ["-landscape", "-packaging", "-industrial", "-fashion", "-video", "-motion"],
        "frontend developer": [""],
        "frontend engineer": [""],
    }

    all_jobs = []

    for role in roles:
        exclusions = default_exclusions + role_exclusions.get(role, [])
        exclusions_str = " ".join(exclusions)

        search_term = f"entry level {role} {exclusions_str}"
        google_search_term = f"entry level {role} jobs near NY, NY {exclusions_str}"

        print(f"Searching for: '{search_term}'")

        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter", "google"],
                # search_term=search_term,
                # google_search_term=google_search_term,
                search_term="entry level ux designer",
                google_search_term="entry level ux designer jobs near NY, NY",
                location="NY, NY",
                results_wanted=40,
                # job_level=["entry level"],
                hours_old=336, # last 14 days
                country_indeed="USA",
                linkedin_fetch_description=True
            )

            if jobs is None or len(jobs) == 0:
                print(f"No results for '{role}'")
                continue

            # tag results with the originating search term (use role as the job_category)
            jobs = jobs.copy()
            jobs["job_category"] = role
            print(f"Found {len(jobs)} jobs for '{role}'")
            all_jobs.append(jobs)

        except Exception as e:
            print(f"Error searching for '{role}': {e}")
            continue

    if not all_jobs:
        print("No jobs found for any search.")
        return

    # Combine and deduplicate
    combined = pd.concat(all_jobs, ignore_index=True)

    # Try to drop obvious duplicates: prefer 'job_id' if present, else drop fully duplicated rows
    if "job_id" in combined.columns:
        before = len(combined)
        combined = combined.drop_duplicates(subset=["job_id"])
        after = len(combined)
        print(f"Dropped {before - after} duplicates by job_id")
    else:
        before = len(combined)
        combined = combined.drop_duplicates()
        after = len(combined)
        print(f"Dropped {before - after} full-row duplicates")

    print(f"Total combined jobs: {len(combined)}")

    # Filter by description: remove anything that explicitly requests >1 years experience
    # Keep postings that explicitly request 0-x years, entry level, no experience, etc.
    # Try to find a description column in the DataFrame
    possible_desc_cols = [c for c in combined.columns if c.lower() in ("description", "job_description", "description_text", "full_description", "summary", "desc")]
    desc_col = possible_desc_cols[0] if possible_desc_cols else None

    def is_entry_level(desc: str) -> bool:
        """Return True if this posting should be considered entry level.

        We:
        - mark as non-entry if we detect explicit '1+' and higher experience, '2 years', '3+ years', 'at least 2 years', numeric ranges with lower bound >= 1 (e.g., 1-3), 'mid-level', 'senior', 'sr.', 'experienced'.
        - consider '0-#' patterns, 'entry level', 'no experience', 'new grad', 'junior' as entry-level.
        - default to True (keep) when we can't determine.
        """
        if not desc or not isinstance(desc, str):
            return True

        d = desc.lower()

        # quick checks for explicit 'non-entry' tokens
        non_entry_tokens = [r"\b(mid-?level|senior|sr\.|sr\b|experienced|experienced\b)\b", r"\b(at least|min|min\.|minimum|minumum)\s+\d+\s*(?:\+)?\s*(?:years|yrs|year)\b"]

        # years with + or standalone numbers (e.g., '1+', '2 years', '3+ years')
        # treat '1+' and above as non-entry-level; allow for optional escape backslash before plus (e.g., '5\+ years')
        years_plus_re = re.compile(r"\b(\d+)\s*\\?\+\s*(?:years|yrs|year)\b")
        # numbers in years, e.g., '2 years' or '3 years'
        years_simple_re = re.compile(r"\b(\d+)\s*(?:years|yrs|year)\b")
        # spelled-out numbers like 'five years' -> detect and convert to number
        word_numbers_re = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:years|yrs|year)\b")
        years_range_re = re.compile(r"\b(\d+)\s*[-–—to]+\s*(\d+)\s*(?:years|yrs|year)\b")

        # Check if there's explicit 'entry level', 'no experience', '0 years', or '0-#' range -> keep
        entry_tokens = [r"entry\s*-?level", r"\bno experience\b", r"\b0\s*(?:years|yrs|year)\b", r"\b0\s*[-–—to]+\s*\d+\s*(?:years|yrs|year)\b", r"new\s+grad|new\s+graduate|recent\s+graduate"]

        for t in entry_tokens:
            if re.search(t, d):
                return True

        # check for explicit non-entry indicators
        for t in non_entry_tokens:
            if re.search(t, d):
                return False

        # 1+ years, 2+ years, etc -> non-entry. Match '5+ years', '5\+ years', etc.
        m = years_plus_re.search(d)
        if m:
            num = int(m.group(1))
            if num >= 1:
                return False

        # simple numbers like '2 years' or '3 years' -> non-entry when >1
        for m in years_simple_re.finditer(d):
            num = int(m.group(1))
            # allow 0 or 0.x
            if num > 1:
                return False
            # If num == 1, be strict: treat '1 year' as ambiguous (keep) but '1-' as a range with upper >1 will be caught in range handling

        # Range, ex '1-3 years' or '2 to 5 years' -> if lower bound >= 1 then non-entry
        for m in years_range_re.finditer(d):
            low = int(m.group(1))
            # if range begins above 0, it's not entry level unless it starts at 0
            if low >= 1:
                return False

        # Spelled-out numbers like 'minimum of five years' -> treat as non-entry when >= 1
        word_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
            'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12
        }
        # check explicit 'minimum of five years' or 'minimum 5 years'
        # capture the numeric or word token after 'minimum' and before 'years' (allow optional 'of' and 'experience')
        min_years_re = re.compile(r"\bminimum(?: of)?\s+((?:\\?\d+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:\\?\+)?)(?:\s+years|\s+yrs|\s+year)(?:\s+of)?(?:\s+experience)?\b")
        m = min_years_re.search(d)
        if m:
            # get the numeric or word token
            token = m.group(0)
            # extract number from token
            # prefer digits
            dig = re.search(r"(\d+)", token)
            if dig:
                if int(dig.group(1)) >= 1:
                    return False
            else:
                w = re.search(r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)", token)
                if w:
                    if word_numbers.get(w.group(1), 0) >= 1:
                        return False

        # Word-number only check: e.g., 'five years', 'two years' -> treat >1 as non-entry
        for m in word_numbers_re.finditer(d):
            num_word = m.group(1)
            val = word_numbers.get(num_word, 0)
            if val > 1:
                return False

        # If nothing found, default to True (can't determine -> keep)
        return True

    if desc_col:
        before = len(combined)
        keep_mask = combined[desc_col].apply(is_entry_level)
        combined = combined.loc[keep_mask].reset_index(drop=True)
        after = len(combined)
        print(f"Filtered {before - after} non-entry-level jobs based on description ({desc_col}).")
    else:
        print("No description column found; skipped description-based filtering.")

    combined.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    print("Saved combined results to jobs.csv")


if __name__ == "__main__":
    run_multiple_searches()