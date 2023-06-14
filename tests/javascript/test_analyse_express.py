import pytest

from static_analysis.javascript.analyse_express import get_express_identifiers
from static_analysis.javascript.analyse_javascript import JS_PARSER


@pytest.mark.parametrize(
    "test_import,expected_identifiers",
    [
        ('import express from "express";', {"express"}),
        ('import * as foo from "express";', {"foo.default"}),
        ('import { default as bar } from "express";', {"bar"}),
        ('import { Request, Response, default as baz } from "express";', {"baz"}),
        ('import express, * as qux from "express";', {"express", "qux.default"}),
        ('import express, { default as quux } from "express";', {"express", "quux"}),
        ('import express, { Request, Response, default as corge } from "express";', {"express", "corge"}),
        # TODO: ('const express = require(\'express\');', {"express"}),
    ],
)
def test_get_express_identifiers(test_import, expected_identifiers):
    parsed_module = JS_PARSER.parse(test_import.encode("utf-8"))

    detected_identifiers = get_express_identifiers(parsed_module)

    assert detected_identifiers == expected_identifiers
