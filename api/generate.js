const DEFAULT_MODEL = process.env.OLLAMA_MODEL || "llama3.2";
const OLLAMA_BASE_URL = (process.env.OLLAMA_BASE_URL || "").replace(/\/$/, "");

function buildPrompt(situation, emotion, style) {
  return `
You are English Poem Generator.

Write a poem for this situation:
${situation}

Emotion: ${emotion}
Style: ${style}
Language instruction: Write in clear, natural English.
Creative instruction: Make the poem vivid, emotionally specific, and memorable. Avoid generic lines.

Return only valid JSON in this exact format:
{
  "title": "Poem title",
  "poem": "Poem with line breaks escaped using \\n"
}

Do not add markdown.
Do not add explanations outside the JSON.
Escape all line breaks inside JSON string values with \\n.
`;
}

function parsePoemJson(rawText) {
  try {
    return JSON.parse(rawText);
  } catch {
    const match = rawText.match(/\{[\s\S]*\}/);
    if (!match) {
      throw new Error("The model did not return valid JSON.");
    }
    return JSON.parse(match[0]);
  }
}

export default async function handler(request, response) {
  if (request.method !== "POST") {
    return response.status(405).json({ error: "Method not allowed." });
  }

  if (!OLLAMA_BASE_URL) {
    return response.status(500).json({
      error: "OLLAMA_BASE_URL is not set in Vercel environment variables.",
    });
  }

  try {
    const { situation = "", emotion = "Love", style = "Simple English" } = request.body || {};

    if (!situation.trim()) {
      return response.status(400).json({
        error: "Please enter a situation or emotional prompt.",
      });
    }

    const ollamaResponse = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: DEFAULT_MODEL,
        prompt: buildPrompt(situation, emotion, style),
        stream: false,
        format: "json",
      }),
    });

    if (!ollamaResponse.ok) {
      const errorText = await ollamaResponse.text();
      return response.status(502).json({
        error: `Ollama request failed with HTTP ${ollamaResponse.status}: ${errorText.slice(0, 500)}`,
      });
    }

    const ollamaData = await ollamaResponse.json();
    const poemData = parsePoemJson(ollamaData.response || "");

    return response.status(200).json({
      title: poemData.title || "Untitled Poem",
      poem: poemData.poem || "",
    });
  } catch (error) {
    return response.status(500).json({
      error: `Server error: ${error.message || "Something went wrong."}`,
    });
  }
}
