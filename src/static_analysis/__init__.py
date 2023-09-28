from typing import Callable

from static_analysis.golang.analyse_golang import analyse_golang
from static_analysis.javascript.analyse_javascript import analyse_javascript
from static_analysis.python.analyse_python import analyse_python

ANALYSER_TYPE = Callable[[str, str], tuple[set[str], dict[str, dict[str, dict]]]]

LANGUAGE_ANALYSERS: dict[str, list[ANALYSER_TYPE]] = {
    "Python": [analyse_python],
    "Go": [analyse_golang],
    "JavaScript": [analyse_javascript],
}


def get_language_analysers(languages: list[str]) -> list[ANALYSER_TYPE]:
    language_analysers: list[ANALYSER_TYPE] = []

    for language in languages:
        if analysers := LANGUAGE_ANALYSERS.get(language):
            language_analysers += analysers

    return language_analysers
