import sys
from pathlib import Path

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer


# ============================================================
# PROJECT PATH
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# CONFIGURATION
# ============================================================

BASE_MODEL = "sarvamai/sarvam-1"

DOMAIN_ADAPTER = (
    ROOT / "models" / "finai-domain-lora"
)

DATA_FILE = (
    ROOT / "data" / "sft_final" / "train.jsonl"
)

OUTPUT_DIR = (
    ROOT / "models" / "finai-v2-lora"
)

SMOKE_TEST = False

SMOKE_EXAMPLES = 64
SMOKE_STEPS = 5


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FINAI-v2 LAYER 2 TRAINING")
    print("=" * 70)

    print(
        "CUDA:",
        torch.cuda.is_available()
    )

    if torch.cuda.is_available():

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    print(
        "Smoke test:",
        SMOKE_TEST
    )

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"SFT dataset not found:\n{DATA_FILE}"
        )

    if not DOMAIN_ADAPTER.exists():

        raise FileNotFoundError(
            f"Domain adapter not found:\n{DOMAIN_ADAPTER}"
        )

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        str(DOMAIN_ADAPTER)
    )

    if tokenizer.pad_token is None:

        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizer loaded.")

    # --------------------------------------------------------
    # Load SFT dataset
    # --------------------------------------------------------

    print("\nLoading Layer-2 dataset...")

    dataset = load_dataset(
        "json",
        data_files=str(DATA_FILE),
        split="train",
    )

    print(
        "Total examples:",
        len(dataset)
    )

    # --------------------------------------------------------
    # Smoke test subset
    # --------------------------------------------------------

    if SMOKE_TEST:

        count = min(
            SMOKE_EXAMPLES,
            len(dataset)
        )

        dataset = dataset.select(
            range(count)
        )

        print(
            "Smoke-test examples:",
            len(dataset)
        )

    # --------------------------------------------------------
    # 4-bit configuration
    # --------------------------------------------------------

    print(
        "\nPreparing 4-bit configuration..."
    )

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # --------------------------------------------------------
    # Base model
    # --------------------------------------------------------

    print(
        "Loading Sarvam-1 in 4-bit..."
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="auto",
    )

    print("Base model loaded.")

    # --------------------------------------------------------
    # Continue training Layer-1 adapter
    #
    # IMPORTANT:
    # is_trainable=True
    # --------------------------------------------------------

    print(
        "Loading FinAI-Domain adapter as trainable..."
    )

    model = PeftModel.from_pretrained(
        base_model,
        str(DOMAIN_ADAPTER),
        is_trainable=True,
    )

    model.train()

    print(
        "Domain adapter loaded."
    )

    model.print_trainable_parameters()

    # --------------------------------------------------------
    # Verify trainable parameters
    # --------------------------------------------------------

    trainable_parameters = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    if trainable_parameters == 0:

        raise RuntimeError(
            "No trainable parameters found. "
            "The adapter was not loaded as trainable."
        )

    print(
        "Trainable parameters:",
        trainable_parameters
    )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    if SMOKE_TEST:

        run_output = (
            ROOT
            / "models"
            / "finai-v2-lora-smoke"
        )

    else:

        run_output = OUTPUT_DIR

    run_output.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Training configuration
    # --------------------------------------------------------

    max_steps = (
        SMOKE_STEPS
        if SMOKE_TEST
        else -1
    )

    training_args = SFTConfig(
        output_dir=str(run_output),

        # Training
        num_train_epochs=1,
        max_steps=max_steps,

        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,

        learning_rate=1e-5,
        lr_scheduler_type="cosine",
        warmup_steps=1,

        # Precision
        fp16=False,
        bf16=False,

        # Memory
        gradient_checkpointing=True,

        # Sequence
        max_length=1024,

        # Dataset format
        completion_only_loss=True,

        # Packing disabled for predictable smoke testing
        packing=False,

        # Logging
        logging_steps=1,
        report_to="none",

        # Save
        save_strategy="steps",
        save_steps=250,
        save_total_limit=3,

        # Evaluation disabled during smoke test
        eval_strategy="no",

        # Reproducibility
        seed=42,
    )

    # --------------------------------------------------------
    # Trainer
    #
    # No peft_config here.
    # We are continuing the existing PeftModel.
    # --------------------------------------------------------

    print(
        "\nCreating SFTTrainer..."
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print(
        "Trainer created."
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    if SMOKE_TEST:

        print("STARTING LAYER-2 SMOKE TEST")

    else:

        print("STARTING FULL LAYER-2 TRAINING")

    print("=" * 70)

    result = trainer.train()

    print("\nTraining result:")
    print(result)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print(
        "\nSaving Layer-2 adapter..."
    )

    trainer.save_model(
        str(run_output)
    )

    tokenizer.save_pretrained(
        str(run_output)
    )

    print("\n" + "=" * 70)

    if SMOKE_TEST:

        print(
            "FINAI-v2 LAYER-2 SMOKE TEST COMPLETE"
        )

    else:

        print(
            "FINAI-v2 LAYER-2 TRAINING COMPLETE"
        )

    print("=" * 70)

    print(
        "Output:",
        run_output
    )


if __name__ == "__main__":
    main()