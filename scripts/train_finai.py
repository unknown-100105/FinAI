import torch

from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer


MODEL_NAME = "sarvamai/sarvam-1"

DATA_DIR = "data/sft_v2"
OUTPUT_DIR = "models/finai-sarvam-lora"

# Keep this TRUE for the first test.
SMOKE_TEST = False

def main():

    print("=" * 70)
    print("FINAI QLoRA TRAINING")
    print("=" * 70)

    # ========================================================
    # GPU
    # ========================================================

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available.")

    print("CUDA:", torch.cuda.is_available())
    print("GPU:", torch.cuda.get_device_name(0))

    # ========================================================
    # TOKENIZER
    # ========================================================

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ========================================================
    # 4-BIT QLoRA
    # ========================================================

    print("Preparing 4-bit configuration...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # ========================================================
    # MODEL
    # ========================================================

    print("Loading Sarvam-1 in 4-bit...")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quantization_config,
        device_map="auto",
    )

    print("Base model loaded.")

    model.config.use_cache = False

    model = prepare_model_for_kbit_training(model)

    # ========================================================
    # LoRA
    # ========================================================

    print("Preparing LoRA adapter...")

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

    print("Loading datasets...")

    dataset = load_dataset(
        "json",
        data_files={
            "train": f"{DATA_DIR}/train.jsonl",
            "validation": f"{DATA_DIR}/validation.jsonl",
        },
    )

    print(
        "Training examples:",
        len(dataset["train"])
    )

    print(
        "Validation examples:",
        len(dataset["validation"])
    )

    # ========================================================
    # TRAINING MODE
    # ========================================================

    if SMOKE_TEST:

        print("\n*** SMOKE TEST MODE ***")

        max_steps = 5
        warmup_steps = 0
        save_strategy = "no"
        eval_strategy = "no"

    else:

        print("\n*** FULL TRAINING MODE ***")

        max_steps = -1
        warmup_steps = 30
        save_strategy = "steps"
        eval_strategy = "steps"

    # ========================================================
    # TRAINING CONFIGURATION
    # ========================================================

    training_args = SFTConfig(

        output_dir=OUTPUT_DIR,

        num_train_epochs=1,
        max_steps=max_steps,

        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,

        gradient_accumulation_steps=16,

        learning_rate=2e-4,

        warmup_steps=warmup_steps,

        lr_scheduler_type="cosine",

        optim="paged_adamw_8bit",

        # IMPORTANT:
        # Use BF16, not FP16.
        fp16=False,
        bf16=True,

        gradient_checkpointing=True,

        gradient_checkpointing_kwargs={
            "use_reentrant": False
        },

        max_length=512,

        packing=True,

        completion_only_loss=True,

        logging_steps=1,

        eval_strategy=eval_strategy,

        save_strategy=save_strategy,

        save_total_limit=2,

        report_to="none",

        seed=42,

        remove_unused_columns=False,
    )

    # ========================================================
    # TRAINER
    # ========================================================

    trainer = SFTTrainer(

    model=model,

    args=training_args,

    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],

    processing_class=tokenizer,

    peft_config=peft_config,
)

    # ========================================================
    # TRAIN
    # ========================================================

    print("\nStarting training...\n")

    trainer.train()

    # ========================================================
    # SAVE
    # ========================================================

    print("\nSaving adapter...")

    trainer.save_model(OUTPUT_DIR)

    tokenizer.save_pretrained(
        OUTPUT_DIR
    )

    print("\n" + "=" * 70)

    if SMOKE_TEST:

        print("FINAI QLoRA SMOKE TEST COMPLETE")
        print()
        print("The training pipeline works.")
        print()
        print("Next:")
        print("Change SMOKE_TEST = False")
        print("and start the full training.")

    else:

        print("FINAI QLoRA TRAINING COMPLETE")

    print("=" * 70)

    print(
        "Adapter location:",
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()