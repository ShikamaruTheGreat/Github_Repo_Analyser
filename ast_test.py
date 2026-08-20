import ast

with open("test_file.py", "r") as code:
    code = code.read()
    tree = ast.parse(code)

class CodeAnalyser(ast.NodeVisitor):
    def __init__(self):
        self.assignments = 0
        self.if_statements = 0

    def visit_Assign(self, node):
        self.assignments += 1
        self.generic_visit(node)
    def visit_If(self, node):
        self.if_statements += 1
        self.generic_visit(node) # this counts nested ifs

    def get_vals(self):
        return (f"in this code file, there are {self.assignments} assignment of variables, "
                f"and {self.if_statements} if branches")

code_analyser = CodeAnalyser()
code_analyser.visit(tree)
print(code_analyser.get_vals())

# UNDERSTAND THIS NIGGA