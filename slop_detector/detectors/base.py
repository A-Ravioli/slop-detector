"""Base detector class for code quality issues."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Any
from enum import Enum


class IssueSeverity(Enum):
    """Severity levels for detected issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Issue:
    """Represents a detected code quality issue."""
    severity: IssueSeverity
    category: str
    message: str
    file_path: str
    line: int = 0
    line_end: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    metadata: dict = field(default_factory=dict)
    
    def __str__(self):
        location = f"{self.file_path}:{self.line}" if self.line else self.file_path
        return f"[{self.severity.value.upper()}] {self.category}: {self.message} ({location})"


class BaseDetector(ABC):
    """Abstract base class for detectors."""
    
    def __init__(self, config):
        self.config = config
        self.issues: List[Issue] = []
    
    @abstractmethod
    def detect(self, *args, **kwargs) -> List[Issue]:
        """Run detection and return list of issues."""
        pass
    
    def get_issues(self) -> List[Issue]:
        """Get all detected issues."""
        return self.issues
    
    def clear_issues(self):
        """Clear all detected issues."""
        self.issues = []
    
    def add_issue(self, issue: Issue):
        """Add an issue to the list."""
        self.issues.append(issue)
    
    def _get_code_snippet(self, file_path: str, line: int, context: int = 2) -> str:
        """Get code snippet around a line.
        
        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            context: Number of lines to include before and after
            
        Returns:
            Code snippet as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line - context - 1)
            end = min(len(lines), line + context)
            
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>>" if i == line - 1 else "   "
                snippet_lines.append(f"{prefix} {i+1:4d} | {lines[i].rstrip()}")
            
            return '\n'.join(snippet_lines)
        except:
            return ""

