import random

def game_round(user_choice, computer_choice):
    if user_choice == computer_choice:
        return "Draw!"
    
    if (user_choice == "snake" and computer_choice == "water") or \
       (user_choice == "water" and computer_choice == "gun") or \
       (user_choice == "gun" and computer_choice == "snake"):
        return "You Win!"
    else:
        return "Computer Wins!"

def snake_water_gun():
    choices = ["snake", "water", "gun"]
    print("🎮 Welcome to Snake, Water, Gun Game 🎮")
    print("Choices: snake | water | gun")

    while True:
        user_choice = input("Enter your choice: ").strip().lower()
        if user_choice not in choices:
            print("❌ Invalid choice! Please select snake, water, or gun.")
            continue

        computer_choice = random.choice(choices)
        print(f"\nYou chose: {user_choice}")
        print(f"Computer chose: {computer_choice}")

        result = game_round(user_choice, computer_choice)
        print(f"👉 {result}\n")

        play_again = input("Do you want to play again? (yes/no): ").strip().lower()
        if play_again != "yes":
            print("Thanks for playing! 🎉")
            break

if __name__ == "__main__":
    snake_water_gun()
