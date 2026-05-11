from flask import Flask, jsonify, request
import os
import torch

from game import ChessGame
from chess_ai import ChessPolicyNet, generate_random_training_data, train_policy_net, predict_move, convert_move_history_to_training_data

app = Flask(__name__, static_folder="../frontend", static_url_path="")
model = ChessPolicyNet()
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pth")
if os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH))
    except Exception:
        pass

game = ChessGame()


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "fen": game.board.fen(),
        "moves": game.legal_moves_uci(),
        "turn": "white" if game.board.turn else "black",
        "is_game_over": game.board.is_game_over(),
        "result": game.result(),
        "recorded_moves": len(game.get_move_history()),
    })


@app.route("/api/new_game", methods=["POST"])
def new_game():
    game.reset()
    return jsonify({
        "fen": game.board.fen(),
        "moves": game.legal_moves_uci(),
        "turn": "white",
        "is_game_over": False,
    })


@app.route("/api/move", methods=["POST"])
def make_move():
    data = request.get_json(force=True)
    uci = data.get("move")
    if not uci:
        return jsonify({"error": "missing move"}), 400
    if not game.push_uci(uci, is_player=True):  # Record player move for learning
        return jsonify({"error": "illegal move"}), 400

    response = {
        "fen": game.board.fen(),
        "moves": game.legal_moves_uci(),
        "last_move": uci,
        "is_game_over": game.board.is_game_over(),
        "result": game.result(),
    }

    if not response["is_game_over"]:
        ai_move = predict_move(game.board, model)
        if ai_move:
            game.push_uci(ai_move)
            response["ai_move"] = ai_move
            response["fen"] = game.board.fen()
            response["moves"] = game.legal_moves_uci()
            response["is_game_over"] = game.board.is_game_over()
            response["result"] = game.result()
    
    # If game just ended, offer reinforcement learning from winning moves
    if response["is_game_over"] and game.get_winning_moves():
        response["can_learn_from_win"] = True
        response["learning_message"] = "Game ended! You can train the AI from the winning moves using the 'Learn from Win' button."

    return jsonify(response)


@app.route("/api/train", methods=["POST"])
def train():
    data = request.get_json(force=True) or {}
    mode = data.get("mode", "random")  # "random", "player", or "winning"
    epochs = int(data.get("epochs", 2))
    
    if mode == "winning":
        # Train from moves made by the winning side
        winning_moves = game.get_winning_moves()
        if not winning_moves:
            return jsonify({
                "message": "Game must be complete with a winner. Play and finish a game first!",
                "data_pairs": 0,
                "epochs": epochs,
            }), 400
        training_data = convert_move_history_to_training_data(winning_moves)
        training_source = f"{len(winning_moves)} winning moves (reinforcement)"
    elif mode == "player":
        # Train exclusively from player moves
        move_history = game.get_move_history()
        if not move_history:
            return jsonify({
                "message": "No player moves recorded yet. Play some games first!",
                "data_pairs": 0,
                "epochs": epochs,
            }), 400
        training_data = convert_move_history_to_training_data(move_history)
        training_source = f"{len(move_history)} player moves"
    else:
        # Random training (original method)
        games = int(data.get("games", 100))
        training_data = generate_random_training_data(games)
        training_source = f"{games} random games"
    
    if not training_data:
        return jsonify({
            "message": "No valid training data.",
            "data_pairs": 0,
        }), 400
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    train_policy_net(model, optimizer, training_data, epochs=epochs)
    torch.save(model.state_dict(), MODEL_PATH)

    return jsonify({
        "message": f"Trained on {training_source} for {epochs} epochs.",
        "data_pairs": len(training_data),
        "epochs": epochs,
        "mode": mode,
    })


if __name__ == "__main__":
    app.run(debug=True)
