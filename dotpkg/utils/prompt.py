from dotpkg.options import Options
from dotpkg.utils.log import PINK_COLOR, CLEAR_COLOR

def prompt(msg: str, choices: list[str], default: str, opts: Options) -> str:
    if opts.assume_yes:
        return default

    aliases: dict[str, str] = {}
    option_strs: list[str] = []

    if choices:
        for choice in choices:
            i = 1
            while choice[:i] in aliases.keys():
                i += 1
            aliases[choice[:i]] = choice
            option_strs.append(f'[{choice[:i]}]{choice[i:]}')

    choices_str = f" - {', '.join(option_strs)}"
    response = input(f"{PINK_COLOR}==> {msg}{choices_str} {CLEAR_COLOR}")

    return aliases.get(response, response)

def confirm(msg: str, opts: Options) -> bool:
    response = prompt(msg, ['yes', 'no'], 'yes', opts)
    return response == 'yes'
