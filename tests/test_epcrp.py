import json
import unittest

from finance_engine.epcrp import EvidenceEdge, EvidenceGatedRiskGraph, RiskNode


class EPCRPTests(unittest.TestCase):
    def setUp(self):
        self.graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode("rate"), RiskNode("bond"), RiskNode("portfolio")],
            edges=[
                EvidenceEdge("rate", "bond", -2.0, "E-RATE-BOND", support_score=0.95),
                EvidenceEdge("bond", "portfolio", 0.5, "E-BOND-PORT", support_score=0.90),
            ],
            model_version="test-model-v1",
        )

    def test_paired_world_delta_and_lineage(self):
        result = self.graph.run_counterfactual(
            source_values={"rate": 10.0}, interventions={"rate": 12.0},
            portfolio_exposures={"portfolio": 1.0}, as_of="2026-10-13T10:00:00Z",
        )
        self.assertAlmostEqual(result.baseline["portfolio"], -10.0)
        self.assertAlmostEqual(result.counterfactual["portfolio"], -12.0)
        self.assertAlmostEqual(result.portfolio_delta, -2.0)
        self.assertEqual(result.evidence_by_output["portfolio"],
                         ("E-BOND-PORT", "E-RATE-BOND"))

    def test_unvalidated_and_missing_evidence_edges_are_excluded(self):
        graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode("A"), RiskNode("B")],
            edges=[
                EvidenceEdge("A", "B", 5.0, "NOT-USED", validated=False),
                EvidenceEdge("A", "B", 3.0, "", support_score=0.99),
            ],
        )
        result = graph.run_counterfactual(
            source_values={"A": 1.0}, interventions={"A": 2.0},
            portfolio_exposures={"B": 1.0}, as_of="2026-10-13T00:00:00Z",
        )
        self.assertAlmostEqual(result.portfolio_delta, 0.0)
        self.assertEqual(set(result.rejected_edges.values()),
                         {"edge_not_validated", "missing_evidence_id"})

    def test_regime_and_time_window_gates(self):
        graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode("A"), RiskNode("B"), RiskNode("C")],
            edges=[
                EvidenceEdge("A", "B", 2.0, "CRISIS", regime="crisis"),
                EvidenceEdge("A", "C", 3.0, "FUTURE",
                             valid_from="2027-01-01T00:00:00Z"),
            ],
        )
        result = graph.run_counterfactual(
            source_values={"A": 1.0}, interventions={"A": 2.0},
            portfolio_exposures={"B": 1.0, "C": 1.0}, regime="normal",
            as_of="2026-10-13T00:00:00Z",
        )
        self.assertIn("regime_mismatch", result.rejected_edges.values())
        self.assertIn("before_validity_window", result.rejected_edges.values())
        self.assertEqual(result.portfolio_delta, 0.0)

    def test_cycle_is_rejected(self):
        graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode("A"), RiskNode("B")],
            edges=[EvidenceEdge("A", "B", 1.0, "AB"),
                   EvidenceEdge("B", "A", 1.0, "BA")],
        )
        with self.assertRaisesRegex(ValueError, "acyclic"):
            graph.run_counterfactual(
                source_values={}, interventions={"A": 1.0},
                portfolio_exposures={"B": 1.0}, as_of="2026-10-13T00:00:00Z",
            )

    def test_direct_intervention_does_not_claim_incoming_edge_causation(self):
        graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode("A"), RiskNode("B")],
            edges=[EvidenceEdge("A", "B", 9.0, "EDGE-INTO-B")],
        )
        result = graph.run_counterfactual(
            source_values={"A": 1.0}, interventions={"B": 5.0},
            portfolio_exposures={"B": 1.0}, as_of="2026-10-13T00:00:00Z",
        )
        self.assertAlmostEqual(result.portfolio_delta, 4.0)
        self.assertEqual(result.evidence_by_output["B"], ())

    def test_uncertainty_is_seeded_and_json_serializable(self):
        kwargs = dict(
            source_values={"rate": 10.0}, interventions={"rate": 11.0},
            portfolio_exposures={"portfolio": 1.0},
            as_of="2026-10-13T00:00:00Z", uncertainty_samples=100, seed=41,
        )
        first, second = self.graph.run_counterfactual(**kwargs), self.graph.run_counterfactual(**kwargs)
        self.assertEqual(first.uncertainty_interval, second.uncertainty_interval)
        self.assertLessEqual(first.uncertainty_interval[0], first.uncertainty_interval[1])
        json.dumps(first.to_dict())

    def test_invalid_nodes_and_timestamps_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown node"):
            self.graph.run_counterfactual(
                source_values={"UNKNOWN": 1.0}, interventions={"rate": 2.0},
                portfolio_exposures={"portfolio": 1.0}, as_of="2026-10-13T00:00:00Z",
            )
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            self.graph.run_counterfactual(
                source_values={}, interventions={"rate": 2.0},
                portfolio_exposures={"portfolio": 1.0}, as_of="not-a-date",
            )

    def test_repeat_run_manifest_is_reproducible(self):
        kwargs = dict(
            source_values={"rate": 10.0}, interventions={"rate": 11.0},
            portfolio_exposures={"portfolio": 1.0}, as_of="2026-10-13T00:00:00Z",
        )
        self.assertEqual(
            self.graph.run_counterfactual(**kwargs).manifest,
            self.graph.run_counterfactual(**kwargs).manifest,
        )


if __name__ == "__main__":
    unittest.main()
