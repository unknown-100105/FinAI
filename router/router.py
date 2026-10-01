import json
from pathlib import Path

import joblib


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")


class FinAIRouter:
    """
    Production-facing wrapper around the trained TF-IDF router.

    The classifier predicts one of the known 50 intents.
    A confidence/margin gate can instead return UNKNOWN when
    the prediction is not sufficiently reliable.
    """

    def __init__(
        self,
        model_path=MODEL_PATH,
        confidence_threshold=0.70,
        margin_threshold=0.15,
    ):
        self.model = joblib.load(model_path)

        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold

        self.classes = list(
            self.model.named_steps["classifier"].classes_
        )

    def route(self, text):
        text = str(text).strip()

        if not text:
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "margin": 0.0,
                "accepted": False,
                "top_k": [],
                "reason": "empty_input",
            }

        probabilities = self.model.predict_proba([text])[0]

        ranked = sorted(
            zip(self.classes, probabilities),
            key=lambda x: x[1],
            reverse=True,
        )

        top_k = [
            {
                "intent": intent,
                "confidence": float(prob),
            }
            for intent, prob in ranked[:5]
        ]

        top1_intent = ranked[0][0]
        top1_conf = float(ranked[0][1])
        top2_conf = float(ranked[1][1]) if len(ranked) > 1 else 0.0

        margin = top1_conf - top2_conf

        accepted = (
            top1_conf >= self.confidence_threshold
            and margin >= self.margin_threshold
        )

        if accepted:
            final_intent = top1_intent
            reason = "accepted"
        else:
            final_intent = "UNKNOWN"

            if top1_conf < self.confidence_threshold:
                reason = "low_confidence"
            else:
                reason = "low_margin"

        return {
            "intent": final_intent,
            "raw_prediction": top1_intent,
            "confidence": top1_conf,
            "margin": margin,
            "accepted": accepted,
            "top_k": top_k,
            "reason": reason,
        }


if __name__ == "__main__":
    router = FinAIRouter()

    tests = [
        "My card is lost",
        "Someone stole my card",
        "My UPI payment failed",
        "My payment is still pending",
        "How much is my account balance?",
        "Tell me about cricket",
        "What is the weather today?",
        "asdfghjkl",
    ]

    print("=" * 70)
    print("FinAI ROUTER CONFIDENCE TEST")
    print("=" * 70)

    for text in tests:
        result = router.route(text)

        print()
        print("USER:", text)
        print("INTENT:", result["intent"])
        print("RAW:", result["raw_prediction"])
        print("CONFIDENCE:", f"{result['confidence']:.4f}")
        print("MARGIN:", f"{result['margin']:.4f}")
        print("ACCEPTED:", result["accepted"])
        print("REASON:", result["reason"])

        print("TOP-3:")
        for item in result["top_k"][:3]:
            print(
                f"  {item['intent']:35s}"
                f" {item['confidence']:.4f}"
            )
