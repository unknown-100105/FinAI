import torch

from pathlib import Path

from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


class FinAIEngine:
    """
    Loads Sarvam-1 with the FinAI domain adapter.

    Important:
    Creating/importing this class does NOT load the model.
    The GPU is used only when load() is called.
    """

    BASE_MODEL = "sarvamai/sarvam-1"

    def __init__(
        self,
        adapter_path="models/finai-domain-lora",
    ):

        self.adapter_path = Path(
            adapter_path
        )

        self.tokenizer = None
        self.model = None

        self.loaded = False

    def load(self):

        if self.loaded:
            return

        if not torch.cuda.is_available():

            raise RuntimeError(
                "CUDA is not available. "
                "FinAI requires the NVIDIA GPU for local inference."
            )

        if not self.adapter_path.exists():

            raise FileNotFoundError(
                f"FinAI domain adapter not found: "
                f"{self.adapter_path}"
            )

        print("=" * 70)
        print("LOADING FINAI")
        print("=" * 70)

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

        # ----------------------------------------------------
        # Tokenizer
        # ----------------------------------------------------

        print("\nLoading tokenizer...")

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                self.BASE_MODEL
            )
        )

        if self.tokenizer.pad_token is None:

            self.tokenizer.pad_token = (
                self.tokenizer.eos_token
            )

        # ----------------------------------------------------
        # 4-bit configuration
        # ----------------------------------------------------

        print(
            "Preparing 4-bit configuration..."
        )

        quantization_config = (
            BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=(
                    torch.bfloat16
                ),
                bnb_4bit_use_double_quant=True,
            )
        )

        # ----------------------------------------------------
        # Base model
        # ----------------------------------------------------

        print(
            "Loading Sarvam-1..."
        )

        base_model = (
            AutoModelForCausalLM.from_pretrained(
                self.BASE_MODEL,
                quantization_config=(
                    quantization_config
                ),
                device_map="auto",
            )
        )

        # ----------------------------------------------------
        # Domain adapter
        # ----------------------------------------------------

        print(
            "Loading FinAI domain adapter..."
        )

        self.model = PeftModel.from_pretrained(
            base_model,
            str(self.adapter_path),
        )

        self.model.eval()

        self.loaded = True

        print("\nFINAI MODEL LOADED")
        print("=" * 70)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 120,
        temperature: float = 0.2,
    ):

        if not self.loaded:
            self.load()

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )

        # Move tensors to the same device as
        # the model's input embedding.
        model_device = (
            self.model.get_input_embeddings()
            .weight.device
        )

        inputs = {
            key: value.to(model_device)
            for key, value in inputs.items()
        }

        with torch.no_grad():

            generated = self.model.generate(
                **inputs,

                max_new_tokens=max_new_tokens,

                temperature=temperature,

                do_sample=(
                    temperature > 0
                ),

                pad_token_id=(
                    self.tokenizer.pad_token_id
                ),

                eos_token_id=(
                    self.tokenizer.eos_token_id
                ),
            )

        # Only decode newly generated tokens.
        input_length = (
            inputs["input_ids"].shape[1]
        )

        new_tokens = generated[
            0,
            input_length:
        ]

        response = self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        )

        return response.strip()

    def unload(self):

        if self.model is not None:

            del self.model

            self.model = None

        if self.tokenizer is not None:

            del self.tokenizer

            self.tokenizer = None

        self.loaded = False

        if torch.cuda.is_available():

            torch.cuda.empty_cache()

        print("FinAI model unloaded.")