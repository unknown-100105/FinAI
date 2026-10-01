from pathlib import Path
import argparse
import torch

from datasets import load_dataset, concatenate_datasets
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
)
from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
    get_peft_model,
)


ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "final_training_v3"
    / "train.jsonl"
)

NORMAL_VALIDATION_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "final_split_v2"
    / "validation.jsonl"
)

ROUTER_EVAL_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_eval_v3.jsonl"
)

BASE_MODEL = "sarvamai/sarvam-1"

FULL_OUTPUT = (
    ROOT
    / "models"
    / "finai-v3-final"
)

SMOKE_OUTPUT = (
    ROOT
    / "models"
    / "finai-v3-final-smoke"
)

MAX_LENGTH = 1024


def build_completion_example(example, tokenizer):

    prompt = str(
        example.get("prompt", "")
    ).strip()

    completion = str(
        example.get("completion", "")
    ).strip()

    prompt_ids = tokenizer(
        prompt,
        add_special_tokens=True,
        truncation=False,
    )["input_ids"]

    completion_ids = tokenizer(
        completion,
        add_special_tokens=False,
        truncation=False,
    )["input_ids"]

    eos_id = tokenizer.eos_token_id

    if eos_id is not None:
        completion_ids = (
            completion_ids
            + [eos_id]
        )

    # Make sure completion always gets space.
    if len(completion_ids) >= MAX_LENGTH:

        completion_ids = completion_ids[
            :MAX_LENGTH
        ]

        if (
            eos_id is not None
            and completion_ids[-1] != eos_id
        ):
            completion_ids[-1] = eos_id

        prompt_ids = []

    else:

        prompt_budget = (
            MAX_LENGTH
            - len(completion_ids)
        )

        if len(prompt_ids) > prompt_budget:

            # Preserve the beginning marker
            # and the end containing the user request.
            prefix_keep = min(
                128,
                prompt_budget
            )

            suffix_keep = (
                prompt_budget
                - prefix_keep
            )

            if suffix_keep > 0:

                prompt_ids = (
                    prompt_ids[:prefix_keep]
                    +
                    prompt_ids[-suffix_keep:]
                )

            else:

                prompt_ids = prompt_ids[
                    :prompt_budget
                ]

    input_ids = (
        prompt_ids
        + completion_ids
    )

    attention_mask = [
        1
        for _ in input_ids
    ]

    labels = (
        [-100] * len(prompt_ids)
        +
        completion_ids
    )

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


class CompletionCollator:

    def __init__(self, tokenizer):

        self.tokenizer = tokenizer

        self.pad_id = (
            tokenizer.pad_token_id
            if tokenizer.pad_token_id is not None
            else tokenizer.eos_token_id
        )

    def __call__(self, features):

        max_len = max(
            len(x["input_ids"])
            for x in features
        )

        input_ids = []
        attention_masks = []
        labels = []

        for feature in features:

            length = len(
                feature["input_ids"]
            )

            padding = (
                max_len
                - length
            )

            input_ids.append(
                feature["input_ids"]
                +
                [self.pad_id] * padding
            )

            attention_masks.append(
                feature["attention_mask"]
                +
                [0] * padding
            )

            labels.append(
                feature["labels"]
                +
                [-100] * padding
            )

        return {
            "input_ids": torch.tensor(
                input_ids,
                dtype=torch.long,
            ),
            "attention_mask": torch.tensor(
                attention_masks,
                dtype=torch.long,
            ),
            "labels": torch.tensor(
                labels,
                dtype=torch.long,
            ),
        }



def load_and_prepare(
    tokenizer,
    smoke=False,
):

    # IMPORTANT:
    # Load each JSON file separately.
    # They do NOT have identical schemas, so they cannot be
    # passed together to one load_dataset() call.

    train_ds = load_dataset(
        "json",
        data_files=str(TRAIN_FILE),
    )["train"]

    normal_eval = load_dataset(
        "json",
        data_files=str(NORMAL_VALIDATION_FILE),
    )["train"]

    router_all = load_dataset(
        "json",
        data_files=str(ROUTER_EVAL_FILE),
    )["train"]

    router_eval = router_all.filter(
        lambda x:
        x.get("eval_split") == "validation"
    )

    print()
    print("RAW TRAIN RECORDS:", len(train_ds))
    print("RAW NORMAL VALIDATION:", len(normal_eval))
    print("RAW ROUTER VALIDATION:", len(router_eval))

    # Normalize evaluation schemas BEFORE concatenation.
    #
    # Normal validation comes from the older dataset format:
    #   user / assistant
    #
    # Router validation already uses:
    #   prompt / completion
    #
    # Convert both to exactly the same schema.

    normal_eval = normal_eval.map(
        lambda x: {
            "prompt": str(
                x.get("user", "")
            ),
            "completion": str(
                x.get("assistant", "")
            ),
        },
        remove_columns=normal_eval.column_names,
        desc="Converting normal validation format",
    )

    router_eval = router_eval.select_columns(
        ["prompt", "completion"]
    )

    # Smoke-test subsets.
    if smoke:

        train_ds = train_ds.select(
            range(
                min(500, len(train_ds))
            )
        )

        normal_eval = normal_eval.select(
            range(
                min(100, len(normal_eval))
            )
        )

        router_eval = router_eval.select(
            range(
                min(100, len(router_eval))
            )
        )

    eval_ds = concatenate_datasets(
        [
            normal_eval,
            router_eval,
        ]
    )

    print()
    print("TRAIN RECORDS:", len(train_ds))
    print("NORMAL VALIDATION:", len(normal_eval))
    print("ROUTER VALIDATION:", len(router_eval))
    print("COMBINED VALIDATION:", len(eval_ds))

    train_tokens = train_ds.map(
        lambda x:
        build_completion_example(
            x,
            tokenizer
        ),
        remove_columns=train_ds.column_names,
        desc="Tokenizing training data",
    )

    eval_tokens = eval_ds.map(
        lambda x:
        build_completion_example(
            x,
            tokenizer
        ),
        remove_columns=eval_ds.column_names,
        desc="Tokenizing validation data",
    )

    return (
        train_tokens,
        eval_tokens,
    )


def build_model():

    print()
    print("Loading 4-bit QLoRA model...")

    quantization_config = (
        BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    )

    model = (
        AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
    )

    model.config.use_cache = False

    print(
        "Model loaded."
    )

    model = (
        prepare_model_for_kbit_training(
            model
        )
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
        peft_config,
    )

    model.print_trainable_parameters()

    return model


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run 100-step smoke test",
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full training",
    )

    args = parser.parse_args()

    if not args.smoke and not args.full:

        raise SystemExit(
            "Use --smoke or --full"
        )

    smoke = args.smoke

    output_dir = (
        SMOKE_OUTPUT
        if smoke
        else FULL_OUTPUT
    )

    print("=" * 72)

    if smoke:
        print(
            "FINAI-V3 FINAL TRAINER - SMOKE TEST"
        )
    else:
        print(
            "FINAI-V3 FINAL TRAINER - FULL TRAINING"
        )

    print("=" * 72)

    print()
    print(
        "CUDA:",
        torch.cuda.is_available()
    )

    if torch.cuda.is_available():

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            TRAIN_FILE
        )

    if not NORMAL_VALIDATION_FILE.exists():
        raise FileNotFoundError(
            NORMAL_VALIDATION_FILE
        )

    if not ROUTER_EVAL_FILE.exists():
        raise FileNotFoundError(
            ROUTER_EVAL_FILE
        )

    print()
    print("Loading tokenizer...")

    tokenizer = (
        AutoTokenizer.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
        )
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = (
            tokenizer.eos_token
        )

    print(
        "Tokenizer loaded."
    )

    train_dataset, eval_dataset = (
        load_and_prepare(
            tokenizer,
            smoke=smoke,
        )
    )

    model = build_model()

    data_collator = (
        CompletionCollator(
            tokenizer
        )
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if smoke:

        max_steps = 100
        eval_steps = 50
        save_steps = 50
        logging_steps = 5

    else:

        max_steps = -1
        eval_steps = 1000
        save_steps = 1000
        logging_steps = 20

    training_args = TrainingArguments(

        output_dir=str(
            output_dir
        ),

        num_train_epochs=1,

        max_steps=max_steps,

        per_device_train_batch_size=1,

        per_device_eval_batch_size=1,

        gradient_accumulation_steps=8,

        learning_rate=1e-5,

        weight_decay=0.01,

        warmup_steps=(3 if smoke else 500),

        lr_scheduler_type="cosine",

        optim="paged_adamw_8bit",

        gradient_checkpointing=True,

        # IMPORTANT:
        # Keep AMP disabled because the previous
        # environment produced a BF16 GradScaler error.
        fp16=False,
        bf16=False,

        logging_strategy="steps",
        logging_steps=logging_steps,

        eval_strategy="steps",
        eval_steps=eval_steps,

        save_strategy="steps",
        save_steps=save_steps,

        save_total_limit=2,

        load_best_model_at_end=False,

        report_to="none",

        seed=42,

        remove_unused_columns=False,

        dataloader_num_workers=0,

    )

    print()
    print("=" * 72)

    if smoke:
        print(
            "STARTING 100-STEP FINAL V3 SMOKE TEST"
        )
    else:
        print(
            "STARTING FULL V3 TRAINING"
        )

    print("=" * 72)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    result = trainer.train()

    print()
    print("=" * 72)

    if smoke:
        print(
            "FINAL V3 SMOKE TEST COMPLETE"
        )
    else:
        print(
            "FINAL V3 TRAINING COMPLETE"
        )

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
    print("FINAL EVALUATION...")

    metrics = trainer.evaluate()

    for key, value in metrics.items():

        print(
            f"{key}: {value}"
        )

    print()
    print("Saving adapter...")

    trainer.save_model(
        str(output_dir)
    )

    tokenizer.save_pretrained(
        str(output_dir)
    )

    print()
    print(
        "[OK] Output:",
        output_dir
    )

    print("=" * 72)

    if smoke:
        print(
            "FINAI-V3 FINAL SMOKE TEST PASSED"
        )
    else:
        print(
            "FINAI-V3 FULL TRAINING PASSED"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()
