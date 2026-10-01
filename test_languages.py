import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "sarvamai/sarvam-1"

print("=" * 60)
print("FINAI — 5 LANGUAGE BASELINE")
print("=" * 60)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.float16,
    device_map="auto"
)

print("Model loaded on:", model.device)

prompts = {
    "English": "Explain digital payments in simple words:",
    "Tamil": "டிஜிட்டல் பணம் செலுத்துதல் பற்றி எளிமையாக விளக்குங்கள்:",
    "Telugu": "డిజిటల్ చెల్లింపుల గురించి సులభంగా వివరించండి:",
    "Kannada": "ಡಿಜಿಟಲ್ ಪಾವತಿಗಳ ಬಗ್ಗೆ ಸರಳವಾಗಿ ವಿವರಿಸಿ:",
    "Malayalam": "ഡിജിറ്റൽ പേയ്‌മെന്റുകളെക്കുറിച്ച് ലളിതമായി വിശദീകരിക്കുക:"
}

for language, prompt in prompts.items():

    print("\n" + "=" * 60)
    print(language)
    print("=" * 60)
    print("Prompt:", prompt)

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

    response = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    print("\nResponse:")
    print(response)

print("\n" + "=" * 60)
print("5-LANGUAGE BASELINE COMPLETE")
print("=" * 60)