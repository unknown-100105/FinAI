import json
import re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

BASE_MODEL = "sarvamai/sarvam-1"
ADAPTER = "models/finai-sarvam-lora"

OUTPUT_FILE = Path("evaluation/unseen_results_v2.json")


TEST_CASES = [
    # English
    {
        "language": "en",
        "expected_intent": "MERCHANT_NOT_CREDITED",
        "text": "The money was deducted from my account but the shopkeeper did not receive it."
    },
    {
        "language": "en",
        "expected_intent": "UNKNOWN_TRANSACTION",
        "text": "I see a transaction in my account that I do not recognize."
    },
    {
        "language": "en",
        "expected_intent": "CARD_LOST",
        "text": "I lost my debit card and need to secure it."
    },
    {
        "language": "en",
        "expected_intent": "KYC_STATUS",
        "text": "How can I check whether my KYC verification is complete?"
    },

    # Tamil
    {
        "language": "ta",
        "expected_intent": "MERCHANT_NOT_CREDITED",
        "text": "என் கணக்கிலிருந்து பணம் கழிந்துவிட்டது ஆனால் கடைக்காரருக்கு பணம் வரவில்லை."
    },
    {
        "language": "ta",
        "expected_intent": "UNKNOWN_TRANSACTION",
        "text": "எனக்கு தெரியாத ஒரு பரிவர்த்தனை என் கணக்கில் இருக்கிறது."
    },
    {
        "language": "ta",
        "expected_intent": "CARD_LOST",
        "text": "எனது டெபிட் கார்டை தொலைத்துவிட்டேன், அதை பாதுகாக்க வேண்டும்."
    },
    {
        "language": "ta",
        "expected_intent": "KYC_STATUS",
        "text": "எனது KYC சரிபார்ப்பு முடிந்ததா என்பதை எப்படி தெரிந்து கொள்வது?"
    },

    # Telugu
    {
        "language": "te",
        "expected_intent": "MERCHANT_NOT_CREDITED",
        "text": "నా ఖాతా నుంచి డబ్బు కట్ అయింది కానీ షాపుదారుడికి డబ్బు అందలేదు."
    },
    {
        "language": "te",
        "expected_intent": "UNKNOWN_TRANSACTION",
        "text": "నాకు తెలియని ఒక లావాదేవీ నా ఖాతాలో కనిపిస్తోంది."
    },
    {
        "language": "te",
        "expected_intent": "CARD_LOST",
        "text": "నా డెబిట్ కార్డు పోయింది, దాన్ని సురక్షితం చేయాలి."
    },
    {
        "language": "te",
        "expected_intent": "KYC_STATUS",
        "text": "నా KYC వెరిఫికేషన్ పూర్తయిందో లేదో ఎలా తెలుసుకోవాలి?"
    },

    # Kannada
    {
        "language": "kn",
        "expected_intent": "MERCHANT_NOT_CREDITED",
        "text": "ನನ್ನ ಖಾತೆಯಿಂದ ಹಣ ಕಡಿತವಾಗಿದೆ ಆದರೆ ಅಂಗಡಿಕಾರರಿಗೆ ಹಣ ಬಂದಿಲ್ಲ."
    },
    {
        "language": "kn",
        "expected_intent": "UNKNOWN_TRANSACTION",
        "text": "ನನ್ನ ಖಾತೆಯಲ್ಲಿ ನನಗೆ ತಿಳಿಯದ ಒಂದು ವಹಿವಾಟು ಕಾಣಿಸುತ್ತಿದೆ."
    },
    {
        "language": "kn",
        "expected_intent": "CARD_LOST",
        "text": "ನನ್ನ ಡೆಬಿಟ್ ಕಾರ್ಡ್ ಕಳೆದುಹೋಗಿದೆ, ಅದನ್ನು ಸುರಕ್ಷಿತಗೊಳಿಸಬೇಕು."
    },
    {
        "language": "kn",
        "expected_intent": "KYC_STATUS",
        "text": "ನನ್ನ KYC ಪರಿಶೀಲನೆ ಪೂರ್ಣಗೊಂಡಿದೆಯೇ ಎಂದು ಹೇಗೆ ತಿಳಿಯುವುದು?"
    },

    # Malayalam
    {
        "language": "ml",
        "expected_intent": "MERCHANT_NOT_CREDITED",
        "text": "എന്റെ അക്കൗണ്ടിൽ നിന്ന് പണം പോയി, പക്ഷേ കടക്കാരന് പണം ലഭിച്ചിട്ടില്ല."
    },
    {
        "language": "ml",
        "expected_intent": "UNKNOWN_TRANSACTION",
        "text": "എന്റെ അക്കൗണ്ടിൽ എനിക്ക് പരിചയമില്ലാത്ത ഒരു ഇടപാട് കാണുന്നു."
    },
    {
        "language": "ml",
        "expected_intent": "CARD_LOST",
        "text": "എന്റെ ഡെബിറ്റ് കാർഡ് നഷ്ടപ്പെട്ടു, അത് സുരക്ഷിതമാക്കണം."
    },
    {
        "language": "ml",
        "expected_intent": "KYC_STATUS",
        "text": "എന്റെ KYC പരിശോധന പൂർത്തിയായോ എന്ന് എങ്ങനെ പരിശോധിക്കാം?"
    },
]


def load_model():
    config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=config,
        device_map="auto",
    )

    model = PeftModel.from_pretrained(
        model,
        ADAPTER,
    )

    model.eval()

    return tokenizer, model


def extract_intent(text):
    match = re.search(
        r"\bINTENT:\s*([A-Z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip().upper()

    return None


def generate_response(tokenizer, model, question):
    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]

    device = next(model.parameters()).device

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    input_length = inputs["input_ids"].shape[-1]

    generated = outputs[
        0,
        input_length:
    ]

    return tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )


def main():
    print("=" * 70)
    print("FINAI CORRECTED UNSEEN EVALUATION")
    print("=" * 70)

    tokenizer, model = load_model()

    results = []

    correct = 0

    for index, case in enumerate(TEST_CASES, start=1):

        print("\n" + "-" * 70)
        print(f"TEST {index}/{len(TEST_CASES)}")
        print("Language :", case["language"])
        print("Expected :", case["expected_intent"])
        print("Question :", case["text"])

        output = generate_response(
            tokenizer,
            model,
            case["text"],
        )

        predicted = extract_intent(output)

        is_correct = predicted == case["expected_intent"]

        if is_correct:
            correct += 1

        print("Predicted :", predicted)
        print("Correct   :", is_correct)

        print("\nModel output:")
        print(output)

        results.append({
            **case,
            "predicted_intent": predicted,
            "correct": is_correct,
            "model_output": output,
        })

    accuracy = correct / len(TEST_CASES) * 100

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print(
        f"INTENT ACCURACY: "
        f"{correct}/{len(TEST_CASES)} = {accuracy:.1f}%"
    )
    print("=" * 70)

    print(
        "Results saved to:",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()