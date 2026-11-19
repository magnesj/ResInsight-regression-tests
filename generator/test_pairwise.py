import itertools

from pairwise import case_id, is_valid, pairwise_cases

PARAMS = {"a": [1, 2, 3], "b": ["x", "y"], "c": [True, False]}


def test_all_valid_pairs_covered():
    cases = pairwise_cases(PARAMS)
    for (n1, v1s), (n2, v2s) in itertools.combinations(PARAMS.items(), 2):
        for v1 in v1s:
            for v2 in v2s:
                assert any(c[n1] == v1 and c[n2] == v2 for c in cases)
    assert len(cases) < 12


def test_excludes_respected_and_deterministic():
    excludes = [{"a": 1, "b": "x"}]
    cases = pairwise_cases(PARAMS, excludes)
    assert all(is_valid(c, excludes) for c in cases)
    assert cases == pairwise_cases(PARAMS, excludes)


def test_case_id_stable_and_order_independent():
    assert case_id({"a": 1, "b": 2}) == case_id({"b": 2, "a": 1})
