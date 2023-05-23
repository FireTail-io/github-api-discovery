from typing import Callable
from static_analysis.python import analyse_python

LANGUAGE_ANALYSERS: dict[str, list[Callable[[str, str], list[str]]]] = {"Python": [analyse_python]}


def get_language_analysers(languages: list[str]) -> list[Callable[[str, str], list[str]]]:
    language_analysers: list[Callable[[str, str], list[str]]] = []

    for language in languages:
        if analysers := LANGUAGE_ANALYSERS.get(language):
            language_analysers += analysers

    return language_analysers
