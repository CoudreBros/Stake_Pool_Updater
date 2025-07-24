import subprocess
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator

def clear_terminal():
    """Clear the terminal screen."""
    subprocess.run(["clear"])

def ask_user_to_continue(question):
    """Prompt user with a yes/no question using prompt_toolkit."""
    validator = Validator.from_callable(
        lambda text: text.lower() in ["y", "n"],
        error_message="Please enter y or n.",
        move_cursor_to_end=True,
    )
    answer = prompt(f"{question} (y/n): ", validator=validator).strip().lower()
    return answer == "y"

def print_header(title: str):
    width = 50
    border = "=" * width
    centered_title = f"{title.center(width - 2)}"

    print(border)
    print(centered_title)
    print(border)
