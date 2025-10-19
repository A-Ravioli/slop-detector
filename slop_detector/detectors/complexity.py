"""Detector for code complexity issues."""

import re
from typing import List
from .base import BaseDetector, Issue, IssueSeverity
from ..parsers.base import ParsedFile


class ComplexityDetector(BaseDetector):
    """Detects complexity-related code quality issues."""
    
    def detect(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Detect complexity issues.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            List of detected issues
        """
        self.clear_issues()
        
        max_lines = self.config.get_threshold('max_function_lines')
        max_nesting = self.config.get_threshold('max_nesting_depth')
        
        for pf in parsed_files:
            self._check_file_complexity(pf, max_lines, max_nesting)
        
        return self.get_issues()
    
    def _check_file_complexity(self, pf: ParsedFile, max_lines: int, max_nesting: int):
        """Check complexity issues in a file."""
        for defn in pf.definitions:
            # Check function length
            func_length = defn.line_end - defn.line_start + 1
            
            if func_length > max_lines:
                self.add_issue(Issue(
                    severity=IssueSeverity.WARNING,
                    category="Long Function",
                    message=f"Function '{defn.name}' is {func_length} lines (max: {max_lines})",
                    file_path=pf.file_path,
                    line=defn.line_start,
                    line_end=defn.line_end,
                    code_snippet=self._get_code_snippet(pf.file_path, defn.line_start),
                    suggestion="Consider breaking this function into smaller functions",
                    metadata={
                        "function_name": defn.name,
                        "length": func_length,
                        "threshold": max_lines
                    }
                ))
            
            # Check nesting depth
            if defn.nesting_depth > max_nesting:
                self.add_issue(Issue(
                    severity=IssueSeverity.WARNING,
                    category="Deep Nesting",
                    message=f"Function '{defn.name}' has nesting depth {defn.nesting_depth} (max: {max_nesting})",
                    file_path=pf.file_path,
                    line=defn.line_start,
                    code_snippet=self._get_code_snippet(pf.file_path, defn.line_start),
                    suggestion="Reduce nesting by extracting functions or using early returns",
                    metadata={
                        "function_name": defn.name,
                        "depth": defn.nesting_depth,
                        "threshold": max_nesting
                    }
                ))
        
        # Check for problematic error handling
        self._check_error_handling(pf)
    
    def _check_error_handling(self, pf: ParsedFile):
        """Check for poor error handling patterns."""
        lines = pf.raw_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Python: empty except blocks
            if pf.language == 'python':
                if stripped == 'pass' and i > 1:
                    # Check if previous line is except
                    prev_line = lines[i-2].strip() if i > 1 else ''
                    if prev_line.startswith('except'):
                        self.add_issue(Issue(
                            severity=IssueSeverity.ERROR,
                            category="Empty Exception Handler",
                            message="Empty except block with only 'pass'",
                            file_path=pf.file_path,
                            line=i-1,
                            code_snippet=self._get_code_snippet(pf.file_path, i-1, context=3),
                            suggestion="Add proper error handling or at least log the exception",
                            metadata={"pattern": "empty_except"}
                        ))
                
                # Bare except
                if re.match(r'except\s*:', stripped):
                    self.add_issue(Issue(
                        severity=IssueSeverity.WARNING,
                        category="Bare Exception",
                        message="Bare except clause catches all exceptions",
                        file_path=pf.file_path,
                        line=i,
                        code_snippet=self._get_code_snippet(pf.file_path, i),
                        suggestion="Catch specific exceptions instead of using bare except",
                        metadata={"pattern": "bare_except"}
                    ))
                
                # Generic exception catch
                if re.match(r'except\s+Exception\s*:', stripped):
                    self.add_issue(Issue(
                        severity=IssueSeverity.INFO,
                        category="Generic Exception",
                        message="Catching generic Exception",
                        file_path=pf.file_path,
                        line=i,
                        code_snippet=self._get_code_snippet(pf.file_path, i),
                        suggestion="Consider catching more specific exceptions",
                        metadata={"pattern": "generic_exception"}
                    ))
            
            # JavaScript/TypeScript: empty catch blocks
            elif pf.language in ('javascript', 'typescript'):
                if stripped.startswith('catch') and '{' in stripped:
                    # Check if next few lines are just closing brace
                    catch_block = []
                    brace_count = stripped.count('{') - stripped.count('}')
                    j = i
                    
                    while j < len(lines) and brace_count > 0:
                        catch_block.append(lines[j].strip())
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        j += 1
                    
                    # Remove empty lines
                    catch_block = [line for line in catch_block if line and line != '}']
                    
                    # If only catch statement, it's empty
                    if len(catch_block) <= 1:
                        self.add_issue(Issue(
                            severity=IssueSeverity.ERROR,
                            category="Empty Catch Block",
                            message="Empty catch block",
                            file_path=pf.file_path,
                            line=i,
                            code_snippet=self._get_code_snippet(pf.file_path, i, context=3),
                            suggestion="Add proper error handling or at least log the error",
                            metadata={"pattern": "empty_catch"}
                        ))

