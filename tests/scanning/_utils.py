import itertools
from typing import TypeVar

T = TypeVar("T")


def powerset(universe: set[T]) -> set[tuple[T, ...]]:
    # Why itertools doesn't come with this built in, I don't know? ¯\_(ツ)_/¯
    return set(itertools.chain.from_iterable([itertools.combinations(universe, n) for n in range(len(universe) + 1)]))
