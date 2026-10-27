# Advanced systemic-risk feature status (branch audit)

Audit basis: source files inspected on `feature/finai-runtime-trading-integration`
on 2026-10-27. This is a source-level audit, not a claim that the full test suite
or empirical evaluation has passed. The hardening branch adds a synthetic smoke
validator and this status note; it does not silently replace the implementation.

## Verified implementation boundaries

| Area | What exists in source | What must not be claimed yet |
|---|---|---|
| Directed risk graphs / DAGs | `causal_risk/research_graph.py`, `causal_risk/scm.py`, graph validation and topological execution are used by research counterfactual code. The SCM rejects contemporaneous cycles. | A domain-correct, empirically identified, fully validated causal graph. User-supplied or assumed edges remain assumptions. |
| NOTEARS | `causal_risk/discovery.py::notears_linear` implements a compact linear NOTEARS-style augmented-Lagrangian objective with an acyclicity penalty. | A universally reliable causal discovery result. The implementation is explicitly a bounded research baseline; optimizer convergence and graph recovery need benchmark evidence. |
| DYNOTEARS | `causal_risk/dynamic_discovery.py::discover_lagged_graph` performs lagged Ridge regression and thresholding; its docstring explicitly calls this “DYNOTEARS-style temporal ridge screening” and says full constrained DYNOTEARS remains future work. | Full DYNOTEARS algorithm is active. The current temporal baseline is not the full constrained algorithm. |
| SCM / do-interventions | `causal_risk/scm.py::simulate_scm` executes a linear weighted graph and fixes intervened variables; `causal_risk/research_counterfactual.py` requires explicit graph approval before execution. | General do-calculus, identification of causal effects from observational data, counterfactual validity, or a validated causal inference engine. The code's `do(X=x)` label denotes an intervention-style simulation under the supplied model. |
| Temporal GNN / TGAT-style | `causal_risk/temporal_gnn.py` contains a trainable continuous-time attention layer and training routine. Existing tests exercise a tiny training smoke case. | A production-trained TGAT, predictive superiority, robust generalization, or financial risk forecasting. Tiny smoke training is not empirical validation. |
| GFlowNet | `causal_risk/gfnets.py` contains a trajectory-balance-style research prototype with a train method and scenario sampling. The advanced API exposes train/generate operations; its registry is in memory and the response says model artifacts are not persisted. | Production GFlowNet optimality, durable model serving, or real-world tail-risk fidelity. Training code exists, but validated GFlowNet performance is not established. |
| Multimodal causal knowledge graph | Typed graph primitives, provenance fields, modality fusion, and ingestion adapters exist in `causal_risk/multimodal_graph.py` and `causal_risk/multimodal_ingestion.py`; API endpoints expose ingestion/encoding paths. | A fully integrated, trained, end-to-end multimodal causal knowledge graph whose cross-modal relations are learned and empirically validated. The deterministic fusion primitive is not itself causal learning. |
| Production systemic-risk prediction | Research APIs and synthetic tests exist. Calibration, regime summaries, counterfactuals and tail scenarios have research paths. | Production-grade prediction, investment alpha, validated early warning, regulatory fitness, or safe automated decisions without real timestamped out-of-sample evaluation, baseline comparisons, data-lineage checks, security review and independent reproduction. |

## Pipeline verified from source

`causal_risk/pipeline.py::run_causal_research_pipeline` currently calls, in order:

1. `notears_linear` for a contemporaneous linear graph;
2. `discover_lagged_graph` for lagged Ridge screening;
3. `assess_discovery_stability` across windows;
4. consensus graph construction;
5. empirical edge calibration;
6. regime assignment.

The temporal component is not full DYNOTEARS. The pipeline's ready status means the research computation bundle returned, not that causal identification succeeded. Inspect each component's diagnostics and evidence metadata.

## Validation requirements before stronger claims

- Run `python scripts/validate_advanced_causal_stack.py` in the repository's configured environment and retain the complete JSON output.
- Run the full test suite and frontend build on this branch; capture exact commands, environment and exit codes.
- Test NOTEARS graph recovery on known synthetic DAGs, including cycles/noise, correlated confounding, variable scaling, near-zero edges and convergence failures.
- Test lagged graph recovery on known simulated time series; compare against a full constrained DYNOTEARS implementation before using that name without qualification.
- Verify SCM intervention semantics, graph direction, cycle handling, negative weights, disconnected nodes and intervention nodes not in the graph.
- For TGAT and GFlowNet, record loss curves, seeds, independent runs, held-out scenarios, simple baselines, finite outputs and clean-process model reload behaviour.
- For multimodal features, test provenance retention, missing modalities, conflicting sources, malformed embeddings, node/edge referential integrity and whether causal edges are evidence-backed or merely asserted.
- For systemic risk, use timestamped real data with leakage-safe walk-forward evaluation, stress-period and regime analysis, uncertainty/calibration metrics, naive baselines and independent reproduction.

## Reporting language

Use “implemented research prototype” for source-backed components; “smoke-tested” only after the command/test actually passes; “empirically evaluated” only when the dataset, split, baseline and metrics are documented; and “production-ready” only after operational and security gates are signed off. A source file or unit test alone does not justify a stronger label.
