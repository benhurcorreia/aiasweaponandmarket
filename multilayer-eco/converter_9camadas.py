#!/usr/bin/env python3
"""
Converte os arquivos autoritativos de 3 camadas (figura1_pre_conflito.mleco e
figura2_pos_conflito.mleco) para a modelagem multiplex de 9 camadas, uma por
tipo de relação.

Vantagem sobre o gerador manual anterior: não reconstrói as arestas à mão. Lê
a lista completa e documentada dos arquivos originais, então nada se perde.

O que a conversão faz com cada relação:
  - layer_id passa a ser a camada do seu tipo (rel_type).
  - o estrato de Jacobides de origem (Modelos / Deployments / Sistemas) é
    gravado no atributo "estrato" da relação, para a densidade por estrato.
  - relações inter-camada do tipo "ator -> ele mesmo" (auto-acoplamento
    vertical) são descartadas: no modelo multiplex node-aligned essa
    informação já é capturada pela presença do ator em várias camadas de
    relação. As demais relações inter-camada (entre atores diferentes) são
    mantidas, com estrato "inter".
  - duplicatas (mesmo par e mesmo tipo) são unificadas.

Saída: um único .mleco com dois momentos (Pré-conflito e Pós-conflito) prontos
para a tela de comparação, além de um .json legível.
"""

import os
import sys

APP_DIR_CANDIDATES = [
    "/Users/benhur.correia/Documents/APP ECOSSISTEMA /multilayer-eco",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "multilayer-eco"),
    os.path.dirname(os.path.abspath(__file__)),
]
for cand in APP_DIR_CANDIDATES:
    if os.path.isdir(os.path.join(cand, "core")):
        sys.path.insert(0, cand)
        APP_DIR = cand
        break
else:
    raise SystemExit("Não encontrei o pacote 'core' do MultilayerEco. "
                     "Ajuste APP_DIR_CANDIDATES.")

from core.models import Project, Layer  # noqa: E402

# ── localizar os arquivos de origem ───────────────────────────────────────
DADOS_CANDIDATES = [
    "/Users/benhur.correia/Documents/DOUTORADO - UFRJ COPPEAD/DISCIPLINAS/"
    "IA APLICADA A PESQUISA ACADÊMICA/ARTIGO 2/REVISAO_V9_2026-06-18/dados",
    "/Users/benhur.correia/Documents/DOUTORADO - UFRJ COPPEAD/DISCIPLINAS/"
    "IA APLICADA A PESQUISA ACADÊMICA/ARTIGO 2",
    os.path.dirname(os.path.abspath(__file__)),
]


def achar(nome):
    for d in DADOS_CANDIDATES:
        p = os.path.join(d, nome)
        if os.path.isfile(p):
            return p
    raise SystemExit(f"Não encontrei {nome}. Ajuste DADOS_CANDIDATES.")


PRE_FILE = achar("figura1_pre_conflito.mleco")
POS_FILE = achar("figura2_pos_conflito.mleco")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_MLECO = os.path.join(OUT_DIR, "ecossistema_ia_guerra_9camadas.mleco")
OUT_JSON = os.path.join(OUT_DIR, "ecossistema_ia_guerra_9camadas.json")

# ── as 9 camadas (uma por tipo de relação) ────────────────────────────────
INFRA, GOV, DEPLOY, RUPTURA, MODELOS, TEAL = (
    "#E74C3C", "#9B59B6", "#27AE60", "#C0392B", "#3498DB", "#16A085")
LAYERS = [
    ("L_fornecimento", "Fornecimento", INFRA, 0),
    ("L_investimento", "Investimento", INFRA, 1),
    ("L_extracao",     "Extração",     INFRA, 2),
    ("L_regulacao",    "Regulação",    GOV, 3),
    ("L_dependencia",  "Dependência",  DEPLOY, 4),
    ("L_conflito",     "Conflito",     RUPTURA, 5),
    ("L_integracao",   "Integração",   DEPLOY, 6),
    ("L_cooperacao",   "Cooperação",   TEAL, 7),
    ("L_competicao",   "Competição",   MODELOS, 8),
]
LAYER_ID = {name.lower(): lid for (lid, name, _c, _o) in LAYERS}

# estrato de Jacobides a partir do nome da camada original
ESTRATO = {
    "camada de modelos": "modelos",
    "camada de deployments": "deployments",
    "camada de sistemas": "infra",
}


def make_layers():
    return [Layer(id=lid, name=name, color=color, order=order)
            for (lid, name, color, order) in LAYERS]


def global_positions(*sources, W=1040, H=660, seed=42, alpha=0.7):
    """Calcula UMA posição (x, y) por ator (chave = nome), a partir da rede
    agregada (união das relações de todos os estados). Atores mais centrais
    (maior grau na rede agregada) são puxados para o centro do plano; os
    periféricos vão para as bordas. A mesma posição é usada em todas as
    camadas, garantindo o alinhamento vertical/diagonal do ator.
    """
    import math
    import networkx as nx

    G = nx.Graph()
    for src in sources:
        id2name = {aid: a.name for aid, a in src.actors.items()}
        for nm in id2name.values():
            G.add_node(nm)
        for r in src.relationships:
            s = id2name.get(r.source_id)
            t = id2name.get(r.target_id)
            if s and t and s != t:
                G.add_edge(s, t)
    if G.number_of_nodes() == 0:
        return {}

    n = G.number_of_nodes()
    pos = nx.spring_layout(G, k=2.5 / math.sqrt(max(n, 1)),
                           iterations=300, seed=seed)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    rx = (maxx - minx) or 1
    ry = (maxy - miny) or 1
    m = 45
    scaled = {nm: (m + (x - minx) / rx * (W - 2 * m),
                   m + (y - miny) / ry * (H - 2 * m))
              for nm, (x, y) in pos.items()}

    # gravidade por centralidade de grau: hubs para o centro
    deg = dict(G.degree())
    dmax, dmin = (max(deg.values()), min(deg.values())) if deg else (0, 0)
    drange = (dmax - dmin) or 1
    cx, cy = W / 2.0, H / 2.0
    out = {}
    for nm, (x, y) in scaled.items():
        norm = (deg.get(nm, 0) - dmin) / drange   # 1 = mais central
        f = 1.0 - alpha * norm
        out[nm] = (round(cx + (x - cx) * f, 1), round(cy + (y - cy) * f, 1))
    return out


def converter(origem: Project, nome_estado: str, positions_by_name=None):
    """Reconstrói `origem` (3 camadas) na modelagem de 9 camadas."""
    lid2name = {l.id: l.name for l in origem.layers}
    novo = Project(name=nome_estado)
    novo.layers = make_layers()

    # recria atores preservando nome, tipo, cor e atributos
    old2new = {}
    for aid, a in origem.actors.items():
        novo_a = novo.add_actor(a.name, a.actor_type, layer_ids=[])
        if a.color:
            novo_a.color = a.color
        novo_a.attributes = dict(a.attributes)
        old2new[aid] = novo_a.id

    presenca = {nid: set() for nid in old2new.values()}
    vistos = set()        # (src, dst, rtype) para deduplicar
    self_loops = 0
    convertidas = 0

    for r in origem.relationships:
        rt = (r.rel_type or "").lower()
        if rt not in LAYER_ID:
            continue
        # estrato de origem da relação
        if r.layer_id and r.layer_id in lid2name:
            estrato = ESTRATO.get(lid2name[r.layer_id].lower(), "inter")
        else:
            estrato = "inter"
        # descarta auto-acoplamento vertical (ator -> ele mesmo)
        if r.source_id == r.target_id:
            self_loops += 1
            continue
        sid = old2new.get(r.source_id)
        did = old2new.get(r.target_id)
        if sid is None or did is None:
            continue
        chave = tuple(sorted([sid, did])) + (rt,)
        if chave in vistos:
            continue
        vistos.add(chave)

        lid = LAYER_ID[rt]
        novo.add_relationship(
            source_id=sid, target_id=did, layer_id=lid, rel_type=r.rel_type,
            direction=r.direction, label=r.label, weight=r.weight)
        novo.relationships[-1].attributes["estrato"] = estrato
        presenca[sid].add(lid)
        presenca[did].add(lid)
        convertidas += 1

    for nid, lids in presenca.items():
        novo.actors[nid].layers = sorted(lids)

    # posição única por ator (mesma (x,y) em todas as camadas em que aparece)
    if positions_by_name:
        for nid, na in novo.actors.items():
            xy = positions_by_name.get(na.name)
            if xy is None:
                continue
            for lid in na.layers:
                na.positions[lid] = [xy[0], xy[1]]
    else:
        try:
            from core.graph_engine import GraphEngine
            GraphEngine(novo).compute_all_layouts(width=620, height=420)
        except Exception:
            pass

    print(f"  {nome_estado}: {convertidas} relações convertidas, "
          f"{self_loops} auto-acoplamentos verticais descartados, "
          f"{len(novo.actors)} atores")
    return novo


def contagem(proj):
    from collections import Counter
    return dict(Counter(r.rel_type for r in proj.relationships))


def main():
    print(f"App: {APP_DIR}")
    print(f"Origem PRÉ: {PRE_FILE}")
    print(f"Origem PÓS: {POS_FILE}\n")

    pre_src = Project.load(PRE_FILE)
    pos_src = Project.load(POS_FILE)
    print(f"Originais: pré {len(pre_src.relationships)} relações / "
          f"pós {len(pos_src.relationships)} relações")

    # posição global por ator (união pré+pós) para alinhar entre camadas
    # e manter a mesma posição nos dois momentos
    posicoes = global_positions(pre_src, pos_src)
    print(f"Posições globais calculadas para {len(posicoes)} atores "
          f"(centralidade -> centro).")

    pre = converter(pre_src, "Pré-conflito (fev/2026)", posicoes)
    pos = converter(pos_src, "Pós-conflito (mar/2026)", posicoes)

    container = pos
    container.name = "Ecossistema IA — Guerra EUA–Irã (9 camadas)"
    container.description = ("Modelagem multiplex (uma camada por tipo de "
                             "relação) convertida de figura1/figura2.")
    container.snapshots = [
        {"name": "Pré-conflito (fev/2026)", "data": pre._state_dict()},
        {"name": "Pós-conflito (mar/2026)", "data": pos._state_dict()},
    ]
    container.save(OUT_MLECO)
    container.save(OUT_JSON)
    print(f"\nSalvo:\n  {OUT_MLECO}\n  {OUT_JSON}")

    print("\nArestas por tipo (pré / pós), após conversão:")
    cp, cq = contagem(pre), contagem(pos)
    for (_lid, nome, _c, _o) in LAYERS:
        k = nome.lower()
        print(f"  {nome:14} {cp.get(k, 0):>3} / {cq.get(k, 0):>3}")
    print(f"  {'TOTAL':14} {len(pre.relationships):>3} / "
          f"{len(pos.relationships):>3}")

    try:
        from core.versatility import VersatilityEngine, compare_states
        print("\n=== Maiores variações de versatilidade (pré -> pós) ===")
        rows = compare_states(VersatilityEngine(pre), VersatilityEngine(pos))
        print("{:<18}{:>9}{:>9}{:>9}{:>9}".format(
            "Ator", "Vi_pre", "Vi_pos", "dVi", "dPi"))
        for r in rows[:10]:
            print("{:<18}{:>9.3f}{:>9.3f}{:>+9.3f}{:>+9.3f}".format(
                r["name"][:18], r["versatility_pre"], r["versatility_pos"],
                r["delta_versatility"], r["delta_participation"]))
    except Exception as e:
        print(f"(métricas não calculadas: {e})")


if __name__ == "__main__":
    main()
