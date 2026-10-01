from pathlib import Path
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel


ROOT = Path(__file__).resolve().parents[1]

BASE_MODEL = "sarvamai/sarvam-1"

ADAPTER = (
    ROOT
    / "models"
    / "finai-v3-diagnostic-smoke"
)


def generate(model, tokenizer, prompt):

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1536,
    )

    inputs = {
        k: v.to(model.device)
        for k, v in inputs.items()
    }

    with torch.no_grad():

        output = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output[
        0
    ][
        inputs["input_ids"].shape[1]:
    ]

    return tokenizer.decode(
        new_tokens,
        skip_special_tokens=True
    )


def main():

    print("=" * 72)
    print("FINAI-V3 DIAGNOSTIC ADAPTER INFERENCE TEST")
    print("=" * 72)

    print(
        "CUDA:",
        torch.cuda.is_available()
    )

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    tokenizer = AutoTokenizer.from_pretrained(
        ADAPTER,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print()
    print("Loading base model...")

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    print("Loading V3 adapter...")

    model = PeftModel.from_pretrained(
        model,
        ADAPTER,
    )

    model.eval()

    print()
    print("=" * 72)
    print("TEST 1 — FINANCIAL QA")
    print("=" * 72)

    prompt1 = """You are FinAI, a financial-domain assistant.

USER:
What is the difference between a debit card and a credit card?
"""

    print()
    print("USER:")
    print(
        "What is the difference between a debit card "
        "and a credit card?"
    )

    print()
    print("MODEL:")
    print(
        generate(
            model,
            tokenizer,
            prompt1
        )
    )

    print()
    print("=" * 72)
    print("TEST 2 — FINAI ROUTER")
    print("=" * 72)

    prompt2 = """You are FinAI, a financial-domain assistant.

For FinAI routing requests, identify the user's intent and return the response using exactly this format:
INTENT: <intent>
RISK_LEVEL: <low|medium|high>
REQUIRES_TOOL: <true|false>
TOOL: <tool name or NONE>
RESPONSE: <helpful answer>

Do not add extra fields.

USER:
My card is lost.
"""

    print()
    print("USER:")
    print("My card is lost.")

    print()
    print("MODEL:")

    print(
        generate(
            model,
            tokenizer,
            prompt2
        )
    )

    print()
    print("=" * 72)
    print("INFERENCE TEST COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
