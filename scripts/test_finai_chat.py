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
    print("FINAI CHAT TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Check GPU
    # --------------------------------------------------------

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available.")

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
    # Test questions
    # --------------------------------------------------------

    questions = [
        (
            "English",
            "The money was deducted from my account but the shopkeeper did not receive it."
        ),
        (
            "Tamil",
            "என் கணக்கிலிருந்து பணம் கழிந்துவிட்டது ஆனால் கடைக்காரருக்கு பணம் வரவில்லை."
        ),
        (
            "Telugu",
            "నా ఖాతా నుంచి డబ్బు కట్ అయింది కానీ షాపుదారుడికి డబ్బు అందలేదు."
        ),
        (
            "Kannada",
            "ನನ್ನ ಖಾತೆಯಿಂದ ಹಣ ಕಡಿತವಾಗಿದೆ ಆದರೆ ಅಂಗಡಿಕಾರರಿಗೆ ಹಣ ಬಂದಿಲ್ಲ."
        ),
        (
            "Malayalam",
            "എന്റെ അക്കൗണ്ടിൽ നിന്ന് പണം പോയി, പക്ഷേ കടക്കാരന് പണം ലഭിച്ചിട്ടില്ല."
        ),
    ]

    # --------------------------------------------------------
    # Generate responses
    # --------------------------------------------------------

    for language, question in questions:

        print("\n" + "=" * 70)
        print(language)
        print("=" * 70)

        print("Question:")
        print(question)

        messages = [
            {
                "role": "user",
                "content": question,
            }
        ]

        device = next(model.parameters()).device

        # Use Sarvam's actual chat template.
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )

        # Move model inputs to GPU.
        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        with torch.no_grad():

            outputs = model.generate(
                **inputs,
                max_new_tokens=120,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        # ----------------------------------------------------
        # Decode only newly generated tokens
        # ----------------------------------------------------

        input_length = inputs["input_ids"].shape[-1]

        generated_tokens = outputs[
            0,
            input_length:
        ]

        response = tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        print("\nFINAI RESPONSE:")
        print(response)

    print("\n" + "=" * 70)
    print("FINAI CHAT TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()