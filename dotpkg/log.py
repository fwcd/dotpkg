import sys

RED_COLOR = '\033[91m'
YELLOW_COLOR = '\033[93m'
BLUE_COLOR = '\033[36m'
GRAY_COLOR = '\033[90m'
GREEN_COLOR = '\033[92m'
PINK_COLOR = '\033[95m'
CLEAR_COLOR = '\033[0m'

def message(msg: str, color: str):
    print(f'{color}==> {msg}{CLEAR_COLOR}')

def error(msg: str):
    message(msg, RED_COLOR)
    sys.exit(1)

def warn(msg: str):
    message(msg, YELLOW_COLOR)

def info(msg: str):
    message(msg, BLUE_COLOR)

def success(msg: str):
    message(msg, GREEN_COLOR)

def note(msg: str):
    print(f'{GRAY_COLOR}{msg}{CLEAR_COLOR}')
