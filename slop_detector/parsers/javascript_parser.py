"""JavaScript and TypeScript parser."""

import re
import esprima
from typing import List, Set, Any, Dict
from .base import (
    BaseParser, ParsedFile, Import, Definition, Comment,
    EntityType
)


class JavaScriptParser(BaseParser):
    """Parser for JavaScript and TypeScript files."""
    
    def can_parse(self, language: str) -> bool:
        return language in ('javascript', 'typescript')
    
    def parse_file(self, file_path: str) -> ParsedFile:
        """Parse JavaScript/TypeScript file."""
        content = self._read_file(file_path)
        
        language = 'typescript' if file_path.endswith(('.ts', '.tsx')) else 'javascript'
        
        parsed = ParsedFile(
            file_path=file_path,
            language=language,
            raw_content=content,
            lines_of_code=self._count_lines(content)
        )
        
        try:
            # Parse with esprima (works for most JS/TS without type annotations)
            tree = esprima.parseModule(content, {'loc': True, 'range': True, 'comment': True})
            
            # Extract imports
            parsed.imports = self._extract_imports(tree)
            
            # Extract definitions
            parsed.definitions = self._extract_definitions(tree, content)
            
            # Extract comments
            parsed.comments = self._extract_comments(tree, content)
            
        except Exception:
            # If parsing fails, try to extract basic info with regex
            parsed.imports = self._extract_imports_regex(content)
            parsed.comments = self._extract_comments_regex(content)
        
        return parsed
    
    def _extract_imports(self, tree: Any) -> List[Import]:
        """Extract import statements from AST."""
        imports = []
        
        def visit_node(node):
            if isinstance(node, dict):
                node_type = node.get('type')
                
                # ES6 imports: import { x, y } from 'module'
                if node_type == 'ImportDeclaration':
                    source = node.get('source', {}).get('value', '')
                    specifiers = node.get('specifiers', [])
                    
                    if specifiers:
                        names = []
                        alias = None
                        for spec in specifiers:
                            spec_type = spec.get('type')
                            if spec_type == 'ImportDefaultSpecifier':
                                name = spec.get('local', {}).get('name', '')
                                names.append(name)
                            elif spec_type == 'ImportSpecifier':
                                imported = spec.get('imported', {}).get('name', '')
                                names.append(imported)
                            elif spec_type == 'ImportNamespaceSpecifier':
                                alias = spec.get('local', {}).get('name', '')
                                names.append('*')
                        
                        imports.append(Import(
                            module=source,
                            names=names,
                            line=node.get('loc', {}).get('start', {}).get('line', 0),
                            is_star_import='*' in names,
                            alias=alias
                        ))
                
                # CommonJS: require()
                elif node_type == 'VariableDeclaration':
                    for declarator in node.get('declarations', []):
                        init = declarator.get('init', {})
                        if init.get('type') == 'CallExpression':
                            callee = init.get('callee', {})
                            if callee.get('name') == 'require':
                                args = init.get('arguments', [])
                                if args and args[0].get('type') == 'Literal':
                                    module = args[0].get('value', '')
                                    id_node = declarator.get('id', {})
                                    names = self._extract_names_from_pattern(id_node)
                                    
                                    imports.append(Import(
                                        module=module,
                                        names=names,
                                        line=node.get('loc', {}).get('start', {}).get('line', 0)
                                    ))
                
                # Recursively visit children
                for key, value in node.items():
                    if isinstance(value, dict):
                        visit_node(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                visit_node(item)
        
        visit_node(tree)
        return imports
    
    def _extract_names_from_pattern(self, pattern: Dict) -> List[str]:
        """Extract names from destructuring pattern."""
        names = []
        pattern_type = pattern.get('type')
        
        if pattern_type == 'Identifier':
            names.append(pattern.get('name', ''))
        elif pattern_type == 'ObjectPattern':
            for prop in pattern.get('properties', []):
                key = prop.get('key', {})
                if key.get('type') == 'Identifier':
                    names.append(key.get('name', ''))
        elif pattern_type == 'ArrayPattern':
            for element in pattern.get('elements', []):
                if element:
                    names.extend(self._extract_names_from_pattern(element))
        
        return names
    
    def _extract_definitions(self, tree: Any, content: str) -> List[Definition]:
        """Extract function and class definitions from AST."""
        definitions = []
        lines = content.split('\n')
        
        def visit_node(node, parent_class=None):
            if isinstance(node, dict):
                node_type = node.get('type')
                loc = node.get('loc', {})
                line_start = loc.get('start', {}).get('line', 0)
                line_end = loc.get('end', {}).get('line', 0)
                
                # Class declarations
                if node_type == 'ClassDeclaration':
                    class_name = node.get('id', {}).get('name', '')
                    definitions.append(Definition(
                        name=class_name,
                        type=EntityType.CLASS,
                        line_start=line_start,
                        line_end=line_end,
                        parent=parent_class
                    ))
                    
                    # Visit class methods
                    body = node.get('body', {})
                    for item in body.get('body', []):
                        visit_node(item, parent_class=class_name)
                    return
                
                # Function declarations
                elif node_type == 'FunctionDeclaration':
                    func_name = node.get('id', {}).get('name', '')
                    params = [p.get('name', '') for p in node.get('params', []) if p.get('type') == 'Identifier']
                    calls = self._extract_calls(node)
                    nesting = self._calculate_nesting(node)
                    
                    definitions.append(Definition(
                        name=func_name,
                        type=EntityType.FUNCTION if not parent_class else EntityType.METHOD,
                        line_start=line_start,
                        line_end=line_end,
                        parent=parent_class,
                        calls=calls,
                        nesting_depth=nesting,
                        parameters=params
                    ))
                
                # Method definitions
                elif node_type == 'MethodDefinition':
                    method_name = node.get('key', {}).get('name', '')
                    value = node.get('value', {})
                    params = [p.get('name', '') for p in value.get('params', []) if p.get('type') == 'Identifier']
                    calls = self._extract_calls(value)
                    nesting = self._calculate_nesting(value)
                    
                    definitions.append(Definition(
                        name=method_name,
                        type=EntityType.METHOD,
                        line_start=line_start,
                        line_end=line_end,
                        parent=parent_class,
                        calls=calls,
                        nesting_depth=nesting,
                        parameters=params
                    ))
                
                # Arrow functions and function expressions
                elif node_type == 'VariableDeclaration':
                    for declarator in node.get('declarations', []):
                        init = declarator.get('init', {})
                        init_type = init.get('type')
                        
                        if init_type in ('FunctionExpression', 'ArrowFunctionExpression'):
                            func_name = declarator.get('id', {}).get('name', '')
                            if func_name:
                                params = [p.get('name', '') for p in init.get('params', []) if p.get('type') == 'Identifier']
                                calls = self._extract_calls(init)
                                nesting = self._calculate_nesting(init)
                                
                                definitions.append(Definition(
                                    name=func_name,
                                    type=EntityType.FUNCTION,
                                    line_start=line_start,
                                    line_end=line_end,
                                    calls=calls,
                                    nesting_depth=nesting,
                                    parameters=params
                                ))
                
                # Recursively visit other nodes
                if node_type not in ('ClassDeclaration', 'FunctionDeclaration', 'MethodDefinition'):
                    for key, value in node.items():
                        if isinstance(value, dict):
                            visit_node(value, parent_class)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    visit_node(item, parent_class)
        
        visit_node(tree)
        return definitions
    
    def _extract_calls(self, node: Dict) -> List[str]:
        """Extract function calls from node."""
        calls = []
        
        def visit(n):
            if isinstance(n, dict):
                if n.get('type') == 'CallExpression':
                    callee = n.get('callee', {})
                    callee_type = callee.get('type')
                    
                    if callee_type == 'Identifier':
                        calls.append(callee.get('name', ''))
                    elif callee_type == 'MemberExpression':
                        obj = callee.get('object', {})
                        prop = callee.get('property', {})
                        if obj.get('type') == 'Identifier' and prop.get('type') == 'Identifier':
                            calls.append(f"{obj.get('name', '')}.{prop.get('name', '')}")
                
                for value in n.values():
                    if isinstance(value, dict):
                        visit(value)
                    elif isinstance(value, list):
                        for item in value:
                            visit(item)
        
        visit(node)
        return calls
    
    def _calculate_nesting(self, node: Dict) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        def visit(n, depth=0):
            nonlocal max_depth
            if isinstance(n, dict):
                node_type = n.get('type')
                
                # Statements that increase nesting
                if node_type in ('IfStatement', 'ForStatement', 'WhileStatement', 
                                 'DoWhileStatement', 'SwitchStatement', 'TryStatement'):
                    depth += 1
                    max_depth = max(max_depth, depth)
                
                for value in n.values():
                    if isinstance(value, dict):
                        visit(value, depth)
                    elif isinstance(value, list):
                        for item in value:
                            visit(item, depth)
        
        visit(node)
        return max_depth
    
    def _extract_comments(self, tree: Any, content: str) -> List[Comment]:
        """Extract comments from AST."""
        comments = []
        
        if hasattr(tree, 'comments'):
            for comment in tree.comments:
                comment_type = comment.get('type')
                value = comment.get('value', '').strip()
                loc = comment.get('loc', {})
                line = loc.get('start', {}).get('line', 0)
                
                is_docstring = comment_type == 'Block' and (value.startswith('*') or value.startswith('!'))
                
                comments.append(Comment(
                    text=value,
                    line=line,
                    is_docstring=is_docstring
                ))
        
        return comments
    
    def _extract_imports_regex(self, content: str) -> List[Import]:
        """Extract imports using regex as fallback."""
        imports = []
        
        # ES6 imports
        import_pattern = r'import\s+(?:{([^}]+)}|(\w+)|\*\s+as\s+(\w+))\s+from\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, content):
            names_group = match.group(1)
            default_import = match.group(2)
            namespace = match.group(3)
            module = match.group(4)
            
            names = []
            alias = None
            
            if names_group:
                names = [n.strip().split(' as ')[0] for n in names_group.split(',')]
            elif default_import:
                names = [default_import]
            elif namespace:
                names = ['*']
                alias = namespace
            
            line = content[:match.start()].count('\n') + 1
            imports.append(Import(
                module=module,
                names=names,
                line=line,
                is_star_import='*' in names,
                alias=alias
            ))
        
        # CommonJS require
        require_pattern = r'(?:const|let|var)\s+(\w+|\{[^}]+\})\s*=\s*require\(["\']([^"\']+)["\']\)'
        for match in re.finditer(require_pattern, content):
            names_group = match.group(1)
            module = match.group(2)
            
            if names_group.startswith('{'):
                names = [n.strip() for n in names_group[1:-1].split(',')]
            else:
                names = [names_group]
            
            line = content[:match.start()].count('\n') + 1
            imports.append(Import(
                module=module,
                names=names,
                line=line
            ))
        
        return imports
    
    def _extract_comments_regex(self, content: str) -> List[Comment]:
        """Extract comments using regex as fallback."""
        comments = []
        
        # Single line comments
        for i, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()
            if stripped.startswith('//'):
                comments.append(Comment(
                    text=stripped[2:].strip(),
                    line=i,
                    is_docstring=False
                ))
        
        # Multi-line comments
        multiline_pattern = r'/\*\*?(.*?)\*/'
        for match in re.finditer(multiline_pattern, content, re.DOTALL):
            text = match.group(1).strip()
            line = content[:match.start()].count('\n') + 1
            is_docstring = match.group(0).startswith('/**')
            
            comments.append(Comment(
                text=text,
                line=line,
                is_docstring=is_docstring
            ))
        
        return comments

