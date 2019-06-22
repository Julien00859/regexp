from .automatons import DCMFA

def compile(pattern, flags=0):
    return DCMFA.from_pattern(pattern, flags)
