export interface Env {
	AI: any;
}

interface ClassifierResult {
	score: number;
}

// A function to clean the raw response from the AI
function cleanResponse(raw: string): string {
	return raw
		.replace(/```json/g, '')
		.replace(/```/g, '')
		.trim();
}

const SUMMARY_PROMPT = `
You are a specialized classifier for job role seniority.

Your job is to determine how senior a job posting is.
Provide a score from 0.0 to 1.0 for each seniority level, where 1.0 is a perfect match.

SCORING GUIDELINES (must total 1):
- Intern = listings containing: “intern”, “internship”, “co-op.”
- Entry = junior, jr, associate, early career, new grad, ≤1 year experience.
- Mid and above = ANY requirement of 2+ years experience or more, OR senior, staff, lead, principal, manager, director, ownership, mentoring.

Output JSON Format (strict):
{
    "intern": <0 to 1>,
    "entry": <0 to 1>,
    "mid and above": <0 to 1>,
	"unknown": <0 to 1>
}

CRITICAL:
- Output JSON ONLY
- No backticks, no markdown, no explanation
- Begin with '{' and end with '}'
`;

async function classifySeniority(job: { title: string; description: string }, env: any): Promise<ClassifierResult> {
	const userPrompt = `
Title: ${job.title}
Description: ${job.description}
`;

	const response = await env.AI.run('@cf/meta/llama-3.2-3b-instruct', {
		messages: [
			{ role: 'system', content: SUMMARY_PROMPT },
			{ role: 'user', content: userPrompt },
		],
		max_tokens: 100,
	});

	let raw = response.response ?? '';
	raw = cleanResponse(raw);

	try {
		const parsed = JSON.parse(raw);
		return {
			score: parsed.score ?? 0,
		};
	} catch (err) {
		console.error('Seniority Classifier parse error:', raw);
		return {
			score: 0,
		};
	}
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		if (request.method !== 'POST') {
			return new Response('Expected POST', { status: 405 });
		}

		try {
			const requestBody = await request.json();
			const job = (requestBody as any).job;

			if (!job || !job.title || !job.description) {
				return new Response('Missing job title or description', { status: 400 });
			}

			const result = await classifySeniority(job, env);
			return new Response(JSON.stringify(result), {
				headers: { 'Content-Type': 'application/json' },
			});
		} catch (e) {
			console.error('Error processing request:', e);
			const error = e instanceof Error ? e.message : String(e);
			return new Response(`Error processing request: ${error}`, { status: 500 });
		}
	},
};
