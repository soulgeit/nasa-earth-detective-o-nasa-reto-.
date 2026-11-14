# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Spanish/English text normalisation shared by BM25, the rules planner and the guard.

Only linguistic processing lives here: no scientific content, no numbers, no facts.
"""

from __future__ import annotations

import re
import unicodedata

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Words that carry no retrieval signal. Kept short on purpose: BM25 works better
# with a small stop list than with an aggressive one, especially for short queries.
STOPWORDS_ES = frozenset(
    """
    a al algo algun alguna algunas alguno algunos ante antes como con contra cual
    cuales cuando de del desde donde dos el ella ellas ellos en entre era erais
    eran eras eres es esa esas ese eso esos esta estan estan estar estas este esto
    estos fue fueron ha habia han has hasta hay la las le les lo los mas me mi
    mis mucho muy nada ni no nos o os para pero poco por porque que quien se sea
    segun ser si sin sobre son su sus tambien tan tanto te tiene tienen todo todos
    tu tus un una uno unos y ya yo
    """.split()
)

STOPWORDS_EN = frozenset(
    """
    a about after all also am an and any are as at be because been before being
    between both but by can could did do does doing during each few for from had
    has have having he her here her him his how i if in into is it its itself
    just me more most my no nor not now of off on once only or other our out over
    own same she should so some such than that the their them then there these
    they this those through to too under until up very was we were what when where
    which while who whom why will with would you your
    """.split()
)

STOPWORDS = STOPWORDS_ES | STOPWORDS_EN


def strip_accents(text: str) -> str:
    """Remove diacritics: 'Piúra' -> 'Piura' (NFKD, dropping combining marks)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def fold(text: str) -> str:
    """Lowercase + accent-free + ß/æ folds. Used for every comparison."""
    text = strip_accents(text).lower()
    return text.replace("ñ", "n").replace("ß", "ss")


def tokenize(text: str, *, drop_stopwords: bool = True) -> list[str]:
    tokens = _TOKEN_RE.findall(fold(text))
    if drop_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens


def light_stem(token: str) -> str:
    """Very conservative es/en folding for retrieval.

    We deliberately do NOT do real stemming ('lluvia'/'llover' must stay apart),
    only inflection endings that are unambiguous in both languages:
    'getting'->'gett' matches 'gets', 'hotter'->'hott', 'calientes'->'calient'.
    """
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 5 and token.endswith("est"):
        return token[:-2]
    if len(token) > 5 and token.endswith("es"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


# Irregular forms a fold cannot reach; kept tiny on purpose.
IRREGULAR = {
    "hotter": "hot", "hottest": "hot", "warmer": "warm", "warmest": "warm",
    "wetter": "wet", "wettest": "wet", "drier": "dry", "driest": "dry",
    "worse": "bad", "better": "good", "calentando": "calentar", "secando": "secar",
    "lloviendo": "llover", "llovio": "llover", "llueve": "llover", "llueven": "llover",
}


def normalize_terms(text: str) -> list[str]:
    return [IRREGULAR.get(t, light_stem(t)) for t in tokenize(text)]


def detect_language(text: str) -> str:
    """Best-effort es/en detector used by the guard (contracts: lang in es|en)."""
    folded = " " + fold(text) + " "
    es_words = ("de", "la", "el", "que", "en", "los", "las", "es", "y", "por", "con", "del", "al", "se", "su")
    en_words = ("the", "of", "and", "is", "in", "to", "that", "for", "with", "are", "this", "it",
                "was", "on", "as", "at", "by", "be", "not", "there")
    es_hits = sum(folded.count(" " + w + " ") for w in es_words)
    en_hits = sum(folded.count(" " + w + " ") for w in en_words)
    # Accented characters, ñ and Spanish opening marks are strong Spanish markers.
    if any(ch in text.lower() for ch in "áéíóúñ¿¡"):
        es_hits += 3
    if es_hits == en_hits:
        # Short queries often contain no stop word at all; fall back to shape.
        return "en" if re.search(r"\b(is|are|what|how|does|the|getting|hotter|less|more)\b", folded) else "es"
    return "es" if es_hits > en_hits else "en"
