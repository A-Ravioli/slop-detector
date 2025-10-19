"""Detector for comment-related code quality issues."""

import re
from typing import List
from .base import BaseDetector, Issue, IssueSeverity
from ..parsers.base import ParsedFile, Comment


class CommentDetector(BaseDetector):
    """Detects problematic comments and documentation."""
    
    # Patterns for different types of slop comments
    PLACEHOLDER_PATTERNS = [
        r'\bTODO\b',
        r'\bFIXME\b',
        r'\bHACK\b',
        r'\bXXX\b',
        r'\bNOTE\b',
        r'add\s+implementation',
        r'your\s+code\s+here',
        r'fill\s+this\s+in',
        r'implement\s+this',
        r'to\s+be\s+implemented',
    ]
    
    OBSOLETE_PATTERNS = [
        r'\blegacy\b',
        r'backwards?\s+compatibility',
        r'\bdeprecated\b',
        r'old\s+code',
        r'don\'?t\s+use',
        r'no\s+longer\s+needed',
        r'remove\s+this',
    ]
    
    # Patterns that might indicate commented-out code
    CODE_PATTERNS = [
        r'^\s*#\s*(def|class|import|from|if|for|while|return|print)\s',  # Python
        r'^\s*//\s*(function|const|let|var|class|import|export|if|for|while|return)\s',  # JS
        r'^\s*//\s*\w+\s*\(',  # Function calls
    ]
    
    def detect(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Detect comment-related issues.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            List of detected issues
        """
        self.clear_issues()
        
        for pf in parsed_files:
            self._check_file_comments(pf)
        
        return self.get_issues()
    
    def _check_file_comments(self, pf: ParsedFile):
        """Check all comments in a file."""
        for comment in pf.comments:
            # Check for placeholder comments
            self._check_placeholder(comment, pf)
            
            # Check for obsolete markers
            self._check_obsolete(comment, pf)
            
            # Check for commented-out code
            if not comment.is_docstring:
                self._check_commented_code(comment, pf)
            
            # Check for obvious/redundant comments
            if not comment.is_docstring:
                self._check_obvious_comment(comment, pf)
            
            # Check for generic AI docstrings
            if comment.is_docstring:
                self._check_generic_docstring(comment, pf)
    
    def _check_placeholder(self, comment: Comment, pf: ParsedFile):
        """Check for placeholder comments."""
        text_lower = comment.text.lower()
        
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.add_issue(Issue(
                    severity=IssueSeverity.WARNING,
                    category="Placeholder Comment",
                    message=f"Incomplete code marker: {comment.text[:50]}...",
                    file_path=pf.file_path,
                    line=comment.line,
                    code_snippet=self._get_code_snippet(pf.file_path, comment.line),
                    suggestion="Complete the implementation or remove the marker",
                    metadata={"comment_text": comment.text}
                ))
                break
    
    def _check_obsolete(self, comment: Comment, pf: ParsedFile):
        """Check for obsolete code markers."""
        text_lower = comment.text.lower()
        
        for pattern in self.OBSOLETE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.add_issue(Issue(
                    severity=IssueSeverity.ERROR,
                    category="Obsolete Code",
                    message=f"Potentially obsolete code: {comment.text[:50]}...",
                    file_path=pf.file_path,
                    line=comment.line,
                    code_snippet=self._get_code_snippet(pf.file_path, comment.line),
                    suggestion="Consider removing deprecated/legacy code",
                    metadata={"comment_text": comment.text}
                ))
                break
    
    def _check_commented_code(self, comment: Comment, pf: ParsedFile):
        """Check if comment contains commented-out code."""
        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, comment.text):
                self.add_issue(Issue(
                    severity=IssueSeverity.WARNING,
                    category="Commented Code",
                    message="Commented-out code found",
                    file_path=pf.file_path,
                    line=comment.line,
                    code_snippet=self._get_code_snippet(pf.file_path, comment.line),
                    suggestion="Remove commented code or uncomment if needed",
                    metadata={"comment_text": comment.text}
                ))
                break
    
    def _check_obvious_comment(self, comment: Comment, pf: ParsedFile):
        """Check for comments that just restate the code."""
        text_lower = comment.text.lower()
        
        # Get the next line of actual code
        try:
            with open(pf.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if comment.line < len(lines):
                next_line = lines[comment.line].strip().lower()
                
                # Check if comment just restates variable operations
                obvious_patterns = [
                    (r'increment', r'\+=\s*1'),
                    (r'decrement', r'-=\s*1'),
                    (r'set.*to', r'='),
                    (r'return', r'return'),
                    (r'print', r'(print|console\.log)'),
                ]
                
                for comment_pattern, code_pattern in obvious_patterns:
                    if re.search(comment_pattern, text_lower) and re.search(code_pattern, next_line):
                        # Extract key words from comment and code
                        comment_words = set(re.findall(r'\w+', text_lower))
                        code_words = set(re.findall(r'\w+', next_line))
                        
                        # If significant overlap, it's probably obvious
                        if len(comment_words & code_words) >= 2:
                            self.add_issue(Issue(
                                severity=IssueSeverity.INFO,
                                category="Obvious Comment",
                                message=f"Comment restates code: {comment.text[:40]}...",
                                file_path=pf.file_path,
                                line=comment.line,
                                code_snippet=self._get_code_snippet(pf.file_path, comment.line),
                                suggestion="Remove redundant comment",
                                metadata={"comment_text": comment.text}
                            ))
                            break
        except:
            pass
    
    def _check_generic_docstring(self, comment: Comment, pf: ParsedFile):
        """Check for generic AI-generated docstrings."""
        if not comment.parent_entity:
            return
        
        text_lower = comment.text.lower()
        entity_lower = comment.parent_entity.lower()
        
        # Check if docstring just rewords the function name
        entity_words = set(re.findall(r'[a-z]+', entity_lower))
        doc_words = set(re.findall(r'[a-z]+', text_lower))
        
        # Generic phrases that add no value
        generic_phrases = [
            r'^' + re.escape(entity_lower),  # Just repeats name
            r'this\s+(function|method|class)\s+' + re.escape(entity_lower),
            r'^(function|method|class)\s+to\s+' + re.escape(entity_lower),
        ]
        
        for phrase in generic_phrases:
            if re.search(phrase, text_lower):
                self.add_issue(Issue(
                    severity=IssueSeverity.INFO,
                    category="Generic Docstring",
                    message=f"Docstring adds no value beyond function name",
                    file_path=pf.file_path,
                    line=comment.line,
                    code_snippet=self._get_code_snippet(pf.file_path, comment.line),
                    suggestion="Add meaningful documentation or remove docstring",
                    metadata={"comment_text": comment.text, "entity": comment.parent_entity}
                ))
                break
        
        # Check if docstring is too short to be useful (< 10 words)
        word_count = len(text_lower.split())
        if word_count > 0 and word_count < 10:
            # And if it mostly just contains the function name words
            overlap = len(entity_words & doc_words)
            if overlap / len(entity_words) > 0.7:
                self.add_issue(Issue(
                    severity=IssueSeverity.INFO,
                    category="Generic Docstring",
                    message="Docstring is too generic",
                    file_path=pf.file_path,
                    line=comment.line,
                    suggestion="Expand docstring with meaningful details",
                    metadata={"comment_text": comment.text}
                ))

