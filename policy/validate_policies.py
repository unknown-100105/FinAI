from pathlib import Path
import joblib

from policy.rules import POLICIES


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")

model = joblib.load(MODEL_PATH)

router_intents = set(
    model.named_steps["classifier"].classes_
)

policy_intents = set(POLICIES.keys())

missing = sorted(router_intents - policy_intents)
extra = sorted(policy_intents - router_intents)

print("=" * 80)
print("FinAI POLICY COVERAGE VALIDATION")
print("=" * 80)

print(f"Router intents : {len(router_intents)}")
print(f"Policy intents : {len(policy_intents)}")
print()

if missing:
    print("MISSING POLICIES:")
    for intent in missing:
        print("  -", intent)
else:
    print("MISSING POLICIES: NONE")

print()

if extra:
    print("EXTRA POLICIES:")
    for intent in extra:
        print("  -", intent)
else:
    print("EXTRA POLICIES: NONE")

print()

if not missing and not extra and len(router_intents) == 50:
    print("RESULT: PASS")
    print("All 50 router intents have policy definitions.")
else:
    print("RESULT: REVIEW REQUIRED")
