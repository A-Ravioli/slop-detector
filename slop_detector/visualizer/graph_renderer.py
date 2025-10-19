"""Graph visualization renderer."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import networkx as nx
from jinja2 import Environment, FileSystemLoader


class GraphRenderer:
    """Renders dependency graphs as interactive HTML."""
    
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render(self, graph: nx.DiGraph, output_path: str, 
               title: str = "Dependency Graph",
               issues_by_file: Dict[str, List] = None) -> str:
        """Render graph as interactive HTML.
        
        Args:
            graph: NetworkX graph to render
            output_path: Path to output HTML file
            title: Title for the visualization
            issues_by_file: Dictionary mapping file paths to lists of issues
            
        Returns:
            Path to generated HTML file
        """
        issues_by_file = issues_by_file or {}
        
        # Convert NetworkX graph to Cytoscape.js format
        cytoscape_data = self._convert_to_cytoscape(graph, issues_by_file)
        
        # Get template
        template = self.env.get_template('graph.html')
        
        # Render template
        html_content = template.render(
            title=title,
            graph_data=json.dumps(cytoscape_data),
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges()
        )
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _convert_to_cytoscape(self, graph: nx.DiGraph, 
                             issues_by_file: Dict[str, List]) -> Dict:
        """Convert NetworkX graph to Cytoscape.js format."""
        elements = []
        
        # Add nodes
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            
            # Count issues for this node
            file_path = node_data.get('file_path', node_id)
            node_issues = issues_by_file.get(file_path, [])
            issue_count = len(node_issues)
            
            # Determine node color based on issues
            color = self._get_node_color(node_data, node_issues)
            
            # Categorize issues
            issue_summary = self._summarize_issues(node_issues)
            
            # Determine node size based on LOC or other metrics
            size = self._calculate_node_size(node_data)
            
            elements.append({
                'data': {
                    'id': node_id,
                    'label': self._get_node_label(node_id, node_data),
                    'cluster': node_data.get('cluster', ''),
                    'type': node_data.get('type', 'file'),
                    'language': node_data.get('language', ''),
                    'lines_of_code': node_data.get('lines_of_code', 0),
                    'issue_count': issue_count,
                    'issues': issue_summary,
                    'in_cycle': node_data.get('in_cycle', False),
                    'file_path': file_path,
                },
                'classes': self._get_node_classes(node_data, node_issues),
                'style': {
                    'background-color': color,
                    'width': size,
                    'height': size,
                }
            })
        
        # Add edges
        for source, target in graph.edges():
            edge_data = graph.edges[source, target]
            
            # Determine edge color
            edge_color = '#3498db'  # Default blue
            if edge_data.get('in_cycle', False):
                edge_color = '#e74c3c'  # Red for circular dependencies
            
            elements.append({
                'data': {
                    'id': f"{source}->{target}",
                    'source': source,
                    'target': target,
                    'type': edge_data.get('import_type', 'direct'),
                },
                'classes': 'cycle' if edge_data.get('in_cycle', False) else '',
                'style': {
                    'line-color': edge_color,
                    'target-arrow-color': edge_color,
                }
            })
        
        return {'elements': elements}
    
    def _get_node_color(self, node_data: Dict, issues: List) -> str:
        """Determine node color based on issues and data."""
        if not issues:
            return '#2ecc71'  # Green - no issues
        
        # Check severity
        has_error = any(issue.severity.value in ('error', 'critical') for issue in issues)
        has_warning = any(issue.severity.value == 'warning' for issue in issues)
        
        if has_error:
            return '#e74c3c'  # Red - has errors
        elif has_warning:
            return '#f39c12'  # Orange - has warnings
        else:
            return '#f1c40f'  # Yellow - has info issues
    
    def _calculate_node_size(self, node_data: Dict) -> int:
        """Calculate node size based on metrics."""
        loc = node_data.get('lines_of_code', 0)
        
        # Scale size based on LOC
        if loc == 0:
            return 30
        elif loc < 50:
            return 40
        elif loc < 200:
            return 50
        elif loc < 500:
            return 60
        else:
            return 70
    
    def _get_node_label(self, node_id: str, node_data: Dict) -> str:
        """Get display label for node."""
        # For entity graphs, use the entity name
        if '::' in node_id:
            return node_id.split('::')[1]
        
        # For file graphs, use filename
        return os.path.basename(node_id)
    
    def _get_node_classes(self, node_data: Dict, issues: List) -> str:
        """Get CSS classes for node."""
        classes = []
        
        if node_data.get('in_cycle', False):
            classes.append('cycle')
        
        if issues:
            has_error = any(issue.severity.value in ('error', 'critical') for issue in issues)
            if has_error:
                classes.append('has-errors')
            else:
                classes.append('has-warnings')
        
        return ' '.join(classes)
    
    def _summarize_issues(self, issues: List) -> Dict[str, int]:
        """Summarize issues by category."""
        summary = {}
        
        for issue in issues:
            category = issue.category
            summary[category] = summary.get(category, 0) + 1
        
        return summary

