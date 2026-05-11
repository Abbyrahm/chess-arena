# Chess AI Web App

A starter chess web app with a Python backend and browser frontend.
The app includes a simple chess board UI, legal move validation, and a basic AI training pipeline.

## Run locally

1. Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

3. Start the server:

```powershell
python backend\app.py
```

4. Open `http://127.0.0.1:5000` in your browser.

## Features

- Chess board UI with move selection
- Move validation using `python-chess`
- AI move generation
- Training endpoint to generate training data and improve the model

## Notes

This is an MVP scaffold. The training pipeline is a simple policy learner and is meant as a starting point for more advanced chess AI improvements.
