import pytest
import yaml

from static_analysis.javascript.analyse_javascript import (JS_PARSER,
                                                           analyse_javascript,
                                                           get_imports)


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
        ("var express = require('express');", {"express"}),
        ("let express = require('express');", {"express"}),
        ("express = require('express');", {"express"}),
        ("const foo = bar = require('express');", {"express"}),
        ("var foo = bar = require('express');", {"express"}),
        ("let foo = bar = require('express');", {"express"}),
        ("foo = bar = require('express');", {"express"}),
    ],
)
def test_get_imports(test_import, expected_imports):
    parsed_module = JS_PARSER.parse(test_import.encode("utf-8"))

    detected_identifiers = get_imports(parsed_module)

    assert detected_identifiers == expected_imports


@pytest.mark.parametrize(
    "test_app_filename, expected_detected_frameworks, expected_appspec_key, expected_appspec_filename",
    [
        (
            "tests/javascript/example_apps/express/hello_world_get.js",
            {"express"},
            "static-analysis:express:tests/javascript/example_apps/express/hello_world_get.js",
            "tests/javascript/example_apps/express/hello_world_get_appspec.yml",
        ),
        (
            "tests/javascript/example_apps/express/hello_world_all.js",
            {"express"},
            "static-analysis:express:tests/javascript/example_apps/express/hello_world_all.js",
            "tests/javascript/example_apps/express/hello_world_all_appspec.yml",
        ),
        (
            "tests/javascript/example_apps/express/router_apiv1.js",
            {"express"},
            "static-analysis:express:tests/javascript/example_apps/express/router_apiv1.js",
            "tests/javascript/example_apps/express/router_apiv1_appspec.yml",
        ),
        (
            "tests/javascript/example_apps/express/web_service.js",
            {"express"},
            "static-analysis:express:tests/javascript/example_apps/express/web_service.js",
            "tests/javascript/example_apps/express/web_service_appspec.yml",
        ),
    ],
)
def test_analyse_javascript(
    test_app_filename, expected_detected_frameworks, expected_appspec_key, expected_appspec_filename
):
    file = open(test_app_filename, "r")
    test_app_file_contents = file.read()
    file.close()

    file = open(expected_appspec_filename, "r")
    expected_appspec = yaml.load(file.read(), Loader=yaml.Loader)
    file.close()

    detected_frameworks, detected_appspecs = analyse_javascript(test_app_filename, test_app_file_contents)

    assert detected_frameworks == expected_detected_frameworks

    assert len(detected_appspecs) == 1
    assert detected_appspecs.get(expected_appspec_key) is not None
    assert detected_appspecs[expected_appspec_key] == expected_appspec
