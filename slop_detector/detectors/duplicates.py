"""Detector for duplicate code blocks."""

import re
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from .base import BaseDetector, Issue, IssueSeverity
from ..parsers.base import ParsedFile


class DuplicateDetector(BaseDetector):
    """Detects duplicate code blocks."""
    
    def detect(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Detect duplicate code.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            List of detected issues
        """
        self.clear_issues()
        
        min_lines = self.config.get_threshold('min_duplicate_lines')
        
        # Find duplicates
        duplicates = self._find_duplicates(parsed_files, min_lines)
        
        # Report duplicates
        for signature, locations in duplicates.items():
            if len(locations) > 1:
                # Create issue for each duplicate instance
                for i, (file_path, line_start, line_end, code) in enumerate(locations):
                    other_locations = [loc for j, loc in enumerate(locations) if j != i]
                    other_refs = [f"{loc[0]}:{loc[1]}" for loc in other_locations[:3]]
                    
                    self.add_issue(Issue(
                        severity=IssueSeverity.WARNING,
                        category="Duplicate Code",
                        message=f"Duplicate code found ({len(locations)} instances)",
                        file_path=file_path,
                        line=line_start,
                        line_end=line_end,
                        code_snippet=self._get_code_snippet(file_path, line_start),
                        suggestion=f"Consider extracting to a shared function. Also found at: {', '.join(other_refs)}",
                        metadata={
                            "duplicate_count": len(locations),
                            "other_locations": other_refs,
                            "lines": line_end - line_start + 1
                        }
                    ))
        
        return self.get_issues()
    
    def _find_duplicates(self, parsed_files: List[ParsedFile], min_lines: int) -> Dict[str, List[Tuple]]:
        """Find duplicate code blocks.
        
        Returns:
            Dictionary mapping signature to list of (file, line_start, line_end, code) tuples
        """
        # Map from normalized code signature to locations
        signatures: Dict[str, List[Tuple]] = defaultdict(list)
        
        for pf in parsed_files:
            lines = pf.raw_content.split('\n')
            
            # Sliding window approach
            for start_idx in range(len(lines) - min_lines + 1):
                for window_size in range(min_lines, min(len(lines) - start_idx + 1, min_lines + 20)):
                    window_lines = lines[start_idx:start_idx + window_size]
                    
                    # Normalize and create signature
                    normalized = self._normalize_code(window_lines)
                    
                    if normalized:  # Skip if empty after normalization
                        signature = self._create_signature(normalized)
                        
                        if signature:
                            code_text = '\n'.join(window_lines)
                            signatures[signature].append((
                                pf.file_path,
                                start_idx + 1,
                                start_idx + window_size,
                                code_text
                            ))
        
        # Filter out signatures that only appear once
        duplicates = {sig: locs for sig, locs in signatures.items() if len(locs) > 1}
        
        # Remove overlapping duplicates (keep longest)
        duplicates = self._remove_overlapping_duplicates(duplicates)
        
        return duplicates
    
    def _normalize_code(self, lines: List[str]) -> List[str]:
        """Normalize code for comparison."""
        normalized = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Skip comments
            if stripped.startswith(('#', '//', '/*', '*')):
                continue
            
            # Normalize whitespace
            normalized_line = re.sub(r'\s+', ' ', stripped)
            
            # Remove string literals (replace with placeholder)
            normalized_line = re.sub(r'"[^"]*"', '"STRING"', normalized_line)
            normalized_line = re.sub(r"'[^']*'", "'STRING'", normalized_line)
            
            # Remove numbers (replace with placeholder)
            normalized_line = re.sub(r'\b\d+\b', 'NUM', normalized_line)
            
            normalized.append(normalized_line)
        
        return normalized
    
    def _create_signature(self, normalized_lines: List[str]) -> str:
        """Create a signature from normalized lines."""
        if len(normalized_lines) < 3:  # Need at least 3 lines
            return ""
        
        # Join lines into signature
        signature = '|||'.join(normalized_lines)
        
        # Only return if it's substantial enough
        if len(signature) > 50:  # Arbitrary threshold
            return signature
        
        return ""
    
    def _remove_overlapping_duplicates(self, duplicates: Dict[str, List[Tuple]]) -> Dict[str, List[Tuple]]:
        """Remove overlapping duplicate instances, keeping the longest."""
        # Sort by length (longest first)
        sorted_duplicates = sorted(
            duplicates.items(),
            key=lambda x: max(loc[2] - loc[1] for loc in x[1]),
            reverse=True
        )
        
        kept_duplicates = {}
        used_ranges: Dict[str, Set[Tuple[int, int]]] = defaultdict(set)
        
        for signature, locations in sorted_duplicates:
            # Check if any location overlaps with already kept duplicates
            new_locations = []
            
            for file_path, line_start, line_end, code in locations:
                # Check for overlap
                overlaps = False
                for used_start, used_end in used_ranges[file_path]:
                    if not (line_end < used_start or line_start > used_end):
                        overlaps = True
                        break
                
                if not overlaps:
                    new_locations.append((file_path, line_start, line_end, code))
                    used_ranges[file_path].add((line_start, line_end))
            
            # Only keep if we have at least 2 non-overlapping instances
            if len(new_locations) > 1:
                kept_duplicates[signature] = new_locations
        
        return kept_duplicates

