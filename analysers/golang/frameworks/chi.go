package frameworks

import "go/ast"

func (visitor *NetHttpVisitor) Chi(node ast.Node) ast.Visitor {
	return visitor
}