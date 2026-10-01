import torch

from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer


# ============================================================
# FINAI DOMAIN ADAPTATION
# ============================================================

MODEL_NAME = "sarvamai/sarvam-1"

DATA_FILE = (
    "data/domain_train/domain_train_20k.jsonl"
)

OUTPUT_DIR = (
    "models/finai-domain-lora"
)


# ------------------------------------------------------------
# FIRST RUN:
# True  = only 5 steps
# False = full domain adaptation
# ------------------------------------------------------------

SMOKE_TEST = False


def main():

    print("=" * 70)
    print("FINAI DOMAIN ADAPTATION")
    print("=" * 70)

    # ========================================================
    # GPU CHECK
    # ========================================================

    if not torch.cuda.is_available():

        raise RuntimeError(
            "CUDA is not available."
        )

    print(
        "CUDA:",
        torch.cuda.is_available()
    )

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    # ========================================================
    # TOKENIZER
    # ========================================================

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    if tokenizer.pad_token is None:

        tokenizer.pad_token = (
            tokenizer.eos_token
        )

    # ========================================================
    # 4-BIT QLoRA
    # ========================================================

    print(
        "Preparing 4-bit configuration..."
    )

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,

        bnb_4bit_quant_type="nf4",

        bnb_4bit_compute_dtype=(
            torch.bfloat16
        ),

        bnb_4bit_use_double_quant=True,
    )

    # ========================================================
    # BASE MODEL
    # ========================================================

    print(
        "Loading Sarvam-1 in 4-bit..."
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=(
            quantization_config
        ),
        device_map="auto",
    )

    print("Base model loaded.")

    model.config.use_cache = False

    model = prepare_model_for_kbit_training(
        model
    )

    # ========================================================
    # LoRA
    # ========================================================

    print(
        "Preparing domain LoRA adapter..."
    )

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

    # ========================================================
    # DATASET
    # ========================================================

    print(
        "\nLoading domain corpus..."
    )

    dataset = load_dataset(
        "json",
        data_files={
            "train": DATA_FILE,
        },
    )

    print(
        "Domain examples:",
        len(dataset["train"])
    )

    # ========================================================
    # TRAINING MODE
    # ========================================================

    if SMOKE_TEST:

        print(
            "\n*** DOMAIN SMOKE TEST MODE ***"
        )

        max_steps = 5

        save_strategy = "no"

    else:

        print(
            "\n*** FULL DOMAIN ADAPTATION ***"
        )

        max_steps = -1

        save_strategy = "steps"

    # ========================================================
    # TRAINING CONFIGURATION
    # ========================================================

    training_args = SFTConfig(

        output_dir=OUTPUT_DIR,

        # One pass through the corpus.
        num_train_epochs=1,

        max_steps=max_steps,

        # RTX 4060 safe settings.
        per_device_train_batch_size=1,

        gradient_accumulation_steps=16,

        # Domain adaptation uses a lower
        # learning rate than our task SFT.
        learning_rate=2e-5,

        warmup_steps=30,

        lr_scheduler_type="cosine",

        optim="paged_adamw_8bit",

        # BF16 fixes the earlier FP16/BF16
        # gradient-scaler problem.
        fp16=False,

        bf16=True,

        gradient_checkpointing=True,

        gradient_checkpointing_kwargs={
            "use_reentrant": False
        },

        # Domain examples are approximately
        # article chunks. 512 is memory-safe.
        max_length=512,

        # IMPORTANT:
        # We intentionally disable packing here.
        # This avoids the Flash-Attention warning
        # we saw during the previous run.
        packing=False,

        # No validation during this layer.
        # We will evaluate the resulting model
        # separately.
        eval_strategy="no",

        save_strategy=save_strategy,

        save_steps=500,

        save_total_limit=2,

        logging_steps=10,

        report_to="none",

        seed=42,

        remove_unused_columns=False,

        # Plain text dataset field.
        dataset_text_field="text",
    )

    # ========================================================
    # TRAINER
    # ========================================================

    print(
        "\nCreating domain trainer..."
    )

    trainer = SFTTrainer(

        model=model,

        args=training_args,

        train_dataset=dataset["train"],

        processing_class=tokenizer,

        peft_config=peft_config,
    )

    # ========================================================
    # TRAIN
    # ========================================================

    print(
        "\nStarting domain training...\n"
    )

    trainer.train()

    # ========================================================
    # SAVE
    # ========================================================

    print(
        "\nSaving domain adapter..."
    )

    trainer.save_model(
        OUTPUT_DIR
    )

    tokenizer.save_pretrained(
        OUTPUT_DIR
    )

    print("\n" + "=" * 70)

    if SMOKE_TEST:

        print(
            "FINAI DOMAIN SMOKE TEST COMPLETE"
        )

        print()
        print(
            "The domain-training pipeline works."
        )

        print()
        print(
            "Next: change SMOKE_TEST = False"
        )

    else:

        print(
            "FINAI DOMAIN ADAPTATION COMPLETE"
        )

    print("=" * 70)

    print(
        "Adapter location:",
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()