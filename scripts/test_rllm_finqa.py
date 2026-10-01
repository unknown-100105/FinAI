import gc
import time

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


MODEL_ID = "rLLM/rLLM-FinQA-4B"


def main():

    print("=" * 80)
    print("FINAI rLLM-FinQA-4B LOCAL SMOKE TEST")
    print("=" * 80)

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "VRAM:",
        round(
            torch.cuda.get_device_properties(0).total_memory
            / 1024**3,
            2,
        ),
        "GB",
    )

    print()
    print("MODEL:", MODEL_ID)
    print("LOADING MODE: 4-bit NF4")
    print()

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    start = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=quant_config,
        device_map="auto",
        low_cpu_mem_usage=True,
    )

    load_time = time.perf_counter() - start

    print(
        "LOAD TIME:",
        round(load_time, 2),
        "seconds",
    )

    allocated = (
        torch.cuda.memory_allocated(0)
        / 1024**3
    )

    reserved = (
        torch.cuda.memory_reserved(0)
        / 1024**3
    )

    print(
        "VRAM ALLOCATED:",
        round(allocated, 2),
        "GB",
    )

    print(
        "VRAM RESERVED:",
        round(reserved, 2),
        "GB",
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are FinAI's financial reasoning "
                "specialist. Answer using only the "
                "information supported by the question. "
                "Do not invent financial facts."
            ),
        },
        {
            "role": "user",
            "content": (
                "A loan principal is ₹10,00,000 at "
                "8.5% annual interest for 20 years. "
                "Explain what the monthly EMI represents. "
                "Do not calculate it."
            ),
        },
    ]

    print()
    print("PROMPT:")
    print(messages[-1]["content"])
    print()

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    start = time.perf_counter()

    with torch.inference_mode():

        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generation_time = (
        time.perf_counter() - start
    )

    generated_tokens = outputs.shape[-1] - (
        inputs["input_ids"].shape[-1]
    )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True,
    ).strip()

    print("GENERATION TIME:")
    print(
        round(generation_time, 2),
        "seconds",
    )

    print(
        "NEW TOKENS:",
        generated_tokens,
    )

    if generated_tokens > 0:
        print(
            "TOKENS/SECOND:",
            round(
                generated_tokens
                / generation_time,
                2,
            ),
        )

    print()
    print("RESPONSE:")
    print(response)

    allocated_after = (
        torch.cuda.memory_allocated(0)
        / 1024**3
    )

    print()
    print(
        "VRAM AFTER GENERATION:",
        round(allocated_after, 2),
        "GB",
    )

    print()
    print("SMOKE TEST: PASSED")

    del outputs
    del inputs
    del model
    del tokenizer

    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
