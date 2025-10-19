"""Detector for unused imports."""

import re
from typing import List, Set
from .base import BaseDetector, Issue, IssueSeverity
from ..parsers.base import ParsedFile


class ImportDetector(BaseDetector):
    """Detects unused imports."""
    
    def detect(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Detect unused imports.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            List of detected issues
        """
        self.clear_issues()
        
        for pf in parsed_files:
            self._check_file_imports(pf)
        
        return self.get_issues()
    
    def _check_file_imports(self, pf: ParsedFile):
        """Check imports in a single file."""
        # Get all imported names
        imported_names = set()
        imports_by_name = {}
        
        for imp in pf.imports:
            for name in imp.names:
                if name != '*':  # Skip star imports
                    imported_names.add(name)
                    imports_by_name[name] = imp
            
            # Also track aliases
            if imp.alias:
                imported_names.add(imp.alias)
                imports_by_name[imp.alias] = imp
        
        # Find which names are actually used
        used_names = self._find_used_names(pf)
        
        # Check for unused imports
        for name in imported_names:
            if name not in used_names:
                imp = imports_by_name[name]
                
                self.add_issue(Issue(
                    severity=IssueSeverity.INFO,
                    category="Unused Import",
                    message=f"Unused import: {name} from {imp.module}",
                    file_path=pf.file_path,
                    line=imp.line,
                    code_snippet=self._get_code_snippet(pf.file_path, imp.line),
                    suggestion="Remove unused import",
                    metadata={"import_name": name, "module": imp.module}
                ))
    
    def _find_used_names(self, pf: ParsedFile) -> Set[str]:
        """Find all names that are used in the file."""
        used = set()
        
        # Names used in function/method calls
        for defn in pf.definitions:
            used.update(defn.calls)
        
        # Names used in type annotations, docstrings, etc.
        # Use regex to find identifiers in the content
        # This is a heuristic but should catch most usage
        
        # Pattern for identifier usage
        identifier_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        
        for match in re.finditer(identifier_pattern, pf.raw_content):
            name = match.group(1)
            
            # Don't count if it's part of import statement
            line_start = pf.raw_content.rfind('\n', 0, match.start()) + 1
            line_end = pf.raw_content.find('\n', match.start())
            if line_end == -1:
                line_end = len(pf.raw_content)
            
            line = pf.raw_content[line_start:line_end].strip()
            
            # Skip if it's on an import line
            if line.startswith(('import ', 'from ')):
                continue
            
            # Skip if it's a definition keyword
            if name in ('def', 'class', 'import', 'from', 'return', 'if', 'else', 'for', 'while'):
                continue
            
            used.add(name)
        
        return used

