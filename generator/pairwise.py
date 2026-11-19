"""Deterministic greedy pairwise (all-pairs) case selection with exclusion rules."""

import hashlib
import itertools
import json


def matches(case, rule):
    return all(case.get(k) == v for k, v in rule.items())


def is_valid(case, excludes):
    return not any(matches(case, rule) for rule in excludes)


def case_id(case):
    text = json.dumps(case, sort_keys=True)
    return hashlib.sha1(text.encode()).hexdigest()[:8]


def pairwise_cases(parameters, excludes=()):
    """Return a list of dicts that covers every valid value pair at least once.

    Pairs that only occur in invalid combinations are ignored. Output order is
    deterministic for a given input.
    """
    names = list(parameters)
    all_cases = [
        dict(zip(names, values))
        for values in itertools.product(*(parameters[n] for n in names))
    ]
    all_cases = [c for c in all_cases if is_valid(c, excludes)]

    def pairs_of(case):
        return {
            ((a, repr(case[a])), (b, repr(case[b])))
            for a, b in itertools.combinations(names, 2)
        }

    uncovered = set()
    for c in all_cases:
        uncovered |= pairs_of(c)

    selected = []
    while uncovered:
        best = max(all_cases, key=lambda c: len(pairs_of(c) & uncovered))
        selected.append(best)
        uncovered -= pairs_of(best)
    return selected
