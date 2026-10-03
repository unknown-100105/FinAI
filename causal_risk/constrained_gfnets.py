"""GFlowNet-style stress generation with causal-feasibility action masking."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import torch

from causal_risk.bidirectional_feasibility import backward_target_cone
from causal_risk.feasibility_pruning import (
    AdaptivePruningController,
    evaluate_prefix_feasibility,
)
from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator


class CausalConstrainedTailGenerator:
    """Research wrapper coupling GFlowNet-style generation to causal certificates.

    Training uses the existing GFlowNet research generator. Generation evaluates
    every candidate action with a cheap prefix certificate and masks actions that
    cannot reach the configured terminal target interval. Optional adaptive
    pruning is heuristic and must be evaluated against an unpruned baseline.
    """

    def __init__(self, factor_ids: Sequence[str], config: GFlowConfig | None = None) -> None:
        labels = tuple(str(value) for value in factor_ids)
        if not labels or len(set(labels)) != len(labels):
            raise ValueError("factor_ids must be non-empty and unique")
        self.factor_ids = labels
        self.generator = GFlowNetTailGenerator(len(labels), config)

    def train(self, *, reward_fn: Any | None = None, objective_name: str = "synthetic_tail_reward", device: str | None = None) -> dict[str, Any]:
        return self.generator.train(
            reward_fn=reward_fn,
            objective_name=objective_name,
            device=device,
        )

    def sample(
        self,
        center: Mapping[str, float],
        *,
        nodes: Sequence[str],
        edges: Sequence[Mapping[str, Any]],
        node_bounds: Mapping[str, Sequence[float]],
        target_node: str,
        target_interval: Sequence[float],
        scale: float = 0.35,
        draws: int = 64,
        seed: int = 42,
        controller: AdaptivePruningController | None = None,
        empirical_center: Mapping[str, float] | None = None,
        empirical_scale: Mapping[str, float] | None = None,
        use_bidirectional_feasibility: bool = True,
    ) -> dict[str, Any]:
        if not self.generator.trained:
            raise RuntimeError("GFlowNet prototype must be trained before constrained sampling")
        if draws < 1 or draws > 5000:
            raise ValueError("draws must be between 1 and 5000")
        keys = tuple(sorted(center))
        if keys != tuple(sorted(self.factor_ids)):
            raise ValueError("center keys must match factor_ids")
        if scale <= 0:
            raise ValueError("scale must be positive")

        device = torch.device(self.generator.device or "cpu")
        local_generator = torch.Generator(device=device).manual_seed(seed)
        levels = self.generator.levels.to(device)

        trajectories: list[dict[str, float]] = []
        certificate_counts = {
            "candidates": 0,
            "bidirectional_pruned": 0,
            "hard_pruned": 0,
            "adaptive_pruned": 0,
            "accepted": 0,
            "forward_certificate_evaluations": 0,
        }
        backward_required: dict[str, tuple[float, float]] = {}
        if use_bidirectional_feasibility:
            backward_result = backward_target_cone(
                nodes,
                edges,
                node_bounds,
                target_node=target_node,
                target_interval=target_interval,
            )
            backward_required = {
                str(node): (float(interval[0]), float(interval[1]))
                for node, interval in backward_result["required_intervals"].items()
            }

        with torch.no_grad():
            for draw_index in range(draws):
                state = torch.zeros((1, len(keys)), dtype=torch.float32, device=device)
                prefix: dict[str, float] = {}
                for step, factor in enumerate(keys):
                    logits = self.generator.policy(state, step)
                    probs = torch.softmax(logits, dim=-1).squeeze(0)

                    candidate_probs: list[float] = []
                    candidate_certificates: list[dict[str, Any]] = []
                    for action_index, level in enumerate(self.generator.config.levels):
                        candidate_value = float(center[factor]) + float(level) * max(abs(float(center[factor])) * scale, 5.0)
                        candidate_prefix = dict(prefix)
                        candidate_prefix[factor] = candidate_value
                        certificate_counts["candidates"] += 1

                        backward_pruned = False
                        backward_reason = ""
                        required_lo = required_hi = 0.0
                        if use_bidirectional_feasibility and factor in backward_required:
                            required_lo, required_hi = backward_required[factor]
                            if required_lo > required_hi:
                                backward_pruned = True
                                backward_reason = f"{factor} has an empty necessary interval"
                            elif candidate_value < required_lo or candidate_value > required_hi:
                                backward_pruned = True
                                backward_reason = (
                                    f"{factor}={candidate_value:.6f} is outside the "
                                    f"necessary interval [{required_lo:.6f},{required_hi:.6f}]"
                                )
                        if backward_pruned:
                            certificate_counts["bidirectional_pruned"] += 1
                            candidate_certificates.append({
                                "target_node": target_node,
                                "hard_infeasible": True,
                                "margin": float("-inf"),
                                "reason": backward_reason,
                                "certificate_type": "backward_necessary_interval",
                                "required_interval": [required_lo, required_hi],
                            })
                            candidate_probs.append(0.0)
                            continue

                        certificate = evaluate_prefix_feasibility(
                            nodes,
                            edges,
                            candidate_prefix,
                            node_bounds,
                            target_node=target_node,
                            target_interval=target_interval,
                            empirical_center=empirical_center,
                            empirical_scale=empirical_scale,
                        )
                        certificate_counts["forward_certificate_evaluations"] += 1
                        hard = certificate.hard_infeasible
                        heuristic = (
                            controller is not None
                            and not hard
                            and certificate.margin < controller.current_margin
                        )
                        if hard:
                            certificate_counts["hard_pruned"] += 1
                        elif heuristic:
                            certificate_counts["adaptive_pruned"] += 1
                        else:
                            certificate_counts["accepted"] += 1
                        candidate_certificates.append(certificate.as_dict())
                        candidate_probs.append(
                            0.0 if (hard or heuristic) else float(probs[action_index].item())
                        )

                    probabilities = np.asarray(candidate_probs, dtype=float)
                    total_probability = float(probabilities.sum())
                    if total_probability <= 0.0:
                        raise ValueError(
                            f"no feasible next action for factor {factor}; all candidates were pruned"
                        )
                    probabilities /= total_probability
                    action_index = int(
                        torch.multinomial(
                            torch.tensor(probabilities, dtype=torch.float32, device=device),
                            1,
                            generator=local_generator,
                        ).item()
                    )
                    chosen_level = float(self.generator.config.levels[action_index])
                    chosen_value = float(center[factor]) + chosen_level * max(abs(float(center[factor])) * scale, 5.0)
                    prefix[factor] = chosen_value
                    state[:, step] = float(chosen_level)

                trajectories.append({key: round(float(prefix[key]), 3) for key in keys})

        return {
            "status": "CAUSALLY_CONSTRAINED_TRAJECTORIES_READY",
            "draws": draws,
            "seed": seed,
            "factors": list(keys),
            "trajectories": trajectories,
            "screening": {
                **certificate_counts,
                "bidirectional_feasibility_enabled": use_bidirectional_feasibility,
                "bidirectional_pruning_is_necessary_condition": True,
                "hard_pruning_is_conservative": True,
                "hard_pruning_certificate": "linear_dag_interval_outer_bound",
                "adaptive_pruning_is_heuristic": controller is not None,
                "baseline_candidate_evaluations": certificate_counts["candidates"],
                "screened_candidate_evaluations": certificate_counts["accepted"],
                "candidate_evaluations_avoided": (
                    certificate_counts["bidirectional_pruned"]
                    + certificate_counts["hard_pruned"]
                    + certificate_counts["adaptive_pruned"]
                ),
                "screening_fraction": (
                    certificate_counts["accepted"] / certificate_counts["candidates"]
                    if certificate_counts["candidates"]
                    else 0.0
                ),
            },
            "semantics": (
                "Research coupling of a GFlowNet-style trajectory policy with "
                "causal-feasibility action masking. Full SCM/tail validation is "
                "still required for final trajectories."
            ),
        }
