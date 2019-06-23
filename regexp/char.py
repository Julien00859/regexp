from typing import NewType, Union

SigmaType = NewType("SigmaType", object)
SIGMA = SigmaType(object())
Character = NewType("Character", Union[str, SigmaType])

def char_to_str(char: Character) -> str:
    return {SIGMA: "Σ", "": "ε"}.get(char, char)
