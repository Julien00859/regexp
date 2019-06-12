from .automatons import DCMA, DCA, DA, NDA

def compile(pattern):
    automaton = NDA.from_pattern(pattern)
    try:
        automaton = DA.from_nda(automaton)
        automaton = DCA.from_da(automaton)
        automaton = DCMA.from_dca(automaton)
    except NotImplementedError:
        pass
    return automaton
