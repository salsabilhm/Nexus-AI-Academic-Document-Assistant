"""Embedding model: Text -> Embedding.

Sole responsibility::

    text -> list[float]   (fixed-size, L2-normalized vector)

Independent by design: this module knows nothing about Django, the Agent,
the vector store or HTTP — only strings and numbers. It can be unit-tested
alone and swapped for a real model (OpenAI embeddings, sentence-transformers,
...) later by implementing the same ``embed`` / ``embed_batch`` methods:
nothing else in chatbot/rag changes.

Implementation — deterministic feature hashing
----------------------------------------------
1. normalize: NFKD accent folding + lowercase ("mémoire" == "memoire");
2. tokenize on [a-z0-9]+ and drop a small English/French stopword list;
3. build unigram + bigram features (bigrams keep expressions like
   "chapter 3" discriminative);
4. hash each feature with blake2b into one of ``dimension`` buckets, with a
   signed hash to cancel collisions (never Python's ``hash()``: it is
   randomized per process and the vectors are persisted — a query embedded
   in a later process must land in the same space as the indexed chunks);
5. weight by sublinear term frequency (1 + ln count) and L2-normalize.

No API key, no dependency, byte-identical output everywhere. Quality is
lexical (keyword-level), not semantic — an honest MVP trade-off while
``EMBEDDING_API_KEY`` is empty; replacing this class with an API-backed
embedder later is the documented upgrade path.

``DEFAULT_DIMENSION`` must match ``DocumentVector.embedding``
(pgvector ``VectorField(dimensions=384)``): changing it requires a
migration and a full re-index of every document.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable

# Must stay in sync with chatbot.models.DocumentVector (vector(384)).
DEFAULT_DIMENSION = 384

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Minimal bilingual (EN/FR) stopword list: hashing is bag-of-words, so
# frequent glue words would otherwise dominate every chunk's vector.
_STOPWORDS = frozenset(
    {
        # English
        "a", "about", "above", "after", "again", "against", "all", "also",
        "am", "an", "and", "any", "are", "as", "at", "be", "because", "been",
        "before", "being", "below", "between", "both", "but", "by", "can",
        "could", "did", "do", "does", "doing", "down", "during", "each",
        "few", "for", "from", "further", "had", "has", "have", "having", "he",
        "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
        "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more",
        "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
        "once", "only", "or", "other", "our", "ours", "ourselves", "out",
        "over", "own", "same", "she", "should", "so", "some", "such", "than",
        "that", "the", "their", "theirs", "them", "themselves", "then", "there",
        "these", "they", "this", "those", "through", "to", "too", "under",
        "until", "up", "very", "was", "we", "were", "what", "when", "where",
        "which", "while", "who", "whom", "why", "will", "with", "would", "you",
        "your", "yours", "yourself", "yourselves",
        # French
        "au", "aux", "avec", "ce", "ces", "comme", "dans", "de", "des", "du",
        "elle", "en", "est", "et", "etre", "ils", "la", "le", "les", "leur",
        "leurs", "lui", "mais", "me", "meme", "mes", "moi", "mon", "ne",
        "nos", "notre", "nous", "on", "ou", "par", "pas", "pour", "qu",
        "que", "qui", "sa", "se", "ses", "son", "sur", "tous", "tout", "toute",
        "toutes", "tu", "un", "une", "vos", "votre", "vous", "dans", "plus",
        "ainsi", "alors", "apres", "avant", "bien", "car", "chez", "donc",
        "entre", "encore", "jamais", "toujours", "vers",
    }
)


def _normalize(text: str) -> str:
    """Lowercase and strip accents so accented/unaccented spellings match."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def _features(text: str) -> Counter:
    """Counter of unigram + bigram features for one text."""
    tokens = [t for t in _TOKEN_RE.findall(_normalize(text)) if t not in _STOPWORDS]
    features: Counter = Counter(tokens)
    features.update(f"{a}\x00{b}" for a, b in zip(tokens, tokens[1:]))
    return features


class Embedder:
    """Deterministic local embedding model (see the module docstring)."""

    def __init__(self, dimension: int = DEFAULT_DIMENSION) -> None:
        if dimension < 8:
            raise ValueError(f"dimension must be >= 8, got {dimension}")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Embed one text into a fixed-size, L2-normalized vector.

        An empty (or stopword-only) text yields the zero vector; callers
        that must not query/store with it check ``any(vector)``.
        """
        vector = [0.0] * self._dimension
        for feature, count in _features(text).items():
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign * (1.0 + math.log(count))

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]

    def embed_batch(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed several texts (same output as calling ``embed`` one by one)."""
        return [self.embed(text) for text in texts]
