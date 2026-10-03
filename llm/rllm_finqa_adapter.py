import time
from typing import Any, Dict

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


class RLLMFinQAModelAdapter:

    MODEL_ID = "rLLM/rLLM-FinQA-4B"
    FINAI_MODEL_ID = "rllm-finqa-4b"

    def __init__(self):

        self.model_id = self.FINAI_MODEL_ID
        self.model = None
        self.tokenizer = None
        self.loaded = False
        self.load_seconds = None

    def load(self):

        if self.loaded:
            return

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is required for rLLM-FinQA-4B."
            )

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        start = time.perf_counter()

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                self.MODEL_ID,
            )
        )

        self.model = (
            AutoModelForCausalLM.from_pretrained(
                self.MODEL_ID,
                quantization_config=quant_config,
                device_map="auto",
                low_cpu_mem_usage=True,
            )
        )

        self.load_seconds = (
            time.perf_counter() - start
        )

        self.loaded = True

    def generate(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 256,
    ) -> Dict[str, Any]:

        self.load()

        system_message = (
            "You are FinAI's financial reasoning specialist. "
            "The system provides authoritative verified financial results. "
            "Preserve every verified numeric and monetary value exactly as supplied; "
            "never round, shorten, approximate, recalculate, or change them. "
            "Repeat important verified values explicitly when explaining the result. "
            "Never invent facts, assumptions, rates, fees, taxes, market conditions, "
            "or other financial claims that are not supplied. "
            "Persona controls tone only and must never change financial meaning or factual content. "
            "Keep the response complete, concise, and directly relevant to the user's request. "
            "Do not execute actions."
        )

        user_message = (
            f"Intent: {intent}\n"
            f"Result source: {source}\n"
            f"Verified result: {verified_result}\n"
            f"User request: {user_text}\n"
            f"Language: {language}\n"
            f"Persona: {persona}\n\n"
            "Respond only to the user's request."
        )

        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.model.device)
            for key, value in inputs.items()
        }

        start = time.perf_counter()

        with torch.inference_mode():

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=(
                    self.tokenizer.eos_token_id
                ),
            )

        generation_seconds = (
            time.perf_counter() - start
        )

        input_tokens = (
            inputs["input_ids"].shape[-1]
        )

        generated_tokens = (
            outputs.shape[-1] - input_tokens
        )

        generated_ids = outputs[0][input_tokens:]
        response = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        ).strip()

        eos_ids = self.tokenizer.eos_token_id
        if eos_ids is None:
            eos_ids = set()
        elif isinstance(eos_ids, int):
            eos_ids = {eos_ids}
        else:
            eos_ids = set(eos_ids)

        hit_eos = bool(eos_ids) and any(
            int(token_id) in eos_ids
            for token_id in generated_ids.tolist()
        )

        generation_complete = (
            generated_tokens < max_new_tokens
            or hit_eos
        )
        truncated = not generation_complete
        finish_reason = (
            "stop"
            if generation_complete
            else "length"
        )

        tokens_per_second = (
            generated_tokens / generation_seconds
            if generation_seconds > 0
            else 0.0
        )

        return {
            "status": "GENERATED",
            "model_id": "rllm-finqa-4b",
            "source": source,
            "language": language,
            "persona": persona,
            "response": response,
            "generation_complete": generation_complete,
            "truncated": truncated,
            "finish_reason": finish_reason,
            "metrics": {
                "load_seconds": self.load_seconds,
                "generation_seconds": generation_seconds,
                "generated_tokens": generated_tokens,
                "tokens_per_second": tokens_per_second,
                "vram_allocated_gb": (
                    torch.cuda.memory_allocated()
                    / 1024**3
                ),
            },
        }


if __name__ == "__main__":

    adapter = RLLMFinQAModelAdapter()

    result = adapter.generate(
        user_text=(
            "Explain what EMI represents for a "
            "₹10 lakh loan at 8.5% for 20 years."
        ),
        intent="EMI_QUERY",
        verified_result={
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
    )

    print("=" * 80)
    print("FINAI rLLM-FinQA-4B ADAPTER")
    print("=" * 80)
    print("MODEL:", result["model_id"])
    print("STATUS:", result["status"])
    print("METRICS:", result["metrics"])
    print()
    print("RESPONSE:")
    print(result["response"])

