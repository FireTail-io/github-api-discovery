from typing import Callable
from static_analysis.python import identify_frameworks as identify_python_frameworks

LANGUAGE_ANALYSERS: dict[str, list[Callable[[str, str], list[str]]]] = {"Python": [identify_python_frameworks]}


def get_language_analysers(languages: list[str]) -> list[Callable[[str, str], list[str]]]:
    language_analysers: list[Callable[[str, str], list[str]]] = []

    for language in languages:
        if analysers := LANGUAGE_ANALYSERS.get(language):
            language_analysers += analysers

    return language_analysers
