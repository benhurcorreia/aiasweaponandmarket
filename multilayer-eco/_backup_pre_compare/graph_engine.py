"""
MultilayerEco - Graph Engine
Construção, layout e métricas de grafos multicamada usando NetworkX.
"""
import math
import random
import networkx as nx
import numpy as np
from .models import Project, Actor, Layer


class GraphEngine:
    """Engine para construção e análise de grafos multicamada."""

    def __init__(self, project: Project):
        self.project = project
        self._layer_graphs = {}  # {layer_id: nx.Graph}
        self._build_graphs()

    def _build_graphs(self):
        """Constrói grafos NetworkX para cada camada."""
        self._layer_graphs = {}
        for layer in self.project.layers:
            G = nx.Graph()
            actors = self.project.get_actors_in_layer(layer.id)
            for actor in actors:
                G.add_node(actor.id, name=actor.name, actor_type=actor.actor_type)
            rels = self.project.get_relationships_in_layer(layer.id)
            for rel in rels:
                if G.has_node(rel.source_id) and G.has_node(rel.target_id):
                    G.add_edge(rel.source_id, rel.target_id,
                               rel_type=rel.rel_type, weight=rel.weight,
                               label=rel.label)
            self._layer_graphs[layer.id] = G

    def compute_layout(self, layer_id: str, algorithm: str = "spring",
                       width: float = 600, height: float = 400) -> dict:
        """Computa posições para nós de uma camada."""
        G = self._layer_graphs.get(layer_id)
        if G is None or len(G.nodes) == 0:
            return {}

        n = len(G.nodes)
        if n == 1:
            node = list(G.nodes)[0]
            return {node: (width / 2, height / 2)}

        try:
            if algorithm == "spring":
                pos = nx.spring_layout(G, k=2.0 / math.sqrt(max(n, 1)),
                                       iterations=50, seed=42)
            elif algorithm == "circular":
                pos = nx.circular_layout(G)
            elif algorithm == "spectral" and n >= 3:
                pos = nx.spectral_layout(G)
            elif algorithm == "kamada_kawai":
                pos = nx.kamada_kawai_layout(G)
            elif algorithm == "shell":
                pos = nx.shell_layout(G)
            else:
                pos = nx.spring_layout(G, k=2.0 / math.sqrt(max(n, 1)),
                                       iterations=50, seed=42)
        except Exception:
            pos = nx.spring_layout(G, seed=42)

        # Scale to desired dimensions with margin
        margin = 60
        scaled = {}
        if pos:
            xs = [p[0] for p in pos.values()]
            ys = [p[1] for p in pos.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            range_x = max_x - min_x if max_x != min_x else 1
            range_y = max_y - min_y if max_y != min_y else 1

            for node_id, (x, y) in pos.items():
                sx = margin + (x - min_x) / range_x * (width - 2 * margin)
                sy = margin + (y - min_y) / range_y * (height - 2 * margin)
                scaled[node_id] = (sx, sy)

        return scaled

    def compute_all_layouts(self, width: float = 600, height: float = 400,
                            algorithm: str = "spring"):
        """Computa layout para todas as camadas e salva nas posições dos atores."""
        for layer in self.project.layers:
            positions = self.compute_layout(layer.id, algorithm, width, height)
            for actor_id, (x, y) in positions.items():
                if actor_id in self.project.actors:
                    self.project.actors[actor_id].positions[layer.id] = (x, y)

    def get_layer_metrics(self, layer_id: str) -> dict:
        """Calcula métricas de rede para uma camada."""
        G = self._layer_graphs.get(layer_id)
        if G is None or len(G.nodes) == 0:
            return {"nodes": 0, "edges": 0, "density": 0}

        n = len(G.nodes)
        m = len(G.edges)
        metrics = {
            "nodes": n,
            "edges": m,
            "density": nx.density(G),
        }

        if n > 0:
            degree_cent = nx.degree_centrality(G)
            metrics["avg_degree_centrality"] = sum(degree_cent.values()) / n
            if nx.is_connected(G) and n > 2:
                try:
                    between = nx.betweenness_centrality(G)
                    metrics["avg_betweenness"] = sum(between.values()) / n
                except:
                    metrics["avg_betweenness"] = 0
            else:
                metrics["avg_betweenness"] = 0

            try:
                metrics["clustering_coeff"] = nx.average_clustering(G)
            except:
                metrics["clustering_coeff"] = 0

        return metrics

    def get_cross_layer_stats(self) -> dict:
        """Estatísticas inter-camada."""
        layers = self.project.layers
        stats = {
            "total_actors": len(self.project.actors),
            "total_relationships": len(self.project.relationships),
            "inter_layer_relationships": len(self.project.get_inter_layer_relationships()),
            "shared_actors": {},
        }
        # Count actors shared between each pair of layers
        for i, l1 in enumerate(layers):
            for j, l2 in enumerate(layers):
                if j > i:
                    actors_l1 = set(a.id for a in self.project.get_actors_in_layer(l1.id))
                    actors_l2 = set(a.id for a in self.project.get_actors_in_layer(l2.id))
                    shared = actors_l1 & actors_l2
                    stats["shared_actors"][f"{l1.name} ↔ {l2.name}"] = len(shared)
        return stats

    def get_actor_centrality(self, actor_id: str) -> dict:
        """Centralidade de um ator em cada camada."""
        result = {}
        actor = self.project.actors.get(actor_id)
        if not actor:
            return result
        for layer_id in actor.layers:
            G = self._layer_graphs.get(layer_id)
            if G and G.has_node(actor_id):
                dc = nx.degree_centrality(G)
                result[layer_id] = {
                    "degree_centrality": dc.get(actor_id, 0),
                    "degree": G.degree(actor_id),
                }
        return result
