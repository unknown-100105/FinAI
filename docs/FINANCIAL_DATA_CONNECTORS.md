# Financial data connectors and model-training workflow

FinAI includes **read-only** adapters for Financial Datasets and Longbridge. The ingestion path does not place orders or write to an external brokerage account. Raw provider data and generated training files stay local by default.

## 1. Credentials

Copy .env.example to .env and configure only the provider(s) you are entitled to use:

- Financial Datasets: FINANCIAL_DATASETS_API_KEY and optionally FINANCIAL_DATASETS_BASE_URL.
- Longbridge OpenAPI: LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, and LONGBRIDGE_ACCESS_TOKEN. The SDK may require account/region settings based on your Longbridge setup.

Restart the API/scripts after changing environment values. Shell/CI environment variables take precedence over .env. Never store real credentials in source control, notebooks, logs, or dataset rows.

## 2. Ingest provider records

From the repository root with .venv active and dependencies installed:

~~~powershell
python scripts/ingest_finance_api_data.py --providers financial_datasets --tickers AAPL.US,NVDA.US,MSFT.US
~~~

Or use Longbridge for supported securities:

~~~powershell
python scripts/ingest_finance_api_data.py --providers longbridge --tickers AAPL.US,700.HK
~~~

To combine both providers, use --providers financial_datasets,longbridge. By default the script requests roughly the most recent two years and writes:

- data/raw/finance_api/records.jsonl: normalized provider records with source, dates/currency fields where available and fetch metadata.
- data/raw/finance_api/manifest.json: requested ticker/provider/date ranges, counts, failures and a license-use notice.

Optional switches: --start-date YYYY-MM-DD, --end-date YYYY-MM-DD, --output-dir PATH, --include-news, and --include-facts (Financial Datasets only; adds a request per ticker). A provider can return per-ticker errors while other requested records succeed; always inspect the manifest and error count before using an ingest.

## 3. Build historical-fact SFT examples

~~~powershell
python scripts/build_finance_api_sft.py
~~~

The default input is data/raw/finance_api/records.jsonl; output is data/sft_v3_work/provider_finance/finance_sft.jsonl, plus finance_sft_manifest.json. The builder creates examples from recognized historical financial-statement metrics, deduplicates source agreement, and excludes conflicting values rather than deciding which provider is correct. The manifest records excluded conflicts.

Review the example file and conflict manifest before training. These examples describe historical reported values, not live quotes or forecasts.

## 4. Add the curated data to the existing trainer

Run the small smoke path first, after the Sarvam base model and Python/GPU dependencies are provisioned:

~~~powershell
python scripts/train_finai_v3_final.py --smoke --extra-train-file data/sft_v3_work/provider_finance/finance_sft.jsonl
~~~

The script deliberately accepts repeated --extra-train-file options. Smoke mode uses a bounded, seeded sample and reserves up to 50 examples from the added provider file when available. Full model training is a separate, resource-intensive action:

~~~powershell
python scripts/train_finai_v3_final.py --full --extra-train-file data/sft_v3_work/provider_finance/finance_sft.jsonl
~~~

Training can download/load gigabytes of model weights and use substantial GPU memory. Do not run full training as part of ordinary CI or a user-facing API call. The script's training split is not a substitute for a temporal/ticker holdout: assess leakage and performance on companies and periods not used to create training examples before claiming quality improvements.

## 5. Use Longbridge in the market API

When the three Longbridge environment variables are present before FinAI starts, the market service registers the Longbridge provider while keeping yfinance as the default. Check the registered set with:

~~~text
GET /api/v1/market/providers
~~~

Quote/history/analytics endpoints accept provider=yfinance or provider=longbridge, for example:

~~~text
GET /api/v1/market/quote?instrument=AAPL&provider=longbridge
GET /api/v1/market/history?instrument=AAPL&start=2025-01-01T00:00:00Z&end=2026-01-01T00:00:00Z&interval=1d&provider=longbridge
~~~

Longbridge history in this adapter supports daily, weekly, and monthly candles only. Market coverage depends on the account and Longbridge's supported venues; the app rejects known Indian NSE/BSE registry instruments for this provider rather than silently routing them to a different feed. Market search, news, and overall gainers/losers remain yfinance-sourced.

## Data licensing and validation boundary

Before using provider data in training, external demos or redistributed products, read the current data-provider terms, attribution requirements, retention, and machine-learning/training permissions for your account. Availability of an API response does not grant redistribution rights. Raw records and generated SFT files are under the ignored data/ tree and must not be committed.

These adapters have mocked regression tests; that does not prove current credentials, subscription entitlements, API quotas, the Longbridge account region, or current provider responses work. Run a small, authorized ingestion and review its manifest on your own machine before training.
