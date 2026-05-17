# Poem Generator

Poem Generator is a simple AI poem-writing app. A user enters a situation or emotional prompt, chooses an emotion and style, and the app generates a short English poem.

## Features

- Generate poems from custom prompts.
- Choose emotion and writing style.
- Save generated poems to History.
- Copy generated poems with their prompt.

## Tech Stack

Vercel app:

- HTML
- CSS
- JavaScript
- Vercel Serverless Functions
- Groq API
- Browser `localStorage` for per-user history

## Project Structure

```text
.
|-- app.py              # Local Streamlit app
|-- database.py         # SQLite database helpers
|-- prompts.py          # Prompt options and prompt builder
|-- index.html          # Vercel frontend
|-- api/generate.js     # Vercel API route for poem generation
|-- vercel.json         # Vercel routing config
|-- package.json        # Vercel JavaScript project metadata
|-- requirements.txt    # Python dependencies for local app
`-- README.md
```
