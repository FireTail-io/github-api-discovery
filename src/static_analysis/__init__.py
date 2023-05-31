from typing import Callable

from static_analysis.python.analyse_python import analyse_python

ANALYSER_TYPE = Callable[[str, str], tuple[set[str], dict[str, list[str]]]]

LANGUAGE_ANALYSERS: dict[str, list[ANALYSER_TYPE]] = {"Python": [analyse_python]}


def get_language_analysers(languages: list[str]) -> list[ANALYSER_TYPE]:
    language_analysers: list[ANALYSER_TYPE] = []

    for language in languages:
        if analysers := LANGUAGE_ANALYSERS.get(language):
            language_analysers += analysers

    return language_analysers
