"""
MultilayerEco - Versatility & Participation Engine
==================================================

Extensão do GraphEngine com as métricas de redes multiplex que sustentam o
argumento do artigo e respondem ao ponto de André e Roberto (separar cada tipo
de relação em uma camada própria para que a versatilidade meça articulação
entre papéis, e não apenas número de parceiros).

Métricas implementadas:

1. Grau de sobreposição (overlapping degree), o_i = Σα k_i^α
   Volume total de conexão do ator somado entre as camadas.

2. Coeficiente de participação multiplex (Battiston, Nicosia & Latora, 2014):
   P_i = (M / (M - 1)) * [ 1 - Σα (k_i^α / o_i)^2 ]
   Vale 0 quando o ator concentra todas as suas arestas em uma única camada
   (papel focado) e 1 quando as distribui uniformemente entre as M camadas
   (papel genuinamente multiplex). É o instrumento direto contra a "inflação":
   um ator concentrado em um único tipo de relação (ex.: Nvidia em fornecimento)
   recebe P próximo de 0, ainda que tenha grau alto.

3. Versatilidade multinível (V_i), na forma usada no artigo:
   V_i = (1 / M) * Σα [ k_i^α / (Nα - 1) ]
   Média, entre as camadas, do grau normalizado do ator em cada camada.

4. Cartografia multiplex: classificação de cada nó combinando o z-score do grau
   de sobreposição (hub vs. regular) com a faixa de participação
   (focado / misto / multiplex), conforme Battiston et al. (2014).

Todas as métricas são calculadas sobre os grafos intracamada já construídos por
GraphEngine._layer_graphs. Logo, esta classe não duplica a construção do grafo:
apenas a estende.

Uso típico:

    from core.models import Project
    from core.versatility import VersatilityEngine

    proj = Project.load("ecossistema_pre.mleco")
    eng = VersatilityEngine(proj)

    # métrica de um ator
    eng.participation_coefficient(actor_id)

    # tabela completa, ordenada por versatilidade
    for aid, m in eng.all_actor_metrics().items():
        print(m["name"], m["versatility"], m["participation"])

    # excluindo a camada de Competição (grafo completo, densidade 1 por
    # definição), que infla a participação de todos os labs ao mesmo tempo:
    eng.all_actor_metrics(exclude=["Competição"])

Nota sobre pesos: por padrão as métricas usam grau não ponderado, coerente com
Battiston et al. (2014) e com a fórmula do artigo. Passe weighted=True para usar
a soma de pesos das arestas; nesse caso a versatilidade pode ultrapassar 1 se
houver pesos maiores que 1, então interprete com cautela.

Nota sobre M (número de camadas): segue a convenção de multiplex node-aligned,
M é o total de camadas consideradas, e camadas onde o ator tem grau 0 entram no
somatório contribuindo com zero. Para comparar dois estados (pré e pós), mantenha
o mesmo conjunto de camadas nos dois, mesmo que alguma fique vazia, para que o
delta seja comparável.
"""

import csv
import math
import networkx as nx

from .graph_engine import GraphEngine


class VersatilityEngine(GraphEngine):
    """GraphEngine acrescido das métricas de redes multiplex."""

    # ── seleção de camadas ────────────────────────────────────────────────
    def _layer_ids(self, exclude=None):
        """IDs das camadas consideradas, em ordem de empilhamento.

        `exclude` aceita ids ou nomes de camadas a ignorar (ex.: ["Competição"]).
        """
        excl = set(exclude or [])
        ids = []
        for layer in sorted(self.project.layers, key=lambda l: l.order):
            if layer.id in excl or layer.name in excl:
                continue
            ids.append(layer.id)
        return ids

    def _degree(self, actor_id, layer_id, weighted=False):
        """Grau do ator em uma camada (0 se ausente)."""
        G = self._layer_graphs.get(layer_id)
        if G is None or not G.has_node(actor_id):
            return 0.0
        if weighted:
            return float(G.degree(actor_id, weight="weight"))
        return float(G.degree(actor_id))

    # ── perfil de grau por camada ─────────────────────────────────────────
    def actor_layer_degrees(self, actor_id, exclude=None, weighted=False):
        """Dicionário {layer_id: grau} do ator em cada camada considerada."""
        return {lid: self._degree(actor_id, lid, weighted)
                for lid in self._layer_ids(exclude)}

    def layer_sizes(self, exclude=None):
        """Número de atores presentes (Nα) em cada camada considerada."""
        sizes = {}
        for lid in self._layer_ids(exclude):
            G = self._layer_graphs.get(lid)
            sizes[lid] = G.number_of_nodes() if G is not None else 0
        return sizes

    # ── métricas centrais ─────────────────────────────────────────────────
    def overlapping_degree(self, actor_id, exclude=None, weighted=False):
        """o_i = Σα k_i^α. Volume total de conexão entre camadas."""
        return sum(self.actor_layer_degrees(actor_id, exclude, weighted).values())

    def participation_coefficient(self, actor_id, exclude=None, weighted=False):
        """P_i de Battiston et al. (2014). Retorna valor em [0, 1].

        0 = todas as arestas em uma única camada (focado);
        1 = arestas uniformemente distribuídas entre as M camadas (multiplex).
        """
        layer_ids = self._layer_ids(exclude)
        M = len(layer_ids)
        if M < 2:
            return 0.0
        degs = self.actor_layer_degrees(actor_id, exclude, weighted)
        o = sum(degs.values())
        if o <= 0:
            return 0.0
        soma_quadrados = sum((k / o) ** 2 for k in degs.values())
        return (M / (M - 1)) * (1.0 - soma_quadrados)

    def versatility(self, actor_id, exclude=None, weighted=False):
        """V_i = (1/M) Σα k_i^α / (Nα - 1). Forma usada no artigo.

        Camadas com Nα <= 1 contribuem 0 (evita divisão por zero).
        """
        layer_ids = self._layer_ids(exclude)
        M = len(layer_ids)
        if M == 0:
            return 0.0
        total = 0.0
        for lid in layer_ids:
            G = self._layer_graphs.get(lid)
            if G is None or not G.has_node(actor_id):
                continue
            n = G.number_of_nodes()
            if n <= 1:
                continue
            k = (G.degree(actor_id, weight="weight") if weighted
                 else G.degree(actor_id))
            total += k / (n - 1)
        return total / M

    def n_layers_present(self, actor_id, exclude=None):
        """Em quantas camadas consideradas o ator tem ao menos uma aresta."""
        c = 0
        for lid in self._layer_ids(exclude):
            G = self._layer_graphs.get(lid)
            if G is not None and G.has_node(actor_id) and G.degree(actor_id) > 0:
                c += 1
        return c

    # ── cartografia multiplex ─────────────────────────────────────────────
    @staticmethod
    def _cartography_label(z_overlap, participation, hub_z=1.0):
        """Rótulo combinando faixa de participação e condição de hub.

        Faixas de participação (Battiston et al., 2014):
          P <= 1/3        -> focado
          1/3 < P <= 2/3  -> misto
          P > 2/3         -> multiplex
        Hub quando o z-score do grau de sobreposição >= hub_z.
        """
        if participation <= 1.0 / 3.0:
            papel = "focado"
        elif participation <= 2.0 / 3.0:
            papel = "misto"
        else:
            papel = "multiplex"
        tipo = "hub" if z_overlap >= hub_z else "regular"
        return f"{papel}/{tipo}"

    # ── tabela completa ───────────────────────────────────────────────────
    def all_actor_metrics(self, exclude=None, weighted=False, hub_z=1.0):
        """Métricas de todos os atores, ordenadas por versatilidade decrescente.

        Retorna {actor_id: {name, actor_type, overlapping_degree, participation,
        versatility, z_overlap, n_layers_present, category}}.
        """
        ids = list(self.project.actors.keys())

        overlap = {aid: self.overlapping_degree(aid, exclude, weighted)
                   for aid in ids}
        vals = list(overlap.values())
        n = len(vals)
        mean = sum(vals) / n if n else 0.0
        var = sum((v - mean) ** 2 for v in vals) / n if n else 0.0
        std = math.sqrt(var)

        out = {}
        for aid in ids:
            actor = self.project.actors[aid]
            o = overlap[aid]
            P = self.participation_coefficient(aid, exclude, weighted)
            V = self.versatility(aid, exclude, weighted)
            z = (o - mean) / std if std > 0 else 0.0
            out[aid] = {
                "name": actor.name,
                "actor_type": actor.actor_type,
                "overlapping_degree": round(o, 4),
                "participation": round(P, 4),
                "versatility": round(V, 4),
                "z_overlap": round(z, 3),
                "n_layers_present": self.n_layers_present(aid, exclude),
                "category": self._cartography_label(z, P, hub_z),
            }
        return dict(sorted(out.items(),
                           key=lambda kv: kv[1]["versatility"],
                           reverse=True))

    # ── densidade por camada (conveniência) ───────────────────────────────
    def density_by_layer(self, exclude=None):
        """{nome_camada: densidade} para cada camada considerada."""
        res = {}
        for lid in self._layer_ids(exclude):
            layer = self.project.get_layer_by_id(lid)
            res[layer.name if layer else lid] = round(
                self.get_layer_metrics(lid).get("density", 0.0), 4)
        return res

    # ── exportação ────────────────────────────────────────────────────────
    def report_rows(self, exclude=None, weighted=False, hub_z=1.0):
        """Lista de linhas (dicts) pronta para tabela ou CSV."""
        rows = []
        for aid, m in self.all_actor_metrics(exclude, weighted, hub_z).items():
            row = {"actor_id": aid}
            row.update(m)
            rows.append(row)
        return rows

    def export_csv(self, filepath, exclude=None, weighted=False, hub_z=1.0):
        """Salva a tabela de métricas em CSV (UTF-8)."""
        rows = self.report_rows(exclude, weighted, hub_z)
        if not rows:
            return
        fields = ["actor_id", "name", "actor_type", "overlapping_degree",
                  "participation", "versatility", "z_overlap",
                  "n_layers_present", "category"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(r)


# ── comparação entre dois estados (pré vs. pós) ───────────────────────────
def compare_states(pre_engine, post_engine, exclude=None, weighted=False):
    """Delta de versatilidade e participação por ator entre dois engines.

    Casa os atores por nome (não por id, que pode diferir entre snapshots).
    Retorna lista de dicts ordenada pelo maior |delta de versatilidade|.
    Atores ausentes em um dos estados recebem 0 nas métricas daquele estado.
    """
    pre = {m["name"]: m for m in pre_engine.all_actor_metrics(exclude, weighted).values()}
    post = {m["name"]: m for m in post_engine.all_actor_metrics(exclude, weighted).values()}
    nomes = sorted(set(pre) | set(post))

    linhas = []
    for nome in nomes:
        a = pre.get(nome, {})
        b = post.get(nome, {})
        v_pre = a.get("versatility", 0.0)
        v_pos = b.get("versatility", 0.0)
        p_pre = a.get("participation", 0.0)
        p_pos = b.get("participation", 0.0)
        linhas.append({
            "name": nome,
            "versatility_pre": v_pre,
            "versatility_pos": v_pos,
            "delta_versatility": round(v_pos - v_pre, 4),
            "participation_pre": p_pre,
            "participation_pos": p_pos,
            "delta_participation": round(p_pos - p_pre, 4),
        })
    linhas.sort(key=lambda r: abs(r["delta_versatility"]), reverse=True)
    return linhas


# ── execução direta para inspeção rápida ──────────────────────────────────
if __name__ == "__main__":
    import sys
    from .models import Project

    if len(sys.argv) < 2:
        print("Uso: python -m core.versatility <arquivo.mleco|.json> "
              "[camada_a_excluir ...]")
        sys.exit(1)

    caminho = sys.argv[1]
    excluir = sys.argv[2:] or None
    projeto = Project.load(caminho)
    engine = VersatilityEngine(projeto)

    print(f"\nProjeto: {projeto.name}")
    print(f"Camadas ({len(projeto.layers)}): "
          f"{', '.join(l.name for l in sorted(projeto.layers, key=lambda x: x.order))}")
    if excluir:
        print(f"Excluindo do cálculo: {', '.join(excluir)}")

    print("\nDensidade por camada:")
    for nome, d in engine.density_by_layer(excluir).items():
        print(f"  {nome:<24} {d:.4f}")

    print("\n{:<24} {:>6} {:>7} {:>7} {:>6} {:>5}  {}".format(
        "Ator", "Vi", "Pi", "o_i", "z", "#cam", "categoria"))
    print("-" * 78)
    for m in engine.all_actor_metrics(excluir).values():
        print("{:<24} {:>6.3f} {:>7.3f} {:>7.1f} {:>6.2f} {:>5} {}".format(
            m["name"][:24], m["versatility"], m["participation"],
            m["overlapping_degree"], m["z_overlap"],
            m["n_layers_present"], m["category"]))
