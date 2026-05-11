import random

import chess
import torch
import torch.nn as nn
import torch.nn.functional as F

PROMOTION_OFFSET = 4096
PROMOTION_PIECES = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
OUTPUT_SIZE = 4096 + 64


def board_to_tensor(board: chess.Board) -> torch.Tensor:
    planes = torch.zeros(12, 8, 8, dtype=torch.float32)
    for square, piece in board.piece_map().items():
        color_offset = 0 if piece.color == chess.WHITE else 6
        plane = color_offset + (piece.piece_type - 1)
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        planes[plane, row, col] = 1.0
    return planes


def move_to_index(move: chess.Move) -> int:
    if move.promotion is None:
        return move.from_square * 64 + move.to_square

    if move.from_square >= 48:
        base = (move.from_square - 48) * 4
    else:
        base = 32 + (move.from_square - 8) * 4
    return PROMOTION_OFFSET + base + PROMOTION_PIECES.index(move.promotion)


def index_to_move(index: int, board: chess.Board) -> chess.Move | None:
    if index < 4096:
        from_sq = index // 64
        to_sq = index % 64
        return chess.Move(from_sq, to_sq)

    promo_index = index - PROMOTION_OFFSET
    if promo_index < 32:
        from_sq = 48 + promo_index // 4
    else:
        from_sq = 8 + (promo_index - 32) // 4
    promotion = PROMOTION_PIECES[promo_index % 4]
    to_sq = from_sq + 8 if from_sq >= 48 else from_sq - 8
    return chess.Move(from_sq, to_sq, promotion=promotion)


class ChessPolicyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(12, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 8 * 8, 512)
        self.fc2 = nn.Linear(512, OUTPUT_SIZE)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


def predict_move(board: chess.Board, model: ChessPolicyNet) -> str | None:
    model.eval()
    tensor = board_to_tensor(board).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor).squeeze(0)

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    legal_scores = []
    for move in legal_moves:
        idx = move_to_index(move)
        legal_scores.append((logits[idx].item(), move))

    winner = max(legal_scores, key=lambda item: item[0])[1]
    return winner.uci()


def generate_random_training_data(num_games: int = 50, max_moves: int = 80) -> list[tuple[torch.Tensor, int]]:
    data = []
    for _ in range(num_games):
        board = chess.Board()
        for _ in range(max_moves):
            legal = list(board.legal_moves)
            if not legal:
                break
            move = random.choice(legal)
            data.append((board_to_tensor(board), move_to_index(move)))
            board.push(move)
            if board.is_game_over():
                break
    return data


def train_policy_net(model: ChessPolicyNet, optimizer: torch.optim.Optimizer, data: list[tuple[torch.Tensor, int]], epochs: int = 3, batch_size: int = 64) -> None:
    model.train()
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        random.shuffle(data)
        for start in range(0, len(data), batch_size):
            batch = data[start : start + batch_size]
            states = torch.stack([item[0] for item in batch])
            target = torch.tensor([item[1] for item in batch], dtype=torch.long)
            optimizer.zero_grad()
            logits = model(states)
            loss = criterion(logits, target)
            loss.backward()
            optimizer.step()


def convert_move_history_to_training_data(move_history: list[dict]) -> list[tuple[torch.Tensor, int]]:
    """Convert player move history to training data (board_tensor, move_index pairs).
    
    Args:
        move_history: List of dicts with 'fen', 'move', 'color' keys
    
    Returns:
        List of (board_tensor, move_index) tuples for training
    """
    data = []
    for record in move_history:
        try:
            board = chess.Board(record['fen'])
            move = chess.Move.from_uci(record['move'])
            if move in board.legal_moves:
                board_tensor = board_to_tensor(board)
                move_index = move_to_index(move)
                data.append((board_tensor, move_index))
        except (ValueError, KeyError):
            pass  # Skip invalid moves
    return data
