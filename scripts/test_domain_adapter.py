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
    ROOT / "models" / "finai-domain-lora"
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
    print("FINAI LAYER-1 MULTILINGUAL QUALITY TEST")
    print("=" * 70)

    if not torch.cuda.is_available():

        print("ERROR: CUDA is not available.")
        return

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    # --------------------------------------------------------
    # Check adapter
    # --------------------------------------------------------

    print("\nChecking adapter...")

    required_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
    ]

    for filename in required_files:

        path = ADAPTER_PATH / filename

        print(
            f"{filename} -> "
            f"{'FOUND' if path.exists() else 'MISSING'}"
        )

        if not path.exists():
            return

    # --------------------------------------------------------
    # Tokenizer
    # --------------------------------------------------------

    print("\nLoading tokenizer...")

    tokenizer_source = str(ADAPTER_PATH)

    tokenizer_file = (
        ADAPTER_PATH / "tokenizer.json"
    )

    if not tokenizer_file.exists():

        tokenizer_source = BASE_MODEL

    print(
        "Tokenizer source:",
        tokenizer_source
    )

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_source
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizer loaded.")

    # --------------------------------------------------------
    # Quantization
    # --------------------------------------------------------

    print("\nPreparing 4-bit configuration...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # --------------------------------------------------------
    # Base model
    # --------------------------------------------------------

    print("Loading Sarvam-1 in 4-bit...")

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="auto",
    )

    print("Base model loaded.")

    # --------------------------------------------------------
    # Adapter
    # --------------------------------------------------------

    print("Loading FinAI domain adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_PATH),
    )

    model.eval()

    print("Domain adapter loaded.")

    device = (
        model.get_input_embeddings()
        .weight.device
    )

    print(
        "Model input device:",
        device
    )

    # --------------------------------------------------------
    # Multilingual tests
    # --------------------------------------------------------

    for language, question in TESTS:

        print("\n" + "=" * 70)
        print(language)
        print("=" * 70)

        print("Question:")
        print(question)

        try:

            # ------------------------------------------------
            # Build prompt text
            # ------------------------------------------------

            chat_template = getattr(
                tokenizer,
                "chat_template",
                None,
            )

            if chat_template:

                prompt_text = (
                    tokenizer.apply_chat_template(
                        [
                            {
                                "role": "user",
                                "content": question,
                            }
                        ],
                        tokenize=False,
                        add_generation_prompt=True,
                    )
                )

            else:

                prompt_text = (
                    "### User:\n"
                    + question
                    + "\n\n"
                    + "### Assistant:\n"
                )

            # ------------------------------------------------
            # Tokenize normally
            # ------------------------------------------------

            tokenized = tokenizer(
                prompt_text,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
            )

            input_ids = tokenized["input_ids"]

            attention_mask = tokenized.get(
                "attention_mask"
            )

            if not torch.is_tensor(input_ids):

                raise TypeError(
                    "input_ids is not a PyTorch tensor."
                )

            input_ids = input_ids.to(device)

            if attention_mask is not None:
                attention_mask = attention_mask.to(device)

            print("\nGenerating response...")

            # ------------------------------------------------
            # Generate
            # ------------------------------------------------

            with torch.no_grad():

                output = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=100,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

            # ------------------------------------------------
            # Decode only newly generated tokens
            # ------------------------------------------------

            input_length = input_ids.shape[1]

            generated_tokens = (
                output[0][input_length:]
            )

            response = tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True,
            )

            print("\nMODEL RESPONSE:")
            print(response)

        except Exception as error:

            print("\nTEST ERROR:")
            print(
                "Type:",
                type(error).__name__
            )
            print(
                "Message:",
                str(error)
            )

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("MULTILINGUAL QUALITY TEST COMPLETE")
    print("=" * 70)

    del model
    del base_model

    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()