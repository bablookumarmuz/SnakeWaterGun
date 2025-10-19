import random

# Function to get the current high score from file
def get_high_score():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read())
    except:
        return None  # If file doesn’t exist or empty


# Function to save a new high score
def save_high_score(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))


def play_game():
    number = random.randint(1, 100)
    guesses = 0
    max_guesses = 10
    user_guess = None

    print("\n🎯 Welcome to The Perfect Guess Game!")
    print("I have chosen a number between 1 and 100. Can you guess it?")
    print(f"You have {max_guesses} tries to guess correctly.")

    high_score = get_high_score()
    if high_score:
        print(f"🏆 Current Best Score: {high_score} guesses")

    while guesses < max_guesses:
        try:
            user_guess = int(input(f"\nGuess {guesses + 1}: "))
            guesses += 1

            if user_guess > number:
                print("📉 Lower number please!")
            elif user_guess < number:
                print("📈 Higher number please!")
            else:
                print(f"✅ Congratulations! You guessed it in {guesses} tries.")

                # Check for high score
                if high_score is None or guesses < high_score:
                    print("🎉 New High Score! 🏆")
                    save_high_score(guesses)
                break
        except ValueError:
            print("⚠️ Please enter a valid number!")

    else:
        print(f"\n❌ Game Over! The number was {number}. Better luck next time!")


def perfect_guess():
    while True:
        play_game()
        choice = input("\n🔁 Do you want to play again? (y/n): ").lower()
        if choice != 'y':
            print("👋 Thanks for playing! Goodbye!")
            break


# Run the game
perfect_guess()
