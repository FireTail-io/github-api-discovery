package main

import (
	"go/parser"
	"go/token"
	"log"
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
	abstractSyntaxTree, err := parser.ParseFile(fileSet, filePath, fileContents, parser.ImportsOnly)
	if err != nil {
		return map[string]string{}, map[string]interface{}{}, err
	}

	// A map of imports' paths to their package names. E.g.
	// import foo "net/http" -> {"net/http": "foo"}
	// import "net/http" -> {"net/http" -> "http"}
	imports := map[string]string{}
	for _, parsedImport := range abstractSyntaxTree.Imports {
		log.Println(parsedImport.Comment, parsedImport.Doc, parsedImport.Name, parsedImport.Path)
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

	// TODO: perform analysis based on the detected frameworks to find routes & methods

	return importedSupportedFrameworks, map[string]interface{}{}, nil
}
