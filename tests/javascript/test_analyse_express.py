import pytest

from static_analysis.javascript.analyse_express import (
    get_app_identifiers, get_express_identifiers, get_paths_and_methods
)
from static_analysis.javascript.analyse_javascript import JS_PARSER


@pytest.mark.parametrize(
    "test_import, expected_identifiers",
    [
        ('import express from "express";', {"express"}),
        ('import * as foo from "express";', {"foo.default"}),
        ('import { default as bar } from "express";', {"bar"}),
        ('import { Request, Response, default as baz } from "express";', {"baz"}),
        ('import express, * as qux from "express";', {"express", "qux.default"}),
        ('import express, { default as quux } from "express";', {"express", "quux"}),
        ('import express, { Request, Response, default as corge } from "express";', {"express", "corge"}),
        ('const grault = require(\'express\');', {"grault"}),
        ('import express from "not-express";', set()),
        ('import * as foo from "not-express";', set()),
        ('import { default as bar } from "not-express";', set()),
        ('import { Request, Response, default as baz } from "not-express";', set()),
        ('import express, * as qux from "not-express";', set()),
        ('import express, { default as quux } from "not-express";', set()),
        ('import express, { Request, Response, default as corge } from "not-express";', set()),
        ('const grault = require(\'not-express\');', set()),
    ],
)
def test_get_express_identifiers(test_import, expected_identifiers):
    parsed_module = JS_PARSER.parse(test_import.encode("utf-8"))

    detected_identifiers = get_express_identifiers(parsed_module)

    assert detected_identifiers == expected_identifiers


@pytest.mark.parametrize(
    "test_app, express_identifiers, expected_app_identifiers",
    [
        ("foo = express()", {"express"}, {"foo"}),
        ("const bar = express()", {"express"}, {"bar"}),
        ("var baz = express()", {"express"}, {"baz"}),
        ("let qux = express()", {"express"}, {"qux"}),
        ("quux = express({ strict: false })", {"express"}, {"quux"}),
        ("const corge = express({ strict: false })", {"express"}, {"corge"}),
        ("var grault = express({ strict: false })", {"express"}, {"grault"}),
        ("let garply = express({ strict: false })", {"express"}, {"garply"}),
    ]
)
def test_get_app_identifiers(test_app, express_identifiers, expected_app_identifiers):
    parsed_module = JS_PARSER.parse(test_app.encode("utf-8"))

    detected_app_identifiers = get_app_identifiers(parsed_module, express_identifiers)

    assert detected_app_identifiers == expected_app_identifiers


@pytest.mark.parametrize(
    "test_app_filename, app_and_router_identifiers, expected_paths",
    [
        ("tests/javascript/example_apps/express_hello_world_get.js", {"app"}, {"/": {"get"}}),
        (
            "tests/javascript/example_apps/express_hello_world_all.js",
            {"app"},
            {"/": {'delete', 'trace', 'options', 'head', 'get', 'patch', 'post', 'put'}}
        ),
        (
            "tests/javascript/example_apps/express_web_service.js",
            {"app"},
            {
                '/': {'delete', 'trace', 'options', 'head', 'get', 'patch', 'post', 'put'},
                '/api': {'delete', 'trace', 'options', 'head', 'get', 'patch', 'post', 'put'},
                '/api/users': {'get'},
                '/api/repos': {'get'},
                '/api/user/:name/repos': {'get'},
            }
        ),
        ("tests/javascript/example_apps/express_router_apiv1.js", {"apiv1"}, {"/": {"get"}, "/users": {"get"}}),
    ]
)
def test_get_paths_and_methods(test_app_filename, app_and_router_identifiers, expected_paths):
    file = open(test_app_filename, "r")
    file_contents = file.read()
    file.close()

    parsed_module = JS_PARSER.parse(file_contents.encode("utf-8"))

    detected_paths = get_paths_and_methods(parsed_module, app_and_router_identifiers)

    assert detected_paths == expected_paths
