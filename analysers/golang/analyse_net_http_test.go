package main

import (
	"go/parser"
	"go/token"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAnalyseNetHttpHandle(t *testing.T) {
	fileName := "net_http_hello_world.go"
	fileContents := `package main

import (
	"fmt"
	"log"
	"net/http"
	"sync"
)

type countHandler struct {
	mu sync.Mutex // guards n
	n  int
}

func (h *countHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.n++
	fmt.Fprintf(w, "count is %d\n", h.n)
}

func main() {
	http.Handle("/count", new(countHandler))
	log.Fatal(http.ListenAndServe(":8080", nil))
}`
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, fileName, fileContents, parser.SkipObjectResolution)
	require.Nil(t, err)

	paths := analyseNetHTTP(parsedFile, "http")
	assert.Equal(t, []string{"/count"}, paths)
}

func TestAnalyseNetHttpHandleFunc(t *testing.T) {
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
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, fileName, fileContents, parser.SkipObjectResolution)
	require.Nil(t, err)

	paths := analyseNetHTTP(parsedFile, "http")
	assert.Equal(t, []string{"/hello"}, paths)
}


func TestAnalyseNetHttpTooManyArgsToHandleFunc(t *testing.T) {
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
	http.HandleFunc("/hello", hello, hello) // Too many args here
	http.ListenAndServe(":8080", nil)
}`
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, fileName, fileContents, parser.SkipObjectResolution)
	require.Nil(t, err)

	paths := analyseNetHTTP(parsedFile, "http")
	assert.Equal(t, []string{}, paths)
}

func TestAnalyseNetHttpWrongFunctionSelectorTarget(t *testing.T) {
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
	wrong.HandleFunc("/hello", hello)
	http.ListenAndServe(":8080", nil)
}`
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, fileName, fileContents, parser.SkipObjectResolution)
	require.Nil(t, err)

	paths := analyseNetHTTP(parsedFile, "http")
	assert.Equal(t, []string{}, paths)
}

func TestAnalyseNetHttpNonStringPath(t *testing.T) {
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
	http.HandleFunc(3.14159, hello)
	http.ListenAndServe(":8080", nil)
}`
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, fileName, fileContents, parser.SkipObjectResolution)
	require.Nil(t, err)

	paths := analyseNetHTTP(parsedFile, "http")
	assert.Equal(t, []string{}, paths)
}
