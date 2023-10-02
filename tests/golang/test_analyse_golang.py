from static_analysis import analyse_golang


def test_analyse_net_http_hello_world():
    file_path = "tests/golang/example_apps/net_http_hello_world.go"
    file_contents = open(file_path, "r").read()

    detected_frameworks, appspecs = analyse_golang(file_path, file_contents)

    assert detected_frameworks == {"net/http"}
    assert appspecs == {
        "static-analysis:net/http:tests/golang/example_apps/net_http_hello_world.go": {
            "openapi": "3.0.0",
            "info": {"title": "Static Analysis - Golang net/http"},
            "paths": {
                "/hello": {"responses": {"default": {"description": "Discovered via static analysis"}}},
            },
        }
    }


def test_analyse_malformed_go_file():
    file_path = "tests/golang/example_apps/malformed.go"
    file_contents = '{"Oh no": "This is\'nt golang, i\'s JSON!"}'

    detected_frameworks, appspecs = analyse_golang(file_path, file_contents)

    assert detected_frameworks == set()
    assert appspecs == {}
