"""Graph analysis for detecting issues."""

from typing import List, Set, Dict, Tuple
import networkx as nx


class GraphAnalyzer:
    """Analyzes dependency graphs for issues."""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph.
        
        Returns:
            List of cycles, where each cycle is a list of node names
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            # Sort cycles by length (shortest first) and filter out self-loops
            cycles = [c for c in cycles if len(c) > 1]
            cycles.sort(key=len)
            return cycles
        except:
            return []
    
    def find_isolated_nodes(self) -> List[str]:
        """Find nodes with no incoming or outgoing edges.
        
        Returns:
            List of isolated node names
        """
        isolated = []
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            if in_degree == 0 and out_degree == 0:
                isolated.append(node)
        
        return isolated
    
    def find_stranded_nodes(self, entry_points: List[str] = None) -> List[str]:
        """Find nodes that are never imported/used (no incoming edges).
        
        Args:
            entry_points: List of entry point file names that shouldn't be flagged
            
        Returns:
            List of stranded node names
        """
        entry_points = entry_points or []
        stranded = []
        
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            
            # Check if it's an entry point
            is_entry_point = any(ep in node for ep in entry_points)
            
            if in_degree == 0 and not is_entry_point:
                stranded.append(node)
        
        return stranded
    
    def calculate_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality for all nodes.
        
        Returns:
            Dictionary mapping node names to centrality scores
        """
        try:
            return nx.betweenness_centrality(self.graph)
        except:
            return {}
    
    def get_dependencies(self, node: str) -> Set[str]:
        """Get all direct dependencies of a node.
        
        Args:
            node: Node name
            
        Returns:
            Set of dependency node names
        """
        if node not in self.graph:
            return set()
        
        return set(self.graph.successors(node))
    
    def get_dependents(self, node: str) -> Set[str]:
        """Get all nodes that depend on this node.
        
        Args:
            node: Node name
            
        Returns:
            Set of dependent node names
        """
        if node not in self.graph:
            return set()
        
        return set(self.graph.predecessors(node))
    
    def get_node_data(self, node: str) -> Dict:
        """Get data associated with a node.
        
        Args:
            node: Node name
            
        Returns:
            Dictionary of node attributes
        """
        if node not in self.graph:
            return {}
        
        return dict(self.graph.nodes[node])
    
    def get_clusters(self) -> Dict[str, List[str]]:
        """Group nodes by their cluster attribute.
        
        Returns:
            Dictionary mapping cluster names to lists of node names
        """
        clusters = {}
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            cluster = node_data.get('cluster', 'unknown')
            
            if cluster not in clusters:
                clusters[cluster] = []
            
            clusters[cluster].append(node)
        
        return clusters
    
    def mark_cycles(self) -> None:
        """Mark nodes and edges that are part of cycles."""
        cycles = self.find_circular_dependencies()
        
        # Create set of all nodes in cycles
        nodes_in_cycles = set()
        for cycle in cycles:
            nodes_in_cycles.update(cycle)
        
        # Mark nodes
        for node in self.graph.nodes():
            self.graph.nodes[node]['in_cycle'] = node in nodes_in_cycles
        
        # Mark edges
        for cycle in cycles:
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                
                if self.graph.has_edge(source, target):
                    self.graph.edges[source, target]['in_cycle'] = True

