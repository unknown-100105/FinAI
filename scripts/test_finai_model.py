import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

BASE_MODEL = "sarvamai/sarvam-1"
ADAPTER = "models/finai-sarvam-lora"


def main():

    print("=" * 70)
    print("FINAI FINE-TUNED MODEL TEST")
    print("=" * 70)

    print("CUDA:", torch.cuda.is_available())
    print("GPU:", torch.cuda.get_device_name(0))

    # --------------------------------------------------------
    # 4-bit configuration
    # --------------------------------------------------------

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # --------------------------------------------------------
    # Tokenizer
    # --------------------------------------------------------

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL
    )

    # --------------------------------------------------------
    # Base model
    # --------------------------------------------------------

    print("Loading base model...")

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
    )

    # --------------------------------------------------------
    # FinAI adapter
    # --------------------------------------------------------

    print("Loading FinAI adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER,
    )

    model.eval()

    print("FinAI model loaded.")

    # --------------------------------------------------------
    # Test prompts
    # --------------------------------------------------------

    prompts = {
        "English":
            "My payment is still pending. What should I do?",

        "Tamil":
            "என்னோட payment இன்னும் pendingல இருக்கு. என்ன செய்ய வேண்டும்?",

        "Telugu":
            "నా payment ఇంకా pendingలో ఉంది. నేను ఏమి చేయాలి?",

        "Kannada":
            "ನನ್ನ payment ಇನ್ನೂ pendingನಲ್ಲಿ ಇದೆ. ನಾನು ಏನು ಮಾಡಬೇಕು?",

        "Malayalam":
            "എന്റെ payment ഇപ്പോഴും pending ആണ്. ഞാൻ എന്ത് ചെയ്യണം?"
    }

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    for language, question in prompts.items():

        print("\n" + "=" * 70)
        print(language)
        print("=" * 70)

        prompt = (
            "### User:\n"
            + question
            + "\n\n"
            + "### Assistant:\n"
        )

        device = next(model.parameters()).device

        inputs = tokenizer(
            prompt,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():

            outputs = model.generate(
                **inputs,
                max_new_tokens=120,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        print(response)

    print("\n" + "=" * 70)
    print("FINAI MODEL TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()