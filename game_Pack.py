"""
name: "game_Pack"
description: "A pack of simple games for SDOS (Simple DOS Simulator)"
author: "martinP"
"""
import random
from random import randint
import time
import os
import curses

def save_score(name, score, filename="leaderboard.txt"):
    """Saves the player's name and score to the leaderboard file."""
    with open(filename, "a") as f:
        f.write(f"{name}:{score}\n")
    print("Score saved!")

def display_leaderboard(filename="leaderboard.txt"):
    """Reads and displays the leaderboard in the console after the game."""
    print("\n--- Leaderboard ---")
    if not os.path.exists(filename):
        print("No leaderboard data found.")
        return

    scores = []
    with open(filename, "r") as f:
        for line in f:
            try:
                name, score_str = line.strip().split(':')
                score = int(score_str)
                scores.append((name, score))
            except ValueError:
                continue

    sorted_scores = sorted(scores, key=lambda item: item[1], reverse=True)

    if sorted_scores:
        for i, (name, score) in enumerate(sorted_scores, 1):
            print(f"{i}. {name}: {score}")
    else:
        print("No scores found.")

def game_intro():
    os.system("cls" if os.name == "nt" else "clear")
    print("GAMES Pack 1 MENU")
    print("------------------")
    print("1. Snake")
    print("2. Text Adventure")
    print("3. Exit to DOS")
    print()

def games_menu():
    while True:
        game_intro()
        choice = input("Select a game (1-3): ").strip()

        if choice == "1":
            snake()
        elif choice == "2":
            text_adventure()
        elif choice == "3":
            print("\nReturning to DOS...")
            time.sleep(1)
            break
        else:
            print("Invalid choice.")
            time.sleep(1)

# ---------- Game 1: Snake ---------- #

def show_leaderboard_in_game(window):
    """
    Pauses the game to display the leaderboard within the curses window.
    """
    window.clear()  # Clear the game screen
    sh, sw = window.getmaxyx()  # Get screen dimensions

    window.addstr(1, sw // 2 - 8, "--- Leaderboard ---")

    filename = "leaderboard.txt"
    if not os.path.exists(filename):
        window.addstr(3, sw // 2 - 12, "No leaderboard data found.")
    else:
        scores = []
        with open(filename, "r") as f:
            for line in f:
                try:
                    name, score_str = line.strip().split(':')
                    score = int(score_str)
                    scores.append((name, score))
                except ValueError:
                    continue

        sorted_scores = sorted(scores, key=lambda item: item[1], reverse=True)

        if sorted_scores:
            # Display top scores, making sure not to go off-screen
            max_scores_to_show = min(len(sorted_scores), sh - 6)
            for i, (name, score) in enumerate(sorted_scores[:max_scores_to_show], 1):
                display_string = f"{i}. {name}: {score}"
                window.addstr(3 + i, sw // 2 - len(display_string) // 2, display_string)
        else:
            window.addstr(3, sw // 2 - 8, "No scores found.")

    window.addstr(sh - 2, sw // 2 - 12, "Press 'z' to resume game")
    window.refresh()

    # Wait until 'z' is pressed again to exit the leaderboard view
    while True:
        key = window.getch()
        if key == ord('z'):
            break

    window.clear()  # Clear the leaderboard screen before returning to the game

def snake():
    """Wrapper function to handle the snake game and its score."""
    final_score = 0

    def main(stdscr):
        nonlocal final_score
        opposite_directions = {
            curses.KEY_UP: curses.KEY_DOWN,
            curses.KEY_DOWN: curses.KEY_UP,
            curses.KEY_LEFT: curses.KEY_RIGHT,
            curses.KEY_RIGHT: curses.KEY_LEFT
        }

        curses.curs_set(0)
        sh, sw = stdscr.getmaxyx()
        w = curses.newwin(sh, sw, 0, 0)
        w.keypad(1)
        w.timeout(100)
        score = 0
        
        snake = [[sh//2, sw//4], [sh//2, sw//4-1], [sh//2, sw//4-2]]
        food = [sh//2, sw//2]
        w.addch(food[0], food[1], curses.ACS_PI)

        key = curses.KEY_RIGHT

        while True:
            w.addstr(0, 2, f"Score: {score} ")
            
            key_press = w.getch()

            if key_press == ord('z'):
                # Pause the game and show the leaderboard
                show_leaderboard_in_game(w)
                
                # After returning, redraw the entire game state to resume
                w.addch(food[0], food[1], curses.ACS_PI)
                for part in snake:
                    w.addch(part[0], part[1], curses.ACS_CKBOARD)

            elif key_press == ord('x'):
                final_score = score
                break
            # Only change direction if a valid arrow key was pressed
            elif key_press in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                 if key_press != opposite_directions.get(key):
                    key = key_press

            head = snake[0]
            new_head = head[:]

            if key == curses.KEY_UP:
                new_head[0] -= 1
            elif key == curses.KEY_DOWN:
                new_head[0] += 1
            elif key == curses.KEY_LEFT:
                new_head[1] -= 1
            elif key == curses.KEY_RIGHT:
                new_head[1] += 1

            if (new_head in snake
                or new_head[0] < 1 or new_head[0] >= sh-1
                or new_head[1] < 1 or new_head[1] >= sw-1):
                msg = f"GAME OVER! Your Score: {score}"
                w.addstr(sh//2, sw//2 - len(msg)//2, msg)
                w.refresh()
                time.sleep(2)
                final_score = score
                break

            snake.insert(0, new_head)

            if new_head == food:
                food = None
                score += 1
                while food is None:
                    nf = [randint(1, sh-2), randint(1, sw-2)]
                    food = nf if nf not in snake else None
                w.addch(food[0], food[1], curses.ACS_PI)
            else:
                tail = snake.pop()
                w.addch(tail[0], tail[1], ' ')

            w.addch(new_head[0], new_head[1], curses.ACS_CKBOARD)
            w.refresh()
            
    curses.wrapper(main)

    print(f"\nGame Over! Final score: {final_score}")
    name = input("Please enter your name for the leaderboard: ").strip()
    if name:
        save_score(name, final_score)
    else:
        print("Name cannot be empty. Score not saved.")

    display_leaderboard()
    input("\nPress Enter to return to the main menu...")

# ---------- Game 2: Text Adventure ---------- #
def text_adventure():
    os.system("cls" if os.name == "nt" else "clear")
    print("=== MINI TEXT ADVENTURE ===")
    print("You wake up in a small room. There's a door and a window.\n")

    choice = input("Do you go to the (D)oor or (W)indow? ").lower().strip()
    if choice == "d":
        print("The door creaks open... you escape to freedom!")
    elif choice == "w":
        print("You climb out the window and fall into a bush. Ouch!")
    else:
        print("You stand still... and time passes slowly.")
    input("\nPress Enter to return to menu...")

if __name__ == '__main__':
    games_menu()