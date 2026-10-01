from pathlib import Path
import torch

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


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
    / "finai-v3-diagnostic-smoke"
)

MODEL_NAME = "sarvamai/sarvam-1"

TRAIN_SAMPLES = 200
VALIDATION_SAMPLES = 50
MAX_LENGTH = 1024
MAX_STEPS = 20


def build_text(example):
    prompt = str(
        example.get("prompt", "")
    ).strip()

    completion = str(
        example.get("completion", "")
    ).strip()

    return {
        "text": prompt
        + "\n"
        + completion
    }


def main():

    print("=" * 72)
    print("FINAI-V3 CLEAN DIAGNOSTIC SMOKE TEST")
    print("=" * 72)

    print()
    print("CUDA:", torch.cuda.is_available())

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(TRAIN_FILE)

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(VALIDATION_FILE)

    print()
    print("Loading raw dataset...")

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_FILE),
            "validation": str(VALIDATION_FILE),
        },
    )

    print(
        "FULL TRAIN:",
        len(dataset["train"])
    )

    print(
        "FULL VALIDATION:",
        len(dataset["validation"])
    )

    # Small deterministic smoke-test subset.
    train_ds = dataset["train"].select(
        range(
            min(
                TRAIN_SAMPLES,
                len(dataset["train"])
            )
        )
    )

    validation_ds = dataset["validation"].select(
        range(
            min(
                VALIDATION_SAMPLES,
                len(dataset["validation"])
            )
        )
    )

    train_ds = train_ds.map(
        build_text,
        remove_columns=train_ds.column_names,
    )

    validation_ds = validation_ds.map(
        build_text,
        remove_columns=validation_ds.column_names,
    )

    print()
    print(
        "SMOKE TRAIN:",
        len(train_ds)
    )

    print(
        "SMOKE VALIDATION:",
        len(validation_ds)
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

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_LENGTH,
            padding=False,
        )

    print()
    print("Tokenizing smoke dataset...")

    train_tokens = train_ds.map(
        tokenize,
        batched=True,
        remove_columns=["text"],
    )

    validation_tokens = validation_ds.map(
        tokenize,
        batched=True,
        remove_columns=["text"],
    )

    print(
        "Tokenized TRAIN:",
        len(train_tokens)
    )

    print(
        "Tokenized VALIDATION:",
        len(validation_tokens)
    )

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
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    model.config.use_cache = False

    print("Model loaded.")

    print()
    print("Preparing model for QLoRA...")

    model = prepare_model_for_kbit_training(
        model
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

    model = get_peft_model(
        model,
        peft_config
    )

    model.print_trainable_parameters()

    print()
    print("TRAINABLE PARAMETER DTYPES:")

    dtype_counts = {}

    for name, parameter in model.named_parameters():

        if parameter.requires_grad:

            dtype = str(
                parameter.dtype
            )

            dtype_counts[dtype] = (
                dtype_counts.get(dtype, 0)
                + parameter.numel()
            )

    for dtype, count in dtype_counts.items():
        print(
            " ",
            dtype,
            ":",
            count,
            "parameters"
        )

    print()
    print(
        "Creating language-model data collator..."
    )

    # IMPORTANT:
    # This creates normal causal-LM labels.
    # No completion-only masking is used.
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),

        max_steps=MAX_STEPS,

        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,

        gradient_accumulation_steps=4,

        learning_rate=1e-5,

        warmup_steps=2,

        lr_scheduler_type="cosine",

        gradient_checkpointing=True,

        # IMPORTANT:
        # No AMP and therefore no GradScaler.
        fp16=False,
        bf16=False,

        logging_steps=1,

        eval_strategy="steps",
        eval_steps=10,

        save_strategy="steps",
        save_steps=10,
        save_total_limit=1,

        report_to="none",

        seed=42,

        remove_unused_columns=False,
    )

    print()
    print("=" * 72)
    print("STARTING 20-STEP CLEAN SMOKE TEST")
    print("=" * 72)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokens,
        eval_dataset=validation_tokens,
        data_collator=data_collator,
    )

    result = trainer.train()

    print()
    print("=" * 72)
    print("CLEAN SMOKE TEST COMPLETE")
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
    print("Running final smoke evaluation...")

    metrics = trainer.evaluate()

    for key, value in metrics.items():

        print(
            f"{key}: {value}"
        )

    print()
    print("Saving diagnostic adapter...")

    trainer.save_model(
        str(OUTPUT_DIR)
    )

    tokenizer.save_pretrained(
        str(OUTPUT_DIR)
    )

    print()
    print(
        "[OK] Diagnostic adapter:",
        OUTPUT_DIR
    )

    print("=" * 72)
    print("FINAI-V3 CLEAN SMOKE TEST PASSED")
    print("=" * 72)


if __name__ == "__main__":
    main()
