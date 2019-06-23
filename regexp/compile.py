from .automatons import DCMFA

def compile(pattern: str, flags:int=0) -> DCMFA:
    """Compile the pattern into the most efficient automaton"""
    return DCMFA.from_pattern(pattern, flags)
