# Tic-Tac-Toe Game

# Initialize the game board
board = [' ' for _ in range(9)]

# Function to print the board
def print_board():
    print("\n")
    for row in [board[i:i + 3] for i in range(0, 9, 3)]:
        print(" | ".join(row))
        print("-" * 5)

# Check for a winner
def check_winner(player):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    return any(all(board[pos] == player for pos in condition) for condition in win_conditions)

# Check for a draw
def check_draw():
    return all(space != ' ' for space in board)

# Main game loop
def play_game():
    current_player = 'X'
    while True:
        print_board()
        try:
            move = int(input(f"Player {current_player}, enter your move (1-9): ")) - 1
            if move < 0 or move >= 9 or board[move] != ' ':
                print("Invalid move. Try again.")
                continue
            board[move] = current_player
            if check_winner(current_player):
                print_board()
                print(f"Player {current_player} wins!")
                break
            if check_draw():
                print_board()
                print("It's a draw!")
                break
            current_player = 'O' if current_player == 'X' else 'X'
        except ValueError:
            print("Please enter a valid number between 1 and 9.")

# Run the game
if __name__ == "__main__":
    play_game()
