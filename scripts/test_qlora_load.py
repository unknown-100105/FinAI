import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

MODEL_NAME = "sarvamai/sarvam-1"


def main():
    print("=" * 60)
    print("FINAI QLoRA LOAD TEST")
    print("=" * 60)

    print("CUDA:", torch.cuda.is_available())
    print("GPU:", torch.cuda.get_device_name(0))

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading 4-bit model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
    )

    print("\nMODEL LOADED SUCCESSFULLY")

    prompt = (
        "### User:\n"
        "What is a failed payment?\n\n"
        "### Assistant:\n"
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    print("\nGenerating test response...")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            do_sample=False,
        )

    response = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    print("\n" + response)

    print("\n" + "=" * 60)
    print("QLORA LOAD TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()