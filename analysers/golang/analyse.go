package main

import (
	"go/parser"
	"go/token"
)

func filterImportsToSupportedFrameworks(imports []string) []string {
	supportedFrameworks := map[string]struct{}{
		"net/http": {},
	}

	importedSupportedFrameworks := []string{}

	for _, importName := range imports {
		if _, ok := supportedFrameworks[importName]; ok {
			importedSupportedFrameworks = append(importedSupportedFrameworks, importName)
		}
	}

	return importedSupportedFrameworks
}


func analyse(filePath string, fileContents string) ([]string, map[string]interface{}, error) {
	fileSet := token.NewFileSet()
	abstractSyntaxTree, err := parser.ParseFile(fileSet, filePath, fileContents, parser.ImportsOnly)
	if err != nil {
		return []string{}, map[string]interface{}{}, err
	}

	imports := []string{}
	for _, parsedImport := range abstractSyntaxTree.Imports {
		if parsedImport.Name != nil {
			imports = append(imports, parsedImport.Name.Name)
		} else {
			// parsedImport.Path.Value includes quotes on either end (e.g. "net/http"); these indexes strip them.
			imports = append(imports, parsedImport.Path.Value[1:len(parsedImport.Path.Value)-1])
		}
	}

	importedSupportedFrameworks := filterImportsToSupportedFrameworks(imports)

	// TODO: perform analysis based on the detected frameworks to find routes & methods

	return importedSupportedFrameworks, map[string]interface{}{}, nil
}
