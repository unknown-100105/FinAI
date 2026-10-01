import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "sarvamai/sarvam-1"

print("=" * 60)
print("FINAI - SARVAM-1 TEST")
print("=" * 60)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)

print("Model loaded!")
print("Device:", model.device)

prompt = "தமிழ்நாட்டில் டிஜிட்டல் பணம் செலுத்துதல் பற்றி"

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("\nGenerating response...\n")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)