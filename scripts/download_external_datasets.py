import json
from pathlib import Path

from datasets import load_dataset


ROOT = Path(__file__).resolve().parent.parent

OUTPUT_ROOT = ROOT / "data" / "external"


DATASETS = {
    "finllm_india": {
        "name": "TaanishChauhan/finllm-india",
        "split": "train",
    },
    "indian_financial_news": {
        "name": "kdave/Indian_Financial_News",
        "split": "train",
    },
}


def download_dataset(key, config):
    name = config["name"]
    split = config["split"]

    output_dir = OUTPUT_ROOT / key
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "full.jsonl"

    print("\n" + "=" * 80)
    print("DATASET")
    print("=" * 80)
    print("Name :", name)
    print("Split:", split)
    print("Output:", output_file)

    print("\nLoading dataset...")

    dataset = load_dataset(
        name,
        split=split,
    )

    print("Rows:", len(dataset))
    print("Columns:", dataset.column_names)

    print("\nSaving complete dataset...")

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as f:

        for index, record in enumerate(dataset):

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

            if (index + 1) % 5000 == 0:
                print(
                    f"Saved {index + 1}/{len(dataset)}"
                )

    print("\nSaved successfully:")
    print(output_file)

    return len(dataset)


def main():

    print("=" * 80)
    print("FINAI EXTERNAL DATASET DOWNLOAD")
    print("=" * 80)

    total = 0

    for key, config in DATASETS.items():

        try:

            count = download_dataset(
                key,
                config,
            )

            total += count

        except Exception as error:

            print("\nFAILED:")
            print("Dataset:", config["name"])
            print("Error:", type(error).__name__)
            print(error)

            print(
                "\nThe other datasets will continue."
            )

    print("\n" + "=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)

    print("Total rows downloaded:", total)

    print("\nFiles:")

    for path in OUTPUT_ROOT.rglob("full.jsonl"):
        print(" ", path)


if __name__ == "__main__":
    main()