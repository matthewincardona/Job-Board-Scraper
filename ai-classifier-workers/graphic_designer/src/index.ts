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

const GRAPHIC_DESIGNER_PROMPT = `
You are a specialized classifier for Graphic Designer roles.

Your job is to determine how relevant a job posting is to a Graphic Designer position.
Provide a score from 0.0 to 1.0, where 1.0 is a perfect match.

SCORING GUIDELINES:
- Provide a higher SCORE if it has a graphic design skill (such as illustration, typography, Illustrator, InDesign, Adobe Creative Suite, Figma).

Output JSON Format (strict):
{
  "score": <a number from 0.0 to 1.0>,
}

CRITICAL:
- Output JSON ONLY
- No backticks, no markdown, no explanation
- Begin with '{' and end with '}'
`;

async function classifyGraphicDesigner(job: { title: string; description: string }, env: any): Promise<ClassifierResult> {
	const userPrompt = `
Title: ${job.title}
Description: ${job.description}
`;

	const response = await env.AI.run('@cf/meta/llama-3.2-3b-instruct', {
		messages: [
			{ role: 'system', content: GRAPHIC_DESIGNER_PROMPT },
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
		console.error('Graphic Designer Classifier parse error:', raw);
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

			const result = await classifyGraphicDesigner(job, env);
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
