import re
from typing import Any, Dict, Iterable, List, Set


class RAGEvidenceVerifier:
    """Deterministic lexical verifier for retrieval-grounded responses.

    The verifier treats retrieved documents as the only authority. It does
    not call an LLM and does not attempt to prove factual correctness beyond
    overlap with the supplied evidence.
    """

    DEFAULT_OVERLAP_THRESHOLD = 0.35
    MIN_CONTENT_TOKENS = 2

    STOPWORDS: Set[str] = {
        "a", "an", "and", "are", "as", "at", "be", "been", "being",
        "but", "by", "can", "could", "did", "do", "does", "for",
        "from", "had", "has", "have", "how", "if", "in", "into",
        "is", "it", "its", "may", "might", "more", "of", "on",
        "or", "our", "should", "that", "the", "their", "them",
        "these", "this", "those", "to", "under", "was", "were",
        "what", "when", "where", "which", "who", "will", "with",
        "would", "you", "your",
    }

    @classmethod
    def _tokens(cls, text: Any) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", str(text).lower())
        return [
            token
            for token in tokens
            if token not in cls.STOPWORDS
        ]

    @classmethod
    def _sentences(cls, response: str) -> Iterable[str]:
        cleaned = re.sub(r"\s+", " ", str(response)).strip()
        if not cleaned:
            return []

        parts = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
        sentences = []

        for part in parts:
            sentence = re.sub(
                r"^\s*(?:[-*•]|\d+[.)])\s*",
                "",
                part,
            ).strip()

            if sentence:
                sentences.append(sentence)

        return sentences

    @classmethod
    def _document_tokens(cls, documents: Iterable[Dict[str, Any]]) -> List[Set[str]]:
        token_sets = []

        for document in documents or []:
            if not isinstance(document, dict):
                continue

            text = " ".join(
                str(document.get(field, "") or "")
                for field in ("title", "text")
            )

            tokens = set(cls._tokens(text))

            if tokens:
                token_sets.append(tokens)

        return token_sets

    @classmethod
    def _best_overlap(
        cls,
        claim_tokens: Set[str],
        document_tokens: List[Set[str]],
    ) -> float:
        if not claim_tokens or not document_tokens:
            return 0.0

        return max(
            len(claim_tokens.intersection(tokens))
            / len(claim_tokens)
            for tokens in document_tokens
        )

    @classmethod
    def verify(
        cls,
        response: str,
        documents: Iterable[Dict[str, Any]],
        threshold: float = DEFAULT_OVERLAP_THRESHOLD,
    ) -> Dict[str, Any]:
        documents = list(documents or [])
        evidence_tokens = cls._document_tokens(documents)

        if not documents or not evidence_tokens:
            return {
                "applicable": True,
                "passed": False,
                "mode": "EVIDENCE_SUPPORT",
                "evidence_count": len(documents),
                "supported_claims": [],
                "unsupported_claims": [
                    {
                        "claim": str(response).strip(),
                        "reason": "No usable retrieved evidence was supplied.",
                    }
                ],
            }

        supported = []
        unsupported = []

        for sentence in cls._sentences(response):
            tokens = set(cls._tokens(sentence))

            # Very short connective/formatting fragments are not treated as
            # substantive factual claims.
            if len(tokens) < cls.MIN_CONTENT_TOKENS:
                continue

            overlap = cls._best_overlap(tokens, evidence_tokens)
            item = {
                "claim": sentence,
                "overlap": round(overlap, 4),
            }

            if overlap >= threshold:
                supported.append(item)
            else:
                unsupported.append({
                    **item,
                    "reason": "Insufficient lexical support in retrieved evidence.",
                })

        # An answer with no substantive sentences is not considered grounded.
        passed = bool(supported) and not unsupported

        return {
            "applicable": True,
            "passed": passed,
            "mode": "EVIDENCE_SUPPORT",
            "evidence_count": len(documents),
            "supported_claims": supported,
            "unsupported_claims": unsupported,
        }


if __name__ == "__main__":
    documents = [
        {
            "title": "KYC evidence",
            "text": (
                "KYC may require PAN card, address proof, photograph, "
                "cancelled cheque, and signatures."
            ),
        }
    ]

    print(
        RAGEvidenceVerifier.verify(
            "KYC may require a PAN card and address proof.",
            documents,
        )
    )
