import json
import os
import re
from http.server import BaseHTTPRequestHandler

import requests


DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "").rstrip("/")


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


def parse_poem_json(raw_text):
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def send_json(handler, status_code, data):
    body = json.dumps(data).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        send_json(self, 200, {"ok": True})

    def do_POST(self):
        if not OLLAMA_BASE_URL:
            send_json(
                self,
                500,
                {
                    "error": (
                        "OLLAMA_BASE_URL is not set. Add a public Ollama endpoint "
                        "as a Vercel environment variable."
                    )
                },
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            request_data = json.loads(raw_body)

            situation = request_data.get("situation", "").strip()
            emotion = request_data.get("emotion", "Love")
            style = request_data.get("style", "Simple English")

            if not situation:
                send_json(self, 400, {"error": "Please enter a situation or prompt."})
                return

            prompt = build_prompt(situation, emotion, style)
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": DEFAULT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=120,
            )
            response.raise_for_status()

            ollama_data = response.json()
            poem_data = parse_poem_json(ollama_data["response"])

            send_json(
                self,
                200,
                {
                    "title": poem_data.get("title", "Untitled Poem"),
                    "poem": poem_data.get("poem", ""),
                },
            )
        except requests.exceptions.RequestException as error:
            send_json(self, 502, {"error": f"Ollama request failed: {error}"})
        except json.JSONDecodeError:
            send_json(self, 502, {"error": "The model did not return valid JSON."})
        except Exception as error:
            send_json(self, 500, {"error": f"Something went wrong: {error}"})
