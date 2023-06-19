package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAnalyseGolang(t *testing.T) {
	fileName := "net_http_hello_world.go"
	fileContents := `package main

import (
	"fmt"
	"net/http"
)

func hello(w http.ResponseWriter, req *http.Request) {
	fmt.Fprintf(w, "Hello, world!\n")
}

func main() {
	http.HandleFunc("/hello", hello)
	http.ListenAndServe(":8080", nil)
}`

	imports, openapiSpecs, err := analyse(fileName, fileContents)
	assert.Nil(t, err)
	assert.Equal(t, map[string]string{"net/http": "http"}, imports)
	assert.Equal(t, map[string]interface{}{
			"static-analysis:net/http:net_http_hello_world.go": map[string]interface{}{
			"openapi": "3.0.0",
			"info": map[string]string{"title": "Static Analysis - Golang net/http"},
			"paths": map[string]map[string]map[string]map[string]string{
				"/hello": {
					"responses": {
						"default": {
							"description": "Discovered via static analysis",
						},
					},
				}},
		},
	}, openapiSpecs)
}

func TestAnalyseGolangNamedImport(t *testing.T) {
	fileName := "net_http_hello_world.go"
	fileContents := `package main

import (
	"fmt"
	nethttp "net/http"
)

func hello(w nethttp.ResponseWriter, req *http.Request) {
	fmt.Fprintf(w, "Hello, world!\n")
}

func main() {
	nethttp.HandleFunc("/hello", hello)
	nethttp.ListenAndServe(":8080", nil)
}`

	imports, openapiSpecs, err := analyse(fileName, fileContents)
	assert.Nil(t, err)
	assert.Equal(t, map[string]string{"net/http": "nethttp"}, imports)
	assert.Equal(t, map[string]interface{}{
			"static-analysis:net/http:net_http_hello_world.go": map[string]interface{}{
			"openapi": "3.0.0",
			"info": map[string]string{"title": "Static Analysis - Golang net/http"},
			"paths": map[string]map[string]map[string]map[string]string{
				"/hello": {
					"responses": {
						"default": {
							"description": "Discovered via static analysis",
						},
					},
				},
			},
		},
	}, openapiSpecs)
}

func TestAnalyseGolangNotGoFile(t *testing.T) {
	fileName := "net_http_hello_world.go"
	fileContents := `{"Oh no": "This isn't a .go file, it's just JSON!"}`

	imports, openapiSpecs, err := analyse(fileName, fileContents)
	assert.NotNil(t, err)
	assert.Equal(t, "net_http_hello_world.go:1:1: expected 'package', found '{'", err.Error())
	assert.Equal(t, map[string]string{}, imports)
	assert.Equal(t, map[string]interface{}{}, openapiSpecs)
}