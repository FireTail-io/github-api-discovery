package main

import (
	"go/ast"
	"go/token"
)

type NetHttpVisitor struct {
	// A slice path strings e.g. ["/hello_world"]
	paths []string
	// The ident of the net/http package to look for. Will generally be the package name, "http".
	packageIdentifier string
}

func (visitor *NetHttpVisitor) Visit(node ast.Node) ast.Visitor {
	// We're only interested in callExprs, e.g. "http.HandleFunc("/health", health)" or "http.Handle("/health", health)"
	callExpr, ok := node.(*ast.CallExpr)
	if !ok {
		return visitor
	}

	// If it's a CallExpr for a http.HandleFunc()/http.Handle() then it'll have exactly two args
	if (len(callExpr.Args) != 2) {
		return visitor
	}

	// If it's a CallExpr for a http.HandleFunc()/http.Handle() then it'll have a SelectorExpr for
	// http.HandleFunc/http.Handle where the Selector name is "HandleFunc" or "Handle"
	functionSelector, ok := callExpr.Fun.(*ast.SelectorExpr)
	if !ok || (functionSelector.Sel.Name != "HandleFunc" && functionSelector.Sel.Name != "Handle") {
		return visitor
	}

	// functionSelector.X should be an Ident with a string value matching the ident of the net/http package
	if packageIdent, ok := functionSelector.X.(*ast.Ident); !ok || packageIdent.String() != visitor.packageIdentifier {
		return visitor
	}

	// We'll only bother with basic literals here for now.
	// E.g. this will be detected:
	// http.HandlerFunc("/health", health)
	// But for now, this will not:
	// healthPath := "/health"
	// http.HandlerFunc(healthPath, health)
	path, ok := callExpr.Args[0].(*ast.BasicLit)
	if !ok || path.Kind != token.STRING {
		return visitor
	}

	// path.Value includes quotes on either end (e.g. "/health"); these indexes strip them.
	visitor.paths = append(visitor.paths, path.Value[1:len(path.Value)-1])

	return visitor
}

func analyseNetHTTP(file *ast.File, packageIdentifier string) []string {
	visitor := &NetHttpVisitor{
		paths: []string{},
		packageIdentifier: packageIdentifier,
	}

	ast.Walk(visitor, file)

	return visitor.paths
}
