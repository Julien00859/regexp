from .automatons import DCMFA
from .pattern import expand

def compile(pattern: str, flags:int=0) -> DCMFA:
    """Compile the pattern into the most efficient automaton"""
    return DCMFA.from_pattern(expand(pattern), flags)
