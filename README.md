# Chess AI Web App

A browser-based chess trainer with a Python backend, a simple board UI, and a learnable AI agent.

## Tech stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python + Flask
- Chess rules / move validation: `python-chess`
- AI / model: PyTorch (`torch`)

## What it does

- Renders a playable chess board in the browser
- Validates legal chess moves on the backend
- Lets the AI respond automatically after each player move
- Records player move history for training
- Supports three training modes:
  - random game self-play
  - player move training
  - reinforcement from winning game moves

## Project structure

- `frontend/` - static UI files (`index.html`, `style.css`, `app.js`)
- `backend/` - Flask server and AI/game logic
- `backend/app.py` - main Flask application and API routes
- `backend/game.py` - chess game state, legal move handling, training history
- `backend/chess_ai.py` - policy network, move encoding, training utilities
- `backend/model.pth` - saved AI model weights
- `backend/requirements.txt` - Python dependencies

## Run locally

1. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

3. Start the Flask server:

```powershell
python backend\app.py
```

4. Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Gameplay and training

- Click squares to choose and play moves.
- The app sends the move to `/api/move`, validates it, then returns the updated board and the AI response.
- Use the buttons to:
  - start a new game
  - train the AI on random games
  - train the AI from your player moves
  - optionally learn from the winner's moves after a completed game

## API endpoints

- `GET /api/status` - current board state, legal moves, turn, game result
- `POST /api/new_game` - reset the board and start a new game
- `POST /api/move` - submit a player move and receive the AI move
- `POST /api/train` - train the policy network

## Notes

- The AI uses a lightweight convolutional policy network to predict moves.
- Training is done on board state tensors and move indices, not on full engine search.
- This app is a foundation for experimenting with chess AI training and move learning.
