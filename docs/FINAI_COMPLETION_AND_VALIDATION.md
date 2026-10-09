# FinAI completion and release-validation plan

This document distinguishes source-code paths from capabilities that still require an
environment, data artifacts, credentials, or experimental evidence.

## Release-blocking sequence

1. **Environment and tests**
   - Create .venv and install requirements.txt.
   - Verify that "python -c" importing sys resolves to the project virtual environment.
   - Run "python -m pytest -q" and record collection errors separately from assertion failures.
   - Run "cd frontend; npm ci; npm run build".
   - Build or restore the ignored TF-IDF router artifact before calling the run a full
     end-to-end test.

2. **End-to-end application**
   - Start the FastAPI backend and Vite frontend.
   - Exercise health, finance calculation, portfolio, market, crypto, RAG, model routing,
     provider fallback, claims verification, and XAI paths through their public APIs.
   - Confirm deterministic financial calculations are never replaced by LLM output.
   - Test timeout, missing credentials, rate limits, malformed provider responses, empty
     outputs and provider failover.

3. **RAG reproducibility**
   - Acquire or generate the domain chunks documented in the README.
   - Build FTS5 and FAISS artifacts from the same corpus/version.
   - Record corpus size, chunk IDs, embedding model/revision, embedding dimension,
     normalization, index build timestamp, and content hashes.
   - Run a versioned evaluation set against lexical, dense and hybrid retrieval. Report
     Recall@k, MRR/nDCG where relevant, latency, and error cases.
   - A small smoke index is not evidence that a production-scale index was built.

4. **Model/provider readiness**
   - Registry entries are metadata, not proof of access. Validate each configured model
     using the provider's current model catalog or a credentialed smoke call.
   - Record success rate, timeout and retry behaviour, cost/latency, structured-output
     quality, language coverage and financial-claim verification results.
   - Never commit API credentials. Keep provider keys in local environment variables.

5. **Research and patent evidence**
   - Run the committed finite-state benchmark and preserve its JSON output.
   - Compare exhaustive enumeration, forward-only screening, bidirectional screening,
     and incremental interval propagation on identical finite-state graphs.
   - Report false-prune rate and high-risk scenario recall as hard correctness gates,
     followed by candidate throughput, total runtime, and number of interval evaluations.
   - Add ablations for each mechanism and multiple seeded graphs; keep synthetic and
     empirical results separate.
   - Validate on chronological holdout periods and compare with unpruned stress sampling.
     Record limitations, failed cases, and data provenance.
   - The prototype/benchmark does not itself prove novelty, inventiveness, non-obviousness,
     real-world risk prediction, or patentability. Conduct a prior-art search and obtain
     qualified patent counsel before filing.

## Optional Calibre probability calibration

The external finite-sample/calibre package provides probability calibrators, including a
centered isotonic method. It requires Python 3.12+ and must not be added to the primary
Python 3.10/3.11 runtime by default.

- Install the optional dependency in an isolated Python 3.12 environment with
  requirements-calibre.txt.
- causal_risk/probability_calibration.py exposes a lazy optional Calibre integration and a
  scikit-learn isotonic fallback for the normal project environment.
- Fit calibration on held-out or out-of-fold predictions only.
- Evaluate on a separate untouched test period using Brier score, equal-mass ECE,
  calibration-in-the-large, and distinct-probability counts.
- The helper does not automatically change production decisions. It must not be treated
  as validated until tested on labelled, chronological financial outcomes.

## Optional Ollama local LLM

The Ollama adapter is opt-in. Set OLLAMA_MODEL to a model already pulled into the local
Ollama service; OLLAMA_BASE_URL defaults to http://127.0.0.1:11434.
A qwen3:4b model is a proposed starting point for constrained local hardware, but RAM/VRAM,
quantization and response quality must be measured on the target machine. Local model
output should continue through FinAI's existing authority and verification layers.

## Completion definition

FinAI should not be called release-ready until the same release candidate passes backend
regression, frontend build, API end-to-end checks, provider error-path tests, reproducible
RAG evaluation, and the defined research benchmark. Missing credentials or data artifacts
must be listed as explicit external prerequisites rather than reported as successful tests.
