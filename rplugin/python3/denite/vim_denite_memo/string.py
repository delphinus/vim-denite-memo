from typing import Dict
from platform import system
from unicodedata import east_asian_width, normalize

EAST_ASIAN_WIDTH: Dict[str, str] = {}


def stdwidthpart(string: str, col: int, ambiwidth: str) -> str:
    # normalize string for filenames in macOS
    target = normalize("NFC", string) if system() == "Darwin" else string
    char_lengths = [(x, _char_width(x, ambiwidth)) for x in target]
    sum_len = sum(x for (_, x) in char_lengths)
    if sum_len < col:
        return target + " " * (col - sum_len)
    result = ""
    result_len = 0
    for (char, length) in char_lengths:
        next_result = result + char
        next_len = result_len + length
        if next_len > col - 3:
            return result + ("...." if result_len < col - 3 else "...")
        elif next_len == col - 3:
            return next_result + "..."
        result = next_result
        result_len = next_len
    return ""


def _char_width(char: str, ambiwidth: str) -> int:
    """
    this func returns 2 if it is Zenkaku string, 1 if other.  Each type, 'F',
    'W', 'A', means below.

    * F -- Fullwidth
    * W -- Wide
    * A -- Ambiguous
    """
    if char not in EAST_ASIAN_WIDTH:
        EAST_ASIAN_WIDTH[char] = east_asian_width(char)
    to_double = "FW" if ambiwidth == "single" else "FWA"
    return 2 if EAST_ASIAN_WIDTH[char] in to_double else 1
