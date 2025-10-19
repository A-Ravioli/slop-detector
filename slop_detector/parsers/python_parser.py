"""Python AST parser."""

import ast
import re
from typing import List, Set
from .base import (
    BaseParser, ParsedFile, Import, Definition, Comment,
    EntityType
)


class PythonParser(BaseParser):
    """Parser for Python files using AST."""
    
    def can_parse(self, language: str) -> bool:
        return language == 'python'
    
    def parse_file(self, file_path: str) -> ParsedFile:
        """Parse Python file."""
        content = self._read_file(file_path)
        
        parsed = ParsedFile(
            file_path=file_path,
            language='python',
            raw_content=content,
            lines_of_code=self._count_lines(content)
        )
        
        try:
            tree = ast.parse(content, filename=file_path)
            
            # Extract imports
            parsed.imports = self._extract_imports(tree)
            
            # Extract definitions
            parsed.definitions = self._extract_definitions(tree, content)
            
            # Extract comments
            parsed.comments = self._extract_comments(content, tree)
            
        except SyntaxError:
            # File has syntax errors, skip parsing
            pass
        
        return parsed
    
    def _extract_imports(self, tree: ast.AST) -> List[Import]:
        """Extract import statements."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(Import(
                        module=alias.name,
                        names=[alias.name],
                        line=node.lineno,
                        alias=alias.asname
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    is_star = '*' in names
                    imports.append(Import(
                        module=node.module,
                        names=names,
                        line=node.lineno,
                        is_star_import=is_star
                    ))
        
        return imports
    
    def _extract_definitions(self, tree: ast.AST, content: str) -> List[Definition]:
        """Extract function and class definitions."""
        definitions = []
        
        class DefinitionVisitor(ast.NodeVisitor):
            def __init__(self, content: str):
                self.definitions = []
                self.content = content
                self.current_class = None
                
            def visit_ClassDef(self, node):
                """Visit class definition."""
                docstring = ast.get_docstring(node)
                parent = self.current_class
                
                defn = Definition(
                    name=node.name,
                    type=EntityType.CLASS,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=docstring,
                    parent=parent
                )
                self.definitions.append(defn)
                
                # Visit class methods
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_FunctionDef(self, node):
                """Visit function definition."""
                docstring = ast.get_docstring(node)
                
                # Determine entity type
                if self.current_class:
                    entity_type = EntityType.METHOD
                else:
                    entity_type = EntityType.FUNCTION
                
                # Extract function calls
                calls = self._extract_calls(node)
                
                # Calculate nesting depth
                nesting = self._calculate_nesting(node)
                
                # Get parameters
                params = [arg.arg for arg in node.args.args]
                
                defn = Definition(
                    name=node.name,
                    type=entity_type,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=docstring,
                    parent=self.current_class,
                    calls=calls,
                    nesting_depth=nesting,
                    parameters=params
                )
                self.definitions.append(defn)
                
                # Don't visit nested functions
                # self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                """Visit async function definition."""
                self.visit_FunctionDef(node)
            
            def _extract_calls(self, node: ast.AST) -> List[str]:
                """Extract function calls within a function."""
                calls = []
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            # For method calls like obj.method()
                            if isinstance(child.func.value, ast.Name):
                                calls.append(f"{child.func.value.id}.{child.func.attr}")
                            else:
                                calls.append(child.func.attr)
                
                return calls
            
            def _calculate_nesting(self, node: ast.AST) -> int:
                """Calculate maximum nesting depth in function."""
                max_depth = 0
                
                def calculate_depth(n, current_depth=0):
                    nonlocal max_depth
                    max_depth = max(max_depth, current_depth)
                    
                    # Nodes that increase nesting
                    if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        current_depth += 1
                    
                    for child in ast.iter_child_nodes(n):
                        calculate_depth(child, current_depth)
                
                calculate_depth(node)
                return max_depth
        
        visitor = DefinitionVisitor(content)
        visitor.visit(tree)
        definitions = visitor.definitions
        
        return definitions
    
    def _extract_comments(self, content: str, tree: ast.AST) -> List[Comment]:
        """Extract comments from source code."""
        comments = []
        lines = content.split('\n')
        
        # Extract regular comments
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                comments.append(Comment(
                    text=stripped[1:].strip(),
                    line=i,
                    is_docstring=False
                ))
        
        # Extract docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    parent_name = None
                    line_no = 1  # Default for module-level docstrings
                    
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        parent_name = node.name
                        line_no = node.lineno
                    
                    comments.append(Comment(
                        text=docstring,
                        line=line_no,
                        is_docstring=True,
                        parent_entity=parent_name
                    ))
        
        return comments

