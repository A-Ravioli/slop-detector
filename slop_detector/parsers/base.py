"""Base parser interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Any
from enum import Enum


class EntityType(Enum):
    """Type of code entity."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"


@dataclass
class Comment:
    """Represents a comment in code."""
    text: str
    line: int
    is_docstring: bool = False
    parent_entity: Optional[str] = None


@dataclass
class Import:
    """Represents an import statement."""
    module: str
    names: List[str]
    line: int
    is_star_import: bool = False
    alias: Optional[str] = None


@dataclass
class Definition:
    """Represents a function, class, or method definition."""
    name: str
    type: EntityType
    line_start: int
    line_end: int
    parent: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    nesting_depth: int = 0
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    """Result of parsing a single file."""
    file_path: str
    language: str
    imports: List[Import] = field(default_factory=list)
    definitions: List[Definition] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    lines_of_code: int = 0
    raw_content: str = ""
    
    def get_imported_names(self) -> Set[str]:
        """Get all imported names."""
        names = set()
        for imp in self.imports:
            if imp.is_star_import:
                names.add(imp.module)
            else:
                names.update(imp.names)
                if imp.alias:
                    names.add(imp.alias)
        return names
    
    def get_definition_names(self) -> Set[str]:
        """Get all defined names."""
        return {d.name for d in self.definitions}
    
    def get_all_calls(self) -> Set[str]:
        """Get all function/class calls."""
        calls = set()
        for defn in self.definitions:
            calls.update(defn.calls)
        return calls


class BaseParser(ABC):
    """Abstract base parser for different languages."""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> ParsedFile:
        """Parse a single file and extract information.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParsedFile object with extracted information
        """
        pass
    
    def can_parse(self, language: str) -> bool:
        """Check if parser can handle this language."""
        return False
    
    def _read_file(self, file_path: str) -> str:
        """Read file contents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _count_lines(self, content: str) -> int:
        """Count non-empty, non-comment lines."""
        lines = content.split('\n')
        return len([line for line in lines if line.strip() and not line.strip().startswith(('#', '//'))])

