package main

import (
	"go/parser"
	"go/token"
	"strings"
)

func filterImportsToSupportedFrameworks(imports map[string]string) map[string]string {
	supportedFrameworks := map[string]struct{}{
		"net/http": {},
	}

	importedSupportedFrameworks := map[string]string{}

	for importedPath, importedPackageName := range imports {
		if _, ok := supportedFrameworks[importedPath]; ok {
			importedSupportedFrameworks[importedPath] = importedPackageName
		}
	}

	return importedSupportedFrameworks
}

func analyse(filePath string, fileContents string) (map[string]string, map[string]interface{}, error) {
	fileSet := token.NewFileSet()
	parsedFile, err := parser.ParseFile(fileSet, filePath, fileContents, parser.SkipObjectResolution)
	if err != nil {
		return map[string]string{}, map[string]interface{}{}, err
	}

	// A map of imports' paths to their package names. E.g.
	// import foo "net/http" -> {"net/http": "foo"}
	// import "net/http" -> {"net/http" -> "http"}
	imports := map[string]string{}
	for _, parsedImport := range parsedFile.Imports {
		// parsedImport.Path.Value includes quotes on either end (e.g. "net/http"); these indexes strip them.
		importPath := parsedImport.Path.Value[1:len(parsedImport.Path.Value)-1]
		if parsedImport.Name != nil {
			imports[importPath] = parsedImport.Name.Name
		} else {
			importPathParts := strings.Split(importPath, "/")
			imports[importPath] = importPathParts[len(importPathParts)-1]
		}
	}

	importedSupportedFrameworks := filterImportsToSupportedFrameworks(imports)
	openapiSpecs := map[string]interface{}{}

	// Static analysis for files importing net/http
	if packageIdentifier, ok := importedSupportedFrameworks["net/http"]; ok {
		netHttpPathsSlice := analyseNetHTTP(parsedFile, packageIdentifier)

		netHttpPathsMap := map[string]map[string]map[string]map[string]string{}
		for _, path := range netHttpPathsSlice {
			netHttpPathsMap[path] = map[string]map[string]map[string]string{
				"responses": {
					"default": {
						"description": "Discovered via static analysis",
					},
				},
			}
		}

		// Only make an appspec if there's at least one path detected
		if len(netHttpPathsMap) > 0 {
			openapiSpecs["static-analysis:net/http:" + filePath] = map[string]interface{}{
				"openapi": "3.0.0",
				"info": map[string]string{"title": "Static Analysis - Golang net/http"},
				"paths": netHttpPathsMap,
			}
		}
	}

	return importedSupportedFrameworks, openapiSpecs, nil
}
