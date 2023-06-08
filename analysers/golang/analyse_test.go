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

	func hello(w beans.ResponseWriter, req *beans.Request) {
		fmt.Fprintf(w, "Hello, world!\n")
	}

	func main() {
		beans.HandleFunc("/hello", hello)
		beans.ListenAndServe(":8080", nil)
	}`

	imports, _, err := analyse(fileName, fileContents)
	require.Nil(t, err)
	assert.Equal(t, map[string]string{"net/http": "http"}, imports)
}