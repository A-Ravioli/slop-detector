"""Graph construction for dependency visualization."""

import os
from pathlib import Path
from typing import List, Dict, Set, Tuple
import networkx as nx
from ..parsers.base import ParsedFile, Definition, EntityType


class GraphBuilder:
    """Builds dependency graphs from parsed files."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.file_graph = nx.DiGraph()
        self.entity_graph = nx.DiGraph()
        
    def build_file_graph(self, parsed_files: List[ParsedFile]) -> nx.DiGraph:
        """Build file-level dependency graph.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            NetworkX directed graph with files as nodes
        """
        self.file_graph.clear()
        
        # Create mapping from module paths to file paths
        module_to_file = self._create_module_mapping(parsed_files)
        
        # Add nodes for each file
        for pf in parsed_files:
            rel_path = self._get_relative_path(pf.file_path)
            cluster = self._get_cluster(rel_path)
            
            self.file_graph.add_node(
                rel_path,
                file_path=pf.file_path,
                language=pf.language,
                lines_of_code=pf.lines_of_code,
                cluster=cluster,
                num_definitions=len(pf.definitions),
                num_imports=len(pf.imports)
            )
        
        # Add edges based on imports
        for pf in parsed_files:
            source = self._get_relative_path(pf.file_path)
            
            for imp in pf.imports:
                # Resolve import to file path
                target_files = self._resolve_import(imp.module, pf.file_path, module_to_file, parsed_files)
                
                for target in target_files:
                    if target in self.file_graph:
                        self.file_graph.add_edge(source, target, import_type='direct')
        
        return self.file_graph
    
    def build_entity_graph(self, parsed_files: List[ParsedFile]) -> nx.DiGraph:
        """Build entity-level dependency graph.
        
        Args:
            parsed_files: List of parsed file objects
            
        Returns:
            NetworkX directed graph with functions/classes as nodes
        """
        self.entity_graph.clear()
        
        # Create mapping from entity names to their file and definition
        entity_map: Dict[str, Tuple[str, Definition]] = {}
        
        # Add nodes for each entity
        for pf in parsed_files:
            rel_path = self._get_relative_path(pf.file_path)
            
            for defn in pf.definitions:
                # Create unique entity ID
                if defn.parent:
                    entity_id = f"{rel_path}::{defn.parent}.{defn.name}"
                else:
                    entity_id = f"{rel_path}::{defn.name}"
                
                entity_map[defn.name] = (rel_path, defn)
                if defn.parent:
                    full_name = f"{defn.parent}.{defn.name}"
                    entity_map[full_name] = (rel_path, defn)
                
                self.entity_graph.add_node(
                    entity_id,
                    name=defn.name,
                    type=defn.type.value,
                    file=rel_path,
                    cluster=rel_path,
                    line_start=defn.line_start,
                    line_end=defn.line_end,
                    nesting_depth=defn.nesting_depth,
                    parent=defn.parent
                )
        
        # Add edges based on calls
        for pf in parsed_files:
            rel_path = self._get_relative_path(pf.file_path)
            
            for defn in pf.definitions:
                # Source entity ID
                if defn.parent:
                    source_id = f"{rel_path}::{defn.parent}.{defn.name}"
                else:
                    source_id = f"{rel_path}::{defn.name}"
                
                # Add edges for each call
                for call in defn.calls:
                    # Try to resolve call to an entity
                    if call in entity_map:
                        target_file, target_defn = entity_map[call]
                        
                        if target_defn.parent:
                            target_id = f"{target_file}::{target_defn.parent}.{target_defn.name}"
                        else:
                            target_id = f"{target_file}::{target_defn.name}"
                        
                        if target_id in self.entity_graph and source_id != target_id:
                            self.entity_graph.add_edge(source_id, target_id, call_type='direct')
        
        return self.entity_graph
    
    def _create_module_mapping(self, parsed_files: List[ParsedFile]) -> Dict[str, str]:
        """Create mapping from module names to file paths."""
        module_map = {}
        
        for pf in parsed_files:
            rel_path = self._get_relative_path(pf.file_path)
            
            # Python module path
            if pf.language == 'python':
                # Convert file path to module path
                module_parts = rel_path.replace('.py', '').split(os.sep)
                module_name = '.'.join(module_parts)
                module_map[module_name] = rel_path
                
                # Also map just the filename
                filename = os.path.basename(rel_path).replace('.py', '')
                if filename not in module_map:
                    module_map[filename] = rel_path
            
            # JavaScript/TypeScript module path
            else:
                # Remove extension
                module_path = rel_path
                for ext in ['.js', '.jsx', '.ts', '.tsx']:
                    if module_path.endswith(ext):
                        module_path = module_path[:-len(ext)]
                        break
                
                module_map[module_path] = rel_path
                
                # Map with ./ prefix
                module_map['./' + module_path] = rel_path
                
                # Map just filename
                filename = os.path.basename(module_path)
                if filename not in module_map:
                    module_map[filename] = rel_path
        
        return module_map
    
    def _resolve_import(self, module: str, source_file: str, 
                       module_map: Dict[str, str], 
                       parsed_files: List[ParsedFile]) -> List[str]:
        """Resolve import statement to actual file paths."""
        resolved = []
        
        # Direct match in module map
        if module in module_map:
            resolved.append(module_map[module])
            return resolved
        
        # Try relative imports
        if module.startswith('.'):
            source_dir = os.path.dirname(self._get_relative_path(source_file))
            
            # Calculate relative path
            parts = module.split('/')
            current_dir = source_dir
            
            for part in parts:
                if part == '.':
                    continue
                elif part == '..':
                    current_dir = os.path.dirname(current_dir)
                else:
                    current_dir = os.path.join(current_dir, part)
            
            # Try various extensions
            for ext in ['', '.py', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']:
                candidate = current_dir + ext
                if candidate in module_map:
                    resolved.append(module_map[candidate])
                    break
        
        # Try absolute path resolution
        else:
            # For Python, try as package import
            for pf in parsed_files:
                rel_path = self._get_relative_path(pf.file_path)
                
                # Check if module path matches file path
                if module.replace('.', os.sep) in rel_path:
                    resolved.append(rel_path)
        
        return resolved
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get path relative to root directory."""
        try:
            return str(Path(file_path).relative_to(self.root_dir))
        except ValueError:
            return os.path.basename(file_path)
    
    def _get_cluster(self, rel_path: str) -> str:
        """Get cluster name from file path (directory)."""
        dirname = os.path.dirname(rel_path)
        return dirname if dirname else '.'

