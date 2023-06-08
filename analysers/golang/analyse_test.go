package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
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
	require.Nil(t, err)
	assert.Equal(t, map[string]string{"net/http": "http"}, imports)
	assert.Equal(t, map[string]interface{}{
			"static-analysis:net/http:net_http_hello_world.go": map[string]interface{}{
			"openapi": "3.0.0",
			"info": map[string]interface{}{"title": "Static Analysis - Golang net/http"},
			"paths": map[string]struct{}{"/hello": {}},
		},
	}, openapiSpecs)
}