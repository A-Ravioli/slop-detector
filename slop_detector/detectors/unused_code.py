"""Detector for unused code (functions, classes, files)."""

from typing import List, Set, Dict
import networkx as nx
from .base import BaseDetector, Issue, IssueSeverity
from ..parsers.base import ParsedFile, Definition


class UnusedCodeDetector(BaseDetector):
    """Detects unused functions, classes, and files."""
    
    def detect(self, parsed_files: List[ParsedFile], file_graph: nx.DiGraph = None,
               entity_graph: nx.DiGraph = None) -> List[Issue]:
        """Detect unused code.
        
        Args:
            parsed_files: List of parsed file objects
            file_graph: File dependency graph (optional)
            entity_graph: Entity dependency graph (optional)
            
        Returns:
            List of detected issues
        """
        self.clear_issues()
        
        # Build usage maps
        all_definitions, all_usages = self._build_usage_maps(parsed_files)
        
        # Check for unused entities
        self._check_unused_entities(all_definitions, all_usages, parsed_files)
        
        # Check for stranded files (if graph provided)
        if file_graph:
            self._check_stranded_files(file_graph)
        
        return self.get_issues()
    
    def _build_usage_maps(self, parsed_files: List[ParsedFile]) -> tuple:
        """Build maps of all definitions and usages.
        
        Returns:
            Tuple of (definitions dict, usages set)
        """
        definitions: Dict[str, tuple] = {}  # name -> (file, definition)
        usages: Set[str] = set()
        
        for pf in parsed_files:
            # Track all definitions
            for defn in pf.definitions:
                # Use qualified name for methods
                if defn.parent:
                    full_name = f"{defn.parent}.{defn.name}"
                    definitions[full_name] = (pf.file_path, defn)
                
                # Also track by simple name
                if defn.name not in definitions:
                    definitions[defn.name] = (pf.file_path, defn)
                else:
                    # Multiple definitions with same name - mark as used to avoid false positives
                    usages.add(defn.name)
                
                # Track all calls within this definition
                usages.update(defn.calls)
            
            # Track imported names as usages
            for imp in pf.imports:
                usages.update(imp.names)
                if imp.alias:
                    usages.add(imp.alias)
            
            # Scan raw content for additional usages (regex-based)
            usages.update(self._scan_for_usages(pf.raw_content))
        
        return definitions, usages
    
    def _scan_for_usages(self, content: str) -> Set[str]:
        """Scan content for potential name usages using simple heuristics."""
        import re
        
        usages = set()
        
        # Find identifier patterns (function calls, variable references)
        # This is a heuristic approach - not perfect but catches most cases
        patterns = [
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',  # Function calls
            r'new\s+([A-Z][a-zA-Z0-9_]*)',  # Class instantiation
            r'([A-Z][a-zA-Z0-9_]*)\.',  # Class method access
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            usages.update(matches)
        
        return usages
    
    def _check_unused_entities(self, definitions: Dict, usages: Set, parsed_files: List[ParsedFile]):
        """Check for unused functions and classes."""
        special_names = {
            '__init__', '__main__', 'main', 'setup', 'teardown',
            'setUp', 'tearDown', 'test_', '__name__',
            # Common framework/library hooks
            'render', 'componentDidMount', 'componentWillUnmount',
            'ngOnInit', 'ngOnDestroy',
        }
        
        for name, (file_path, defn) in definitions.items():
            # Skip special names and test functions
            if name in special_names or name.startswith('test_') or name.startswith('_test'):
                continue
            
            # Skip magic methods
            if name.startswith('__') and name.endswith('__'):
                continue
            
            # Skip if it's a property or starts with underscore (private)
            # Being conservative here to avoid false positives
            if name.startswith('_'):
                continue
            
            # Check if name is used anywhere
            is_used = False
            
            # Check direct name
            if name in usages:
                is_used = True
            
            # Check qualified name (for methods)
            if defn.parent:
                qualified = f"{defn.parent}.{name}"
                if qualified in usages:
                    is_used = True
            
            # If not used, report it
            if not is_used:
                # Determine severity based on entity type
                severity = IssueSeverity.WARNING
                if defn.type.value == 'class':
                    severity = IssueSeverity.ERROR
                
                self.add_issue(Issue(
                    severity=severity,
                    category="Unused Code",
                    message=f"Unused {defn.type.value}: {name}",
                    file_path=file_path,
                    line=defn.line_start,
                    line_end=defn.line_end,
                    code_snippet=self._get_code_snippet(file_path, defn.line_start),
                    suggestion=f"Remove unused {defn.type.value} or add exports if needed",
                    metadata={
                        "entity_name": name,
                        "entity_type": defn.type.value,
                        "parent": defn.parent
                    }
                ))
    
    def _check_stranded_files(self, file_graph: nx.DiGraph):
        """Check for files that are never imported."""
        entry_points = self.config.get('entry_points', [])
        
        for node in file_graph.nodes():
            # Check if file has no incoming edges
            in_degree = file_graph.in_degree(node)
            
            if in_degree == 0:
                # Check if it's an entry point
                is_entry = any(ep in node for ep in entry_points)
                
                # Check if it's a test file (often not imported)
                is_test = 'test' in node.lower() or node.endswith('_test.py')
                
                if not is_entry and not is_test:
                    node_data = file_graph.nodes[node]
                    file_path = node_data.get('file_path', node)
                    
                    self.add_issue(Issue(
                        severity=IssueSeverity.ERROR,
                        category="Stranded File",
                        message=f"File is never imported: {node}",
                        file_path=file_path,
                        suggestion="Remove file or add imports if it's an entry point",
                        metadata={"file": node}
                    ))

