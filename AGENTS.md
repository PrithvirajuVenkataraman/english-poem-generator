# English Poem Generator Agent Notes

English Poem Generator is a beginner-friendly Streamlit app for generating English poems with local Ollama and saving results to local SQLite.

## Project Rules

- Keep the code simple and readable for beginners.
- Do not use paid APIs.
- Use local Ollama for poem generation.
- Use local SQLite for poem history.
- Keep the app runnable with `streamlit run app.py`.
- Avoid adding unnecessary frameworks, folders, services, or abstractions.
- Do not add poet or lyricist style imitation features unless explicitly requested again.

## Current Structure

- `app.py` contains the Streamlit UI and Ollama request logic.
- `database.py` contains SQLite setup, save, and history functions.
- `prompts.py` contains prompt constants and prompt-building logic.
- `poems.db` is created locally when the app runs.

## Deployment Note

Local testing comes first. Vercel hosting will need a separate deployment plan because Vercel cannot directly use a visitor's local Ollama server, and local SQLite is not a durable production database there.
