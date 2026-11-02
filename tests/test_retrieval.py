import math
import unittest

from water_ai_research.metrics import retrieval_metrics
from water_ai_research.retrieval import BM25, mmr_select, rank_scores, reciprocal_rank_fusion


class RetrievalTests(unittest.TestCase):
    def test_bm25_hand_computed(self):
        # Equal document lengths -> denominator tf + k1. Rare x: df=1,N=2.
        scores = BM25(["x a", "a b"]).score("x x")
        self.assertAlmostEqual(scores[0], math.log(2))
        self.assertEqual(scores[1], 0)

    def test_bm25_empty_and_unknown(self):
        self.assertEqual(BM25([]).score("x"), [])
        self.assertEqual(BM25(["", ""]).score("x"), [0, 0])
        self.assertEqual(BM25(["a"]).score("z"), [0])

    def test_custom_tokenizer(self):
        self.assertGreater(BM25(["降雨径流"], tokenizer=list).score("径流")[0], 0)

    def test_ranking_ties_and_rejection(self):
        self.assertEqual(rank_scores([1, 1, 2]), [2, 0, 1])
        self.assertEqual(rank_scores([1], 0), [])
        for values in [[float("nan")], [float("inf")]]:
            with self.assertRaises(ValueError):
                rank_scores(values)
        with self.assertRaises(ValueError):
            rank_scores([1], -1)

    def test_rrf_one_based_incomplete_and_ties(self):
        result = reciprocal_rank_fusion([["a", "b"], ["b", "a", "c"]])
        self.assertEqual([i for i, _ in result], ["a", "b", "c"])
        self.assertAlmostEqual(result[0][1], 1 / 61 + 1 / 62)
        self.assertAlmostEqual(result[2][1], 1 / 63)

    def test_rrf_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            reciprocal_rank_fusion([["a", "a"]])

    def test_mmr_relevance_endpoint(self):
        trace = mmr_select([1, 0.9, 0.8], [[1, 1, 0], [1, 1, 0], [0, 0, 1]], weight=1)
        self.assertEqual([step.index for step in trace], [0, 1, 2])

    def test_mmr_diversity_endpoint_and_trace(self):
        trace = mmr_select([1, 0.9, 0.8], [[1, 1, 0], [1, 1, 0], [0, 0, 1]], weight=0)
        self.assertEqual([step.index for step in trace], [0, 2, 1])
        self.assertEqual(trace[2].redundancy, 1)
        self.assertEqual(trace[2].gain, -1)

    def test_mmr_invalid_shapes_and_nonfinite(self):
        for relevance, similarity in [([1], []), ([1], [[float("nan")]])]:
            with self.assertRaises(ValueError):
                mmr_select(relevance, similarity)
        self.assertEqual(mmr_select([], []), [])

    def test_metric_missing_gold_and_reciprocal_rank(self):
        result = retrieval_metrics(["x", "a", "b"], {"a", "missing"}, k=2)
        self.assertEqual(result["recall_at_k"], 0.5)
        self.assertEqual(result["reciprocal_rank"], 0.5)
        self.assertEqual(result["all_gold_at_k"], 0)

    def test_empty_gold_is_unscored(self):
        self.assertIsNone(retrieval_metrics(["a"], set()))
        result = retrieval_metrics([], {"a"})
        self.assertEqual(result["recall_at_k"], 0)
        self.assertEqual(result["reciprocal_rank"], 0)

    def test_metric_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            retrieval_metrics(["a", "a"], {"a"})


if __name__ == "__main__":
    unittest.main()
