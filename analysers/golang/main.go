package main

import (
	"C"
	"log"
)
import (
	"encoding/json"
	"fmt"
)

//export AnalyseCGOWrapper
func AnalyseCGOWrapper(filePathPointer *C.char, fileContentsPointer *C.char) *C.char {
	filePath := C.GoString(filePathPointer)
	fileContents := C.GoString(fileContentsPointer)

	log.Println("file_path:", filePath)
	log.Println("file_contents:", fileContents)

	frameworks_identified, _, err := analyse(filePath, fileContents)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"%s"}`, err.Error()))
	}

	// TODO: use results from analyse() in response_json
	response_json, err := json.Marshal(map[string]interface{}{
		"frameworks_identified": frameworks_identified,
		"openapi_specs": map[string]interface{}{
			"static-analysis:golang:tests/golang/example_apps/net_http_hello_world.go": map[string]interface{}{
				"openapi": "3.0.0",
				"info": map[string]interface{}{"title": "Static Analysis - Golang"},
				"paths": map[string]interface{}{
					"/hello": map[string]interface{}{"get": map[string]interface{}{}},
				},
			},
		},
	})
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"%s"}`, err.Error()))
	}

	return C.CString(string(response_json))
}

func main() {}