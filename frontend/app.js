const boardElement = document.getElementById("board");
const selectedMoveElement = document.getElementById("selectedMove");
const lastAiMoveElement = document.getElementById("lastAiMove");
const gameStatusElement = document.getElementById("gameStatus");
const logElement = document.getElementById("log");
const newGameButton = document.getElementById("newGameButton");
const trainButton = document.getElementById("trainButton");
const trainPlayerButton = document.getElementById("trainPlayerButton");
const recordedMovesElement = document.getElementById("recordedMoves");

let boardState = null;
let selectedSquare = null;
let legalMoves = [];
let promotionMovePrefix = null;

const pieceMap = {
  p: "♟",
  r: "♜",
  n: "♞",
  b: "♝",
  q: "♛",
  k: "♚",
  P: "♙",
  R: "♖",
  N: "♘",
  B: "♗",
  Q: "♕",
  K: "♔",
};

function squareName(file, rank) {
  return String.fromCharCode(97 + file) + (rank + 1);
}

function setLog(message, level = "info") {
  const formatted = `${new Date().toLocaleTimeString()} — ${message}`;
  if (level === "warn") {
    console.warn(formatted);
  } else if (level === "error") {
    console.error(formatted);
  } else {
    console.log(formatted);
  }
  if (logElement) {
    logElement.value = `${formatted}\n${logElement.value}`;
  }
}

function renderBoard(fen) {
  boardElement.innerHTML = "";
  const rows = fen.split(" ")[0].split("/");
  for (let rank = 7; rank >= 0; rank--) {
    const row = rows[7 - rank];
    let file = 0;
    for (const char of row) {
      if (!isNaN(char)) {
        const count = Number(char);
        for (let i = 0; i < count; i++) {
          const square = document.createElement("div");
          square.dataset.square = squareName(file, rank);
          square.className = `square ${(rank + file) % 2 === 0 ? "light" : "dark"}`;
          square.addEventListener("click", onSquareClick);
          boardElement.appendChild(square);
          file += 1;
        }
        continue;
      }
      const square = document.createElement("div");
      square.dataset.square = squareName(file, rank);
      square.className = `square ${(rank + file) % 2 === 0 ? "light" : "dark"}`;
      square.textContent = pieceMap[char] || "";
      square.addEventListener("click", onSquareClick);
      boardElement.appendChild(square);
      file += 1;
    }
  }
}

function updateStatus(status) {
  gameStatusElement.textContent = status;
}

function showPromotionPicker() {
  const picker = document.getElementById("promotionPicker");
  picker.style.display = "flex";
}

function hidePromotionPicker() {
  promotionMovePrefix = null;
  const picker = document.getElementById("promotionPicker");
  picker.style.display = "none";
}

function highlightSelected() {
  const legalTargets = new Set(legalMoves.map((move) => move.slice(2)));
  document.querySelectorAll(".square").forEach((square) => {
    const squareName = square.dataset.square;
    square.classList.toggle("selected", squareName === selectedSquare);
    square.classList.toggle("legal-target", selectedSquare && legalTargets.has(squareName));
  });
}

function clearSelection() {
  selectedSquare = null;
  legalMoves = [];
  selectedMoveElement.textContent = "None";
  hidePromotionPicker();
  highlightSelected();
}

function selectSquare(square) {
  selectedSquare = square;
  selectedMoveElement.textContent = square;
  legalMoves = boardState?.moves?.filter((move) => move.startsWith(square)) || [];
  hidePromotionPicker();
  highlightSelected();
}

function onSquareClick(event) {
  const square = event.currentTarget.dataset.square;
  if (!selectedSquare) {
    selectSquare(square);
    return;
  }

  if (square === selectedSquare) {
    clearSelection();
    return;
  }

  const matching = legalMoves.filter((move) => move.startsWith(`${selectedSquare}${square}`));
  if (!matching.length) {
    selectSquare(square);
    return;
  }

  if (matching.length === 1) {
    sendMove(matching[0]);
    clearSelection();
    return;
  }

  promotionMovePrefix = `${selectedSquare}${square}`;
  showPromotionPicker();
}

async function sendMove(move) {
  try {
    const response = await fetch("/api/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ move }),
    });

    if (!response.ok) {
      const error = await response.json();
      console.warn("Illegal move or server issue:", error.error || response.statusText, error.details || "");
      setLog(`Illegal move or server issue: ${error.error || response.statusText}${error.details ? ' - ' + error.details : ''}`, "warn");
      return;
    }

    const data = await response.json();
    boardState = data;
    renderBoard(data.fen);
    clearSelection();
    if (data.ai_move) {
      lastAiMoveElement.textContent = data.ai_move;
      setLog(`Player: ${move}, AI: ${data.ai_move}`);
    } else {
      setLog(`Player: ${move}`);
    }

    updateStatus(data.is_game_over ? `Game over: ${data.result || "ended"}` : `Your turn (${data.turn})`);
    recordedMovesElement.textContent = (parseInt(recordedMovesElement.textContent) + 1) || 1;
    
    // Show "Learn from Win" button if game ended with a winner
    if (data.can_learn_from_win) {
      document.getElementById("learnFromWinButton").style.display = "inline-block";
      setLog(data.learning_message);
    } else if (data.is_game_over) {
      document.getElementById("learnFromWinButton").style.display = "none";
    }
  } catch (error) {
    console.error("Failed to send move:", error);
    setLog(`Network error: ${error.message}`);
    updateStatus("Connection error");
  }
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    boardState = data;
    renderBoard(data.fen);
    clearSelection();
    updateStatus(data.is_game_over ? `Game over: ${data.result || "ended"}` : `Your turn (${data.turn})`);
    recordedMovesElement.textContent = data.recorded_moves || 0;
    lastAiMoveElement.textContent = "None";
  } catch (error) {
    console.error("Failed to load status:", error);
    updateStatus("Error loading game status");
  }
}

newGameButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/new_game", { method: "POST" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    boardState = data;
    renderBoard(data.fen);
    clearSelection();
    updateStatus("Your turn (white)");
    recordedMovesElement.textContent = 0;
    lastAiMoveElement.textContent = "None";
    document.getElementById("learnFromWinButton").style.display = "none";
    setLog("Started a new game.");
  } catch (error) {
    console.error("Failed to start new game:", error);
    setLog(`Failed to start new game: ${error.message}`);
  }
});

trainButton.addEventListener("click", async () => {
  trainButton.disabled = true;
  trainButton.textContent = "Training...";
  try {
    const response = await fetch("/api/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "random", games: 120, epochs: 2 }),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const result = await response.json();
    setLog(`Training complete: ${result.message}`);
  } catch (error) {
    console.error("Training failed:", error);
    setLog(`Training failed: ${error.message}`);
  } finally {
    trainButton.textContent = "Train AI (Random)";
    trainButton.disabled = false;
  }
});

trainPlayerButton.addEventListener("click", async () => {
  trainPlayerButton.disabled = true;
  trainPlayerButton.textContent = "Training from moves...";
  try {
    const response = await fetch("/api/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "player", epochs: 3 }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    const result = await response.json();
    setLog(`Training complete: ${result.message}`);
  } catch (error) {
    console.error("Training failed:", error);
    setLog(`Training failed: ${error.message}`);
  } finally {
    trainPlayerButton.textContent = "Train from Moves";
    trainPlayerButton.disabled = false;
  }
});

document.getElementById("promotionPicker").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-piece]");
  if (!button || !promotionMovePrefix) {
    return;
  }
  const promotionPiece = button.dataset.piece;
  console.info(`Promotion selected: ${promotionMovePrefix}${promotionPiece}`);
  const fullMove = `${promotionMovePrefix}${promotionPiece}`;
  hidePromotionPicker();
  sendMove(fullMove);
  clearSelection();
});

document.getElementById("cancelPromotionButton").addEventListener("click", () => {
  hidePromotionPicker();
  clearSelection();
});

document.getElementById("learnFromWinButton").addEventListener("click", async () => {
  const learnButton = document.getElementById("learnFromWinButton");
  learnButton.disabled = true;
  learnButton.textContent = "Learning from win...";
  try {
    const response = await fetch("/api/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "winning", epochs: 3 }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    const result = await response.json();
    setLog(`AI reinforced! Trained on ${result.data_pairs} winning moves for ${result.epochs} epochs.`);
    learnButton.style.display = "none";
  } catch (error) {
    console.error("Learning failed:", error);
    setLog(`Learning failed: ${error.message}`);
  } finally {
    learnButton.textContent = "Learn from Win";
    learnButton.disabled = false;
  }
});

loadStatus();
