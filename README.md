# SatQuery AI

SatQuery AI is an interactive satellite-imagery analysis prototype combining a vision-language model with persistent Hindsight memory.

## Current prototype

- Natural-language satellite image analysis
- Groq vision-language analysis
- Hindsight memory and analyst corrections
- Flask backend
- Browser-based frontend

## Run locally

1. Create a Python virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Create `.env` from `.env.example` and add your API keys.
4. Start the backend:

```bash
python backend/app.py
```

Never commit real API keys or uploaded imagery.
