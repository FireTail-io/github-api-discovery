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

    frameworks_detected = analyse_python(file_path, test_file_contents)

    assert frameworks_detected == ({"flask"}, {"/": ["GET"]})


def test_analyse_flask_notes_app():
    file_path = "tests/python/example_apps/flask_notes_app.py"
    file_contents = open(file_path, "r").read()

    frameworks_detected = analyse_python(file_path, file_contents)

    assert frameworks_detected == (
        {"flask"},
        {
            "/": ["GET"],
            "/new": ["GET", "POST"],
            "/edit/<int:note_id>": ["GET", "POST"],
            "/delete/<int:note_id>": ["POST"],
        },
    )
