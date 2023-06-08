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

	frameworks_identified, openapi_specs, err := analyse(filePath, fileContents)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"%s"}`, err.Error()))
	}

	response_json, err := json.Marshal(map[string]interface{}{
		"frameworks_identified": frameworks_identified,
		"openapi_specs": openapi_specs,
	})
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"%s"}`, err.Error()))
	}

	return C.CString(string(response_json))
}

func main() {}