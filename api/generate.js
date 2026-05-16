const DEFAULT_MODEL = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";
const GROQ_API_KEY = process.env.GROQ_API || process.env.GROQ_API_KEY || "";
const GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";

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

  if (!GROQ_API_KEY) {
    return response.status(500).json({
      error: "GROQ_API is not set in Vercel environment variables.",
    });
  }

  try {
    const { situation = "", emotion = "Love", style = "Simple English" } = request.body || {};

    if (!situation.trim()) {
      return response.status(400).json({
        error: "Please enter a situation or emotional prompt.",
      });
    }

    const groqResponse = await fetch(GROQ_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${GROQ_API_KEY}`,
      },
      body: JSON.stringify({
        model: DEFAULT_MODEL,
        messages: [
          {
            role: "user",
            content: buildPrompt(situation, emotion, style),
          },
        ],
        temperature: 0.85,
        max_tokens: 900,
        response_format: { type: "json_object" },
      }),
    });

    if (!groqResponse.ok) {
      const errorText = await groqResponse.text();
      return response.status(502).json({
        error: `Groq request failed with HTTP ${groqResponse.status} ${groqResponse.statusText}: ${errorText.slice(0, 500)}`,
      });
    }

    const groqData = await groqResponse.json();
    const rawText = groqData.choices?.[0]?.message?.content || "";
    const poemData = parsePoemJson(rawText);

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
