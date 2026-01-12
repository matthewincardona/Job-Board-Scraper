export default {
	async fetch(
		request: { json: () => PromiseLike<{ jobs: any }> | { jobs: any } },
		env: { AI: { run: (arg0: string, arg1: { messages: { role: string; content: string }[]; max_tokens: number }) => any } }
	) {
		try {
			const { jobs } = await request.json();

			if (!Array.isArray(jobs)) {
				return new Response(JSON.stringify({ error: 'Expected { jobs: [...] }' }), {
					status: 400,
					headers: { 'Content-Type': 'application/json' },
				});
			}

			const systemPrompt = `
You classify job postings into two dimensions:

ROLE CATEGORIES:
- ux_designer
- frontend_developer
- frontend_developer_and_software_engineer
- software_engineer
- other

SENIORITY CATEGORIES:
- intern
- entry
- mid and above

Your task:
1. Score each ROLE from 0 to 1 based on how strongly the job matches.
2. Score each SENIORITY from 0 to 1.
3. Write a short AI_SUMMARY of the job description.
4. Create a list of SKILLS mentioned in the job.

Scoring rules (very important):
- A score of 1.0 means extremely strong match.
- A score of 0.5 means ambiguous or partial match.
- A score below 0.2 means weak match.
- All scores must be independent — do NOT force them to sum to 1.

ROLE details:
- "ux_designer": Triggered by Product Designer, UX Designer, UI UX, Interaction Designer, Visual Designer.
- "frontend_developer": Must include at least one frontend signal such as HTML, CSS, DOM, UI implementation, browser APIs, or frameworks like React, Vue, Angular, Svelte, Next.js, Remix. 
  — NOTE: Mentions of “JavaScript” alone DO NOT count as frontend unless tied to UI or browser context.
- "software_engineer": Triggered by general SWE roles without explicit UI or frontend focus.
- "other": For roles that do not match any above categories.

SENIORITY details:
- "intern": internship, intern, co-op.
- "entry": junior, jr, associate, early career, new grad, less than 2 years, 'all levels'.
- "mid and above": anything clearly requiring experience beyond entry level.

AI_SUMMARY details:
- Must be between 30 and 60 words.
- Example format: "Work as a UX Designer working to create..." or "Work as a Frontend Developer responsible for building..."

SKILLS details:
- Extract only hard skills that appear verbatim in the job description text.
- Do NOT guess or infer missing skills.
- Output an array of plain strings.

Output JSON Format (strict):
{
  "role_scores": {
    "ux_designer": <0 to 1>,
    "frontend_developer": <0 to 1>,
    "frontend_developer_and_software_engineer": <0 to 1>,
    "software_engineer": <0 to 1>,
    "other": <0 to 1>
  },
  "seniority_scores": {
    "intern": <0 to 1>,
    "entry": <0 to 1>,
    "mid and above": <0 to 1>,
	"unknown": <0 to 1>
  },
  "ai_summary": "<30 to 60 word summary>",
  "skills": [ "<skill1>", "<skill2>", ... ],
}

CRITICAL:
- Output JSON ONLY
- Do not use backticks
- Do not use markdown
- Do not add explanation outside the JSON
- Begin your answer with '{' and end with '}'

Do not include anything else besides the JSON object.
`;

			// - "frontend_developer_and_software_engineer": Only if BOTH frontend and SWE signals are strong.

			const results = [];

			for (const job of jobs) {
				const userPrompt = `
Title: ${job.title}
Description: ${job.description}
`;

				const response = await env.AI.run('@cf/meta/llama-3.2-3b-instruct', {
					messages: [
						{ role: 'system', content: systemPrompt },
						{ role: 'user', content: userPrompt },
					],
					max_tokens: 200,
				});

				// Extract raw text returned by Cloudflare
				let raw = response.response ?? '';
				raw = raw.trim();

				// Remove ```json or ``` fencing
				raw = raw
					.replace(/^```json/i, '')
					.replace(/^```/, '')
					.replace(/```$/, '')
					.trim();

				let parsed;

				try {
					parsed = JSON.parse(raw);
				} catch (err) {
					console.error('FAILED TO PARSE RAW:', raw);

					// Full fallback schema
					parsed = {
						role_scores: {
							ux_designer: 0,
							frontend_developer: 0,
							frontend_developer_and_software_engineer: 0,
							software_engineer: 0,
							other: 0,
						},
						seniority_scores: {
							intern: 0,
							entry: 0,
							'mid and above': 0,
							unknown: 0,
						},
						ai_summary: '',
						skills: [],
					};
				}

				results.push(parsed);
			}

			return new Response(JSON.stringify({ results }), {
				headers: { 'Content-Type': 'application/json' },
			});
		} catch (err: any) {
			return new Response(JSON.stringify({ error: err.message }), {
				status: 500,
				headers: { 'Content-Type': 'application/json' },
			});
		}
	},
};
