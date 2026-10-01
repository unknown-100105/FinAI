from pathlib import Path
import joblib
import re


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")


# These intents are safety-sensitive and should never trigger
# an external action based only on classifier confidence.
HIGH_RISK_INTENTS = {
    "CARD_STOLEN",
    "CARD_LOST",
    "CARD_BLOCK",
    "FRAUD_REPORT",
    "ACCOUNT_COMPROMISED",
    "SUSPICIOUS_ACTIVITY",
    "DISPUTE_TRANSACTION",
    "UNKNOWN_TRANSACTION",
}


# Known confusion pairs discovered during the 1,000-example
# held-out benchmark.
CONFUSION_PAIRS = {
    frozenset(("PAYMENT_FAILED", "CARD_PAYMENT_FAILED")),
    frozenset(("PAYMENT_PENDING", "REFUND_PENDING")),
    frozenset(("BANK_TRANSFER_FAILED", "BANK_TRANSFER_PENDING")),
    frozenset(("BANK_TRANSFER_PENDING", "BANK_TRANSFER_STATUS")),
    frozenset(("CARD_UNBLOCK", "CARD_ACTIVATION")),
    frozenset(("FRAUD_REPORT", "ACCOUNT_BALANCE")),
    frozenset(("LIMIT_QUERY", "PAYMENT_SUCCESS")),
}


class FinAIRouterGate:

    def __init__(
        self,
        model_path=MODEL_PATH,
        high_confidence=0.65,
        medium_confidence=0.30,
        high_margin=0.20,
        medium_margin=0.08,
    ):
        self.model = joblib.load(model_path)

        self.high_confidence = high_confidence
        self.medium_confidence = medium_confidence

        self.high_margin = high_margin
        self.medium_margin = medium_margin

        self.classes = list(
            self.model.named_steps["classifier"].classes_
        )

    def _basic_ood(self, text):
        """
        Very lightweight safety filter.
        A real production OOD detector will be added later.
        """

        text = str(text).strip()

        if not text:
            return True, "empty_input"

        # Obviously meaningless input.
        if re.fullmatch(r"[\W_]+", text):
            return True, "non_text_input"

        if len(re.sub(r"\W", "", text)) < 3:
            return True, "too_short"

        return False, None

    def route(self, text):

        text = str(text).strip()

        is_ood, ood_reason = self._basic_ood(text)

        if is_ood:
            return {
                "intent": "UNKNOWN",
                "raw_prediction": None,
                "confidence": 0.0,
                "margin": 0.0,
                "decision": "UNKNOWN",
                "risk_level": "low",
                "requires_clarification": False,
                "reason": ood_reason,
                "top_k": [],
            }

        probabilities = self.model.predict_proba([text])[0]

        ranked = sorted(
            zip(self.classes, probabilities),
            key=lambda x: x[1],
            reverse=True,
        )

        top1_intent, top1_conf = ranked[0]
        top2_intent, top2_conf = ranked[1]

        top1_conf = float(top1_conf)
        top2_conf = float(top2_conf)

        margin = top1_conf - top2_conf

        top_k = [
            {
                "intent": intent,
                "confidence": float(probability),
            }
            for intent, probability in ranked[:5]
        ]

        pair = frozenset((top1_intent, top2_intent))

        # ---------------------------------------------------------
        # Critical ambiguity handling
        # ---------------------------------------------------------

        if pair in CONFUSION_PAIRS and margin < self.high_margin:
            return {
                "intent": "UNKNOWN",
                "raw_prediction": top1_intent,
                "confidence": top1_conf,
                "margin": margin,
                "decision": "CLARIFY",
                "risk_level": "medium",
                "requires_clarification": True,
                "reason": "known_confusion_pair",
                "top_k": top_k,
            }

        # ---------------------------------------------------------
        # High-confidence prediction
        # ---------------------------------------------------------

        if (
            top1_conf >= self.high_confidence
            and margin >= self.high_margin
        ):
            return {
                "intent": top1_intent,
                "raw_prediction": top1_intent,
                "confidence": top1_conf,
                "margin": margin,
                "decision": "ROUTE",
                "risk_level": (
                    "high"
                    if top1_intent in HIGH_RISK_INTENTS
                    else "low"
                ),
                "requires_clarification": False,
                "reason": "high_confidence",
                "top_k": top_k,
            }

        # ---------------------------------------------------------
        # Medium confidence → clarification
        # ---------------------------------------------------------

        if (
            top1_conf >= self.medium_confidence
            and margin >= self.medium_margin
        ):
            return {
                "intent": top1_intent,
                "raw_prediction": top1_intent,
                "confidence": top1_conf,
                "margin": margin,
                "decision": "CLARIFY",
                "risk_level": (
                    "high"
                    if top1_intent in HIGH_RISK_INTENTS
                    else "medium"
                ),
                "requires_clarification": True,
                "reason": "medium_confidence",
                "top_k": top_k,
            }

        # ---------------------------------------------------------
        # Low confidence → UNKNOWN
        # ---------------------------------------------------------

        return {
            "intent": "UNKNOWN",
            "raw_prediction": top1_intent,
            "confidence": top1_conf,
            "margin": margin,
            "decision": "UNKNOWN",
            "risk_level": "low",
            "requires_clarification": True,
            "reason": "low_confidence",
            "top_k": top_k,
        }


if __name__ == "__main__":

    router = FinAIRouterGate()

    tests = [
        "My card is lost",
        "Someone stole my card",
        "My UPI payment failed",
        "My payment is still pending",
        "How much is my account balance?",
        "I think someone used my account fraudulently",
        "Tell me about cricket",
        "What is the weather today?",
        "asdfghjkl",
        "The payment failed",
        "My card payment failed",
    ]

    print("=" * 80)
    print("FinAI INTELLIGENT ROUTER GATE")
    print("=" * 80)

    for text in tests:

        result = router.route(text)

        print()
        print("USER:", text)
        print("INTENT:", result["intent"])
        print("RAW:", result["raw_prediction"])
        print("CONFIDENCE:", f"{result['confidence']:.4f}")
        print("MARGIN:", f"{result['margin']:.4f}")
        print("DECISION:", result["decision"])
        print("RISK:", result["risk_level"])
        print("CLARIFICATION:", result["requires_clarification"])
        print("REASON:", result["reason"])

        print("TOP-3:")
        for item in result["top_k"][:3]:
            print(
                f"  {item['intent']:35s}"
                f" {item['confidence']:.4f}"
            )
