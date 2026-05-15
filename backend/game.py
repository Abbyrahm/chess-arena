import chess


class ChessGame:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.board = chess.Board()
        self.move_history = [] # Track (board_state_fen, move_uci, player_color) for learning
        self.all_moves = []  # Track all moves in current game for reinforcement learning

    def legal_moves_uci(self):
        return [move.uci() for move in self.board.legal_moves]

    def push_uci(self, uci: str, is_player: bool = False):
        """Push move and optionally record for learning.
        
        Args:
            uci: Move in UCI format (e.g., 'e2e4')
            is_player: Whether this was a player move (for learning)
        """
        try:
            move = chess.Move.from_uci(uci)
            if move in self.board.legal_moves:
                # Record all moves for reinforcement learning
                self.all_moves.append({
                    'fen': self.board.fen(),
                    'move': uci,
                    'color': 'white' if self.board.turn else 'black',
                    'is_player': is_player
                })

                if is_player:
                    # Also record in player history
                    self.move_history.append({
                        'fen': self.board.fen(),
                        'move': uci,
                        'color': 'white' if self.board.turn else 'black'
                    })
                self.board.push(move)
                return True
        except ValueError:
            pass
        return False

    def result(self):
        """Return game result: '1-0' (white wins), '0-1' (black wins), '1/2-1/2' (draw), or None (ongoing)"""
        # Check for checkmate first (most important)
        if self.board.is_checkmate():
            # If it's white's turn and they're checkmated, black won
            return "0-1" if self.board.turn else "1-0"
        
        # Only check for draws if game is actually over
        if self.board.is_game_over():
            if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_fivefold_repetition() or self.board.is_seventyfive_moves():
                return "1/2-1/2"
        
        # Game is still in progress
        return None

    def get_move_history(self) -> list[dict]:
        """Return recorded player moves for training."""
        return self.move_history.copy()
    
    def get_winning_moves(self) -> list[dict] | None:
        """Return moves made by the winner. Returns None if game not over or draw."""
        if not self.board.is_game_over():
            return None
        
        result = self.result()
        if result is None or result == "1/2-1/2":  # No clear winner
            return None
        
        # Determine winner: "1-0" = white won, "0-1" = black won
        winner_color = 'white' if result == "1-0" else 'black'
        winning_moves = [m for m in self.all_moves if m['color'] == winner_color]
        return winning_moves
