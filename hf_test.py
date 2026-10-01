from huggingface_hub import model_info

model_name = "sarvamai/sarvam-1"

print("Checking Hugging Face access...")
info = model_info(model_name)

print("Model:", info.id)
print("Model exists and is accessible!")