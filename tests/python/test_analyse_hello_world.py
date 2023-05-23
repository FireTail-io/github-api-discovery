from src.static_analysis import analyse_python


def test_analyse_flask_hello_world():
    file_path = "tests/python/example_apps/flask_hello_world.py"
    file_contents = open(file_path, "r").read()

    frameworks_detected = analyse_python(file_path, file_contents)

    assert frameworks_detected == {"flask"}
