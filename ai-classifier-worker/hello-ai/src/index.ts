export default {
	async fetch(
		request: { json: () => PromiseLike<{ jobs: any }> | { jobs: any } },
		env: { AI: { run: (arg0: string, arg1: { messages: { role: string; content: string }[]; max_tokens: number }) => any } },
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

ROLE SCORING (0 to 1, independent):
- Score roles independently; do NOT force totals to sum to 1.
- UX Designer: trigger on product designer, ux, ui, interaction, visual design, prototyping, wireframes, design systems.
- Frontend Developer: require a frontend skill (HTML, CSS, DOM, React, Vue, Angular, Svelte, Next, Remix) AND a UI or browser context. JavaScript alone does not count.
- Software Engineer: trigger on software engineer, backend, full stack, systems, infrastructure, distributed systems.
- Mobile Developer: require a mobile dev skill (Kotlin, Swift, Flutter, React Native, Expo) AND a mobile context.
- Graphic Designer: require a graphic design skill (illustration, typography, Illustrator, Photoshop, Adobe Creative Cloud).
- Other: use only if no other role has meaningful signals.

SENIORITY CLASSIFICATION (must total 1):
- Intern = listings containing: “intern”, “internship”, “co-op.”
- Entry = junior, jr, associate, early career, new grad, ≤1 year experience.
- Mid and above = ANY requirement of 2+ years experience or more, OR senior, staff, lead, principal, manager, director, ownership, mentoring.

CRITICAL OVERRIDE (absolute rule):
- If the posting includes “2+ years,” “3+ years,” “5+ years,” or any experience requirement above 1 year, then the seniority MUST be classified as 100 percent mid_and_above, unless the posting explicitly includes “new grad” or “intern.”
- This rule overrides ALL other signals. Tone, responsibilities, or generic company boilerplate must be ignored.
- A job CANNOT be multiple levels at once.

UNKNOWN RULE:
- Unknown is used only when the description contains zero seniority signals at all (no years, no levels, no junior/senior wording). Otherwise do not use Unknown.

SUMMARY:
- Write 20 to 50 words describing core responsibilities and impact.
- Avoid marketing fluff.
- Always start with "Work as a...".

SKILLS:
- Extract only hard skills that appear verbatim.
- Max 4.
- No soft skills.

Output JSON Format (strict):
{
  "role_scores": {
    "ux_designer": <0 to 1>,
    "frontend_developer": <0 to 1>,
    "software_engineer": <0 to 1>,
	"mobile_developer": <0 to 1>,
	"graphic_designer": <0 to 1>,
    "other": <0 to 1>
  },
  "seniority_scores": {
    "intern": <0 to 1>,
    "entry": <0 to 1>,
    "mid and above": <0 to 1>,
	"unknown": <0 o 1>
  },
  "summary": "<20 to 60 word summary>",
  "skills": [ "<skill1>", "<skill2>", ... ],
}

CRITICAL:
- Output JSON ONLY
- Do not use backticks
- Do not use markdown
- Do not add explanation outside the JSON
- Begin your answer with '{' and end with '}'
- String values must not contain newlines. All text must be on a single line.

Do not include anything else besides the JSON object.
`;

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
					max_tokens: 800,
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

				// Aggressively remove newlines to handle invalid JSON from the model
				raw = raw.replace(/(\r\n|\n|\r)/gm, '');

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
							software_engineer: 0,
							other: 0,
						},
						seniority_scores: {
							intern: 0,
							entry: 0,
							'mid and above': 0,
							unknown: 0,
						},
						summary: '',
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
