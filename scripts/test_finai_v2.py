import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


BASE_MODEL = "sarvamai/sarvam-1"

ADAPTER_PATH = (
    ROOT / "models" / "finai-v2-lora"
)


TESTS = [
    (
        "English",
        "My UPI payment is still pending. What should I do?",
    ),
    (
        "Tamil",
        "என் UPI பணப்பரிவர்த்தனை இன்னும் நிலுவையில் உள்ளது. நான் என்ன செய்ய வேண்டும்?",
    ),
    (
        "Telugu",
        "నా UPI చెల్లింపు ఇంకా పెండింగ్‌లో ఉంది. నేను ఏమి చేయాలి?",
    ),
    (
        "Kannada",
        "ನನ್ನ UPI ಪಾವತಿ ಇನ್ನೂ ಬಾಕಿಯಿದೆ. ನಾನು ಏನು ಮಾಡಬೇಕು?",
    ),
    (
        "Malayalam",
        "എന്റെ UPI പേയ്മെന്റ് ഇപ്പോഴും പെൻഡിംഗ് ആണ്. ഞാൻ എന്ത് ചെയ്യണം?",
    ),
]


def main():

    print("=" * 70)
    print("FINAI-v2 TRAINING-FORMAT TEST")
    print("=" * 70)

    print("GPU:", torch.cuda.get_device_name(0))

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        str(ADAPTER_PATH)
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizer loaded.")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("\nLoading Sarvam-1...")

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="auto",
    )

    print("Base model loaded.")

    print("Loading FinAI-v2 adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_PATH),
    )

    model.eval()

    print("FinAI-v2 adapter loaded.")

    device = model.get_input_embeddings().weight.device

    for language, question in TESTS:

        print("\n" + "=" * 70)
        print(language)
        print("=" * 70)

        print("Question:")
        print(question)

        prompt = (
            "### User:\n"
            + question
            + "\n\n"
            + "### Assistant:\n"
        )

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        )

        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        print("\nGenerating...")

        with torch.no_grad():

            output = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=120,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        generated_tokens = output[
            0
        ][input_ids.shape[1]:]

        response = tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

        print("\nMODEL RESPONSE:")
        print(response)

    print("\n" + "=" * 70)
    print("FINAI-v2 TRAINING-FORMAT TEST COMPLETE")
    print("=" * 70)

    del model
    del base_model

    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()