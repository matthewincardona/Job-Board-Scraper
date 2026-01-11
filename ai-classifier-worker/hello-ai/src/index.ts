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
3. Choose the single best ROLE and single best SENIORITY based on the highest scores.

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
- "entry": junior, jr, associate, early career, new grad, less than 2 years.
- "mid and above": anything clearly requiring experience beyond entry level.

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
    "mid and above": <0 to 1>
  },
  "final_role": "<selected role>",
  "final_seniority": "<selected seniority>",
  "reasoning": "<short explanation>"
}

Do not include anything else besides the JSON object.

Score each category independently.
`;

			// - "frontend_developer_and_software_engineer": Only if BOTH frontend and SWE signals are strong.

			const results = [];

			for (const job of jobs) {
				const userPrompt = `
Title: ${job.title}
Description: ${job.description}
`;

				const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
					messages: [
						{ role: 'system', content: systemPrompt },
						{ role: 'user', content: userPrompt },
					],
					max_tokens: 200,
				});

				let parsed;
				try {
					parsed = JSON.parse(response.response_text);
				} catch (err) {
					parsed = {
						role_scores: {
							frontend_developer: 0,
							ux_designer: 0,
						},
						level_scores: {
							intern: 0,
							entry: 0,
						},
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
