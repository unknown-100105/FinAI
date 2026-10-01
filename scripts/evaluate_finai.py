import json
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

OUTPUT_FILE = Path("evaluation/unseen_results.json")


TEST_CASES = [
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
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
    )

    model = PeftModel.from_pretrained(
        model,
        ADAPTER,
    )

    model.eval()

    return tokenizer, model


def generate(tokenizer, model, text):
    prompt = (
        "### User:\n"
        f"{text}\n\n"
        "### Assistant:\n"
    )

    device = next(model.parameters()).device

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.decode(
        outputs[0],
        skip_special_tokens=True,
    )


def main():
    print("=" * 70)
    print("FINAI UNSEEN EVALUATION")
    print("=" * 70)

    tokenizer, model = load_model()

    results = []

    for index, case in enumerate(TEST_CASES, start=1):

        print("\n" + "-" * 70)
        print(f"TEST {index}/{len(TEST_CASES)}")
        print("Language:", case["language"])
        print("Expected:", case["expected_intent"])
        print("Input:", case["text"])

        output = generate(
            tokenizer,
            model,
            case["text"]
        )

        print("\nMODEL OUTPUT:")
        print(output)

        results.append({
            **case,
            "model_output": output,
        })

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 70)
    print("UNSEEN EVALUATION COMPLETE")
    print("Results saved to:", OUTPUT_FILE)
    print("=" * 70)


if __name__ == "__main__":
    main()