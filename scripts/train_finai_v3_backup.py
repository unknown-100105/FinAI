from pathlib import Path
import json
import torch

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer


ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "training_ready_v2"
    / "train.jsonl"
)

VALIDATION_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "training_ready_v2"
    / "validation.jsonl"
)

OUTPUT_DIR = (
    ROOT
    / "models"
    / "finai-v3-lora"
)

MODEL_NAME = "sarvamai/sarvam-1"

SMOKE_STEPS = 100


def main():

    print("=" * 72)
    print("FINAI-V3 SMOKE TRAINING")
    print("=" * 72)

    print()
    print("CUDA:", torch.cuda.is_available())

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    print()
    print("TRAIN FILE:", TRAIN_FILE)
    print("VALIDATION FILE:", VALIDATION_FILE)
    print("OUTPUT:", OUTPUT_DIR)

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(TRAIN_FILE)

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(VALIDATION_FILE)

    print()
    print("Loading datasets...")

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_FILE),
            "validation": str(VALIDATION_FILE),
        },
    )

    print(
        "TRAIN RECORDS:",
        len(dataset["train"])
    )

    print(
        "VALIDATION RECORDS:",
        len(dataset["validation"])
    )

    print()
    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizer loaded.")

    print()
    print("Loading 4-bit model...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True,
    )

    print("Model loaded.")

    print()
    print("Configuring LoRA...")

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),

        # Smoke-test limit
        max_steps=SMOKE_STEPS,

        # Small memory footprint for RTX 4060 8GB
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,

        learning_rate=1e-5,
        warmup_steps=10,
        lr_scheduler_type="cosine",

        gradient_checkpointing=True,

        fp16=True,
        bf16=False,

        logging_steps=5,

        eval_strategy="steps",
        eval_steps=50,

        save_strategy="steps",
        save_steps=50,
        save_total_limit=2,

        seed=42,

        completion_only_loss=True,

        packing=False,

        report_to="none",

        dataset_text_field=None,
        max_length=1024,
    )

    print()
    print("Creating trainer...")

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    print()
    print("=" * 72)
    print("STARTING 100-STEP SMOKE TEST")
    print("=" * 72)

    result = trainer.train()

    print()
    print("=" * 72)
    print("SMOKE TRAINING COMPLETE")
    print("=" * 72)

    print(
        "TRAIN LOSS:",
        result.training_loss
    )

    print(
        "GLOBAL STEPS:",
        result.global_step
    )

    print()
    print("Saving adapter...")

    trainer.save_model(
        str(OUTPUT_DIR)
    )

    tokenizer.save_pretrained(
        str(OUTPUT_DIR)
    )

    print()
    print("[OK] Adapter:", OUTPUT_DIR)

    print("=" * 72)
    print("FINAI-V3 SMOKE TEST PASSED")
    print("=" * 72)


if __name__ == "__main__":
    main()
