import pytest

from static_analysis.javascript.analyse_javascript import JS_PARSER, get_imports


@pytest.mark.parametrize(
    "test_import,expected_imports",
    [
        ('import express from "express";', {"express"}),
        ('import * as foo from "express";', {"express"}),
        ('import { default as bar } from "express";', {"express"}),
        ('import { Request, Response, default as baz } from "express";', {"express"}),
        ('import express, * as qux from "express";', {"express"}),
        ('import express, { default as quux } from "express";', {"express"}),
        ('import express, { Request, Response, default as corge } from "express";', {"express"}),
        ("const express = require('express');", {"express"}),
        ("const foo = bar = require('express');", {"express"}),
    ],
)
def test_get_imports(test_import, expected_imports):
    parsed_module = JS_PARSER.parse(test_import.encode("utf-8"))

    detected_identifiers = get_imports(parsed_module)

    assert detected_identifiers == expected_imports
