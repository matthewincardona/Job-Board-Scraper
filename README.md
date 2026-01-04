venv/Scripts/activate.bat
python -m notebook

## Job Board Scraper — multi-search usage ✅

This project runs multiple job searches (sequentially) for common frontend/UX/UI/web roles and saves a combined CSV (`jobs.csv`). Each search is limited to "entry level" results and filters out common non-relevant terms.

How to run:

```bash
# Activate your virtualenv and ensure dependencies are installed (e.g., jobspy)
venv/Scripts/activate.bat
python -m pip install jobspy pandas

# Run the multi-search script
python main.py
```

Output:
- `jobs.csv` — combined results from the searches. The script adds a `job_category` column showing which role/search term produced each job posting (e.g. `graphic designer`, `ux ui designer`); duplicates are dropped when possible (by `job_id` if present, otherwise by full-row deduplication).

- Description-based filtering: After combining results, the script inspects job descriptions and removes postings that explicitly require more than entry-level experience (e.g., "1+ years", "2 years", "3 + years", "mid-level", "senior", ranges starting at 1+ etc.). Job posts that explicitly mention `0` years, `0-#` ranges (`0-1 yrs`, `0 to 2`), `entry level`, `no experience`, or `new grad` are kept.

- Description-based filtering: After combining results, the script inspects job descriptions and removes postings that explicitly require more than entry-level experience. It detects patterns such as:
	- Numeric years: `5+ years`, `4+ years`, `3 years`, `5 years of experience`.
	- Escaped plus signs: `5\+ years`, `4\+ years of experience` (some CSV exports or sites use escaped plus characters; the script accounts for this).
	- Minimum phrasing: `Minimum of five years of experience`, `minimum 5 years`, `minimum 3+ years`, etc.
	- Spelled-out numbers: `five years`, `four years` will be interpreted as years and removed if > 1.
	- Seniority tokens: `mid-level`, `senior`, `experienced`, `sr.`

	The script keeps listings explicitly marked as entry-level: `entry level`, `no experience`, `0 years`, `0-1 yrs`, `new grad`, etc.

If you want to limit or change the roles searched, edit the `roles` list in `main.py`.
