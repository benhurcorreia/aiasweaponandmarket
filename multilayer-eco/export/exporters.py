"""
MultilayerEco - Export Module
Exportação de projetos para imagem e dados.
"""
import json
import csv
import os
from core.models import Project


def export_json(project: Project, filepath: str):
    """Export full project as JSON."""
    data = project.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_actors_csv(project: Project, filepath: str):
    """Export actors as CSV."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nome", "Tipo", "Camadas", "Num_Camadas"])
        for actor in project.actors.values():
            layer_names = []
            for lid in actor.layers:
                layer = project.get_layer_by_id(lid)
                if layer:
                    layer_names.append(layer.name)
            writer.writerow([
                actor.id,
                actor.name,
                actor.actor_type,
                "; ".join(layer_names),
                len(actor.layers)
            ])


def export_relationships_csv(project: Project, filepath: str):
    """Export relationships as CSV."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Origem", "Destino", "Camada", "Tipo",
            "Direção", "Peso", "Label", "Inter-Camada",
            "Camada_Origem", "Camada_Destino"
        ])
        for rel in project.relationships:
            src = project.actors.get(rel.source_id)
            tgt = project.actors.get(rel.target_id)
            layer = project.get_layer_by_id(rel.layer_id)
            src_layer = project.get_layer_by_id(rel.source_layer_id)
            tgt_layer = project.get_layer_by_id(rel.target_layer_id)

            writer.writerow([
                rel.id,
                src.name if src else rel.source_id,
                tgt.name if tgt else rel.target_id,
                layer.name if layer else "",
                rel.rel_type,
                rel.direction,
                rel.weight,
                rel.label,
                "Sim" if rel.is_inter_layer else "Não",
                src_layer.name if src_layer else "",
                tgt_layer.name if tgt_layer else "",
            ])


def export_metrics_csv(project: Project, filepath: str):
    """Export network metrics as CSV."""
    from core.graph_engine import GraphEngine
    engine = GraphEngine(project)

    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Camada", "Nós", "Arestas", "Densidade",
            "Centralidade_Grau_Média", "Betweenness_Média",
            "Coef_Clustering"
        ])
        for layer in project.layers:
            m = engine.get_layer_metrics(layer.id)
            writer.writerow([
                layer.name,
                m.get("nodes", 0),
                m.get("edges", 0),
                f"{m.get('density', 0):.4f}",
                f"{m.get('avg_degree_centrality', 0):.4f}",
                f"{m.get('avg_betweenness', 0):.4f}",
                f"{m.get('clustering_coeff', 0):.4f}",
            ])

        # Cross-layer stats
        stats = engine.get_cross_layer_stats()
        writer.writerow([])
        writer.writerow(["Estatísticas Inter-Camada"])
        writer.writerow(["Total Atores", stats["total_actors"]])
        writer.writerow(["Total Relações", stats["total_relationships"]])
        writer.writerow(["Relações Inter-Camada", stats["inter_layer_relationships"]])
        for pair, count in stats["shared_actors"].items():
            writer.writerow([f"Atores Compartilhados ({pair})", count])
