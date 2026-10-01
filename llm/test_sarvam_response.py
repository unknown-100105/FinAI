import torch

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import PeftModel


BASE_MODEL = "sarvamai/sarvam-1"
ADAPTER_PATH = "models/finai-v3-final-smoke"


def build_prompt():
    return """
You are FinAI, a financial response assistant.

The system has already verified the following calculation.
You MUST preserve every numerical value exactly.
Do not recalculate the values.
Do not invent additional financial facts.
Do not change the user's intent.
Return only a clear user-facing response.

USER REQUEST:
Calculate EMI for a ₹10 lakh loan at 8.5% annual interest for 20 years.

VERIFIED RESULT:
Loan amount: ₹1,000,000.00
Annual interest rate: 8.50%
Tenure: 240 months
Monthly EMI: ₹8,678.23
Total payment: ₹2,082,775.76
Total interest: ₹1,082,775.76

SOURCE:
deterministic_finance_engine

PERSONA:
neutral

FINAL RESPONSE:
""".strip()


print("=" * 80)
print("FinAI CONTROLLED SARVAM-1 RESPONSE TEST")
print("=" * 80)

print("Base model :", BASE_MODEL)
print("Adapter    :", ADAPTER_PATH)
print()

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL,
    trust_remote_code=True,
)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading 4-bit base model...")

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=quant_config,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)

print("Loading FinAI smoke adapter...")

model = PeftModel.from_pretrained(
    model,
    ADAPTER_PATH,
)

model.eval()

prompt = build_prompt()

print()
print("=" * 80)
print("PROMPT")
print("=" * 80)
print(prompt)

inputs = tokenizer(
    prompt,
    return_tensors="pt",
)

inputs = {
    key: value.to(model.device)
    for key, value in inputs.items()
}

print()
print("Generating response...")

with torch.inference_mode():

    output = model.generate(
        **inputs,
        max_new_tokens=120,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
        repetition_penalty=1.05,
        use_cache=True,
    )

new_tokens = output[0][inputs["input_ids"].shape[1]:]

response = tokenizer.decode(
    new_tokens,
    skip_special_tokens=True,
).strip()

print()
print("=" * 80)
print("SARVAM-1 RESPONSE")
print("=" * 80)
print(response)

print()
print("=" * 80)
print("NUMERICAL PRESERVATION CHECK")
print("=" * 80)

required_values = [
    "8,678.23",
    "2,082,775.76",
    "1,082,775.76",
]

for value in required_values:
    print(
        f"{value:20s}:",
        "PASS" if value in response else "MISSING"
    )

print()
print("Controlled response test completed.")
