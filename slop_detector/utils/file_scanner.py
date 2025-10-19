"""File scanner that respects .gitignore patterns."""

import os
from pathlib import Path
from typing import List, Set
import pathspec


class FileInfo:
    """Information about a scanned file."""
    
    def __init__(self, path: str, size: int, language: str):
        self.path = path
        self.size = size
        self.language = language
        self.relative_path = path
        
    def __repr__(self):
        return f"FileInfo(path={self.path}, language={self.language})"


class FileScanner:
    """Scans directory for source files while respecting .gitignore."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
    }
    
    DEFAULT_IGNORE_PATTERNS = [
        'node_modules/',
        '__pycache__/',
        '.git/',
        'venv/',
        'env/',
        '.env/',
        'dist/',
        'build/',
        '.next/',
        '.nuxt/',
        'coverage/',
        '.pytest_cache/',
        '.mypy_cache/',
        '.tox/',
        '*.pyc',
        '*.pyo',
        '*.egg-info/',
        '.DS_Store',
    ]
    
    def __init__(self, root_dir: str, additional_ignore: List[str] = None):
        self.root_dir = Path(root_dir).resolve()
        self.additional_ignore = additional_ignore or []
        self.gitignore_spec = self._load_gitignore()
        
    def _load_gitignore(self) -> pathspec.PathSpec:
        """Load .gitignore patterns."""
        patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        
        # Add additional ignore patterns
        patterns.extend(self.additional_ignore)
        
        # Load .gitignore file if it exists
        gitignore_path = self.root_dir / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        try:
            relative_path = path.relative_to(self.root_dir)
            rel_str = str(relative_path)
            
            # Check against gitignore patterns
            if self.gitignore_spec.match_file(rel_str):
                return True
            
            # Check if it's a directory we should skip
            if path.is_dir() and self.gitignore_spec.match_file(rel_str + '/'):
                return True
                
            return False
        except ValueError:
            # Path is not relative to root_dir
            return True
    
    def scan(self) -> List[FileInfo]:
        """Scan directory for source files."""
        files = []
        
        for root, dirs, filenames in os.walk(self.root_dir):
            root_path = Path(root)
            
            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs 
                if not self._should_ignore(root_path / d)
            ]
            
            for filename in filenames:
                file_path = root_path / filename
                
                # Check if file should be ignored
                if self._should_ignore(file_path):
                    continue
                
                # Check if file has a supported extension
                ext = file_path.suffix
                if ext in self.LANGUAGE_EXTENSIONS:
                    try:
                        size = file_path.stat().st_size
                        language = self.LANGUAGE_EXTENSIONS[ext]
                        relative = str(file_path.relative_to(self.root_dir))
                        
                        file_info = FileInfo(
                            path=str(file_path),
                            size=size,
                            language=language
                        )
                        file_info.relative_path = relative
                        files.append(file_info)
                    except (OSError, ValueError):
                        continue
        
        return files

