DEFAULT_MODEL = "llama3.2"

EMOTIONS = ["Love", "Longing", "Heartbreak", "Anger", "Peace", "Closure", "Hope"]

STYLES = [
    "Simple English",
    "Modern Poetic",
    "Classical Poetic",
    "Dark Poetic",
    "Cinematic",
]


def build_prompt(situation, emotion, style):
    return f"""
You are English Poem Generator.

Write a poem for this situation:
{situation}

Emotion: {emotion}
Style: {style}
Language instruction: Write in clear, natural English.
Creative instruction: Make the poem vivid, emotionally specific, and memorable. Avoid generic lines.

Return only valid JSON in this exact format:
{{
  "title": "Poem title",
  "poem": "Poem with line breaks escaped using \\n"
}}

Do not add markdown.
Do not add explanations outside the JSON.
Escape all line breaks inside JSON string values with \\n.
"""
