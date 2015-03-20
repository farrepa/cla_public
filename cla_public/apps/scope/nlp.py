# -*- coding: utf-8 -*-
"Scope diagnosis NLP routines"

from stemming.porter2 import stem
from topia.termextract import extract

from norvig_spelling import correct


class DiagnosisError(Exception):
    pass


def guess_category(text):

    extractor = extract.TermExtractor()
    terms = sorted(extractor(text))

    def clean(*args):
        term, count, strength = args[0]
        return (
            " ".join(map(lambda word: stem(correct(word)), term.split())),
            count, strength)

    terms = map(clean, terms)



    return terms
