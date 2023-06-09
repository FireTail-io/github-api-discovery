import pytest

from static_analysis import analyse_python


@pytest.mark.parametrize(
    "test_file_contents",
    [
        """from flask import Flask

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "<p>Hello, World!</p>"
""",
        """from flask import Flask as F

app = F(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "<p>Hello, World!</p>"
""",
        """import flask

app = flask.Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "<p>Hello, World!</p>"
""",
        """import flask as f

app = f.Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "<p>Hello, World!</p>"
""",
    ],
)
def test_analyse_flask_hello_world(test_file_contents):
    file_path = "tests/python/example_apps/flask_hello_world.py"

    detected_frameworks, appspecs = analyse_python(file_path, test_file_contents)

    assert detected_frameworks == {"flask"}
    assert appspecs == {
        "static-analysis:flask:tests/python/example_apps/flask_hello_world.py": {
            "openapi": "3.0.0",
            "info": {"title": "Static Analysis - Flask"},
            "paths": {"/": {"get": {}}},
        }
    }


def test_analyse_flask_notes_app():
    file_path = "tests/python/example_apps/flask_notes_app.py"
    file_contents = open(file_path, "r").read()

    detected_frameworks, appspecs = analyse_python(file_path, file_contents)

    assert detected_frameworks == {"flask"}
    assert appspecs == {
        "static-analysis:flask:tests/python/example_apps/flask_notes_app.py": {
            "openapi": "3.0.0",
            "info": {"title": "Static Analysis - Flask"},
            "paths": {
                "/": {"get": {}},
                "/new": {"get": {}, "post": {}},
                "/edit/<int:note_id>": {"get": {}, "post": {}},
                "/delete/<int:note_id>": {"post": {}},
            },
        }
    }
