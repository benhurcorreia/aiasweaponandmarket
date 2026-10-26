"""
MultilayerEco - Multilayer Canvas Visualization
Camadas dispostas em escada diagonal:
 - Camada mais alta: canto superior-esquerdo
 - Camada do meio:   centro
 - Camada mais baixa: canto inferior-direito
Isso garante legibilidade total dos nós em cada plano.
"""
import math
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsPathItem, QGraphicsPolygonItem,
    QApplication
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QLineF
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainter, QFont, QPainterPath,
    QPolygonF
)
from core.models import (
    Project, Actor, Layer, Relationship,
    ACTOR_TYPE_COLORS, RELATION_TYPE_STYLES
)
from core.i18n import tr


# ─── Oblique Projection ───────────────────────────────────────────────────────
# Maps (layer_x, layer_y) in local coords to scene (screen) coords.
# Each layer has its own (offset_x, offset_y) origin in scene space,
# producing the staircase diagonal effect.

OBLIQUE_ANGLE = math.radians(28)   # angle of depth axis
COS_A = math.cos(OBLIQUE_ANGLE)
SIN_A = math.sin(OBLIQUE_ANGLE)

# Plane dimensions in scene pixels (local space: 0..PLANE_W, 0..PLANE_H)
PLANE_W = 1100    # width of each layer plane
PLANE_H = 700    # depth of each layer plane

# How much each layer steps diagonally (scene pixels).
# Cascata diagonal: cada camada desce E avança para a direita em passos
# comparáveis, do canto superior esquerdo (camada do topo) ao canto inferior
# direito (camada de baixo). Valores parecidos em X e Y produzem ~45 graus.
STAIR_DX = 380   # passo horizontal por camada (camadas de baixo vão p/ direita)
STAIR_DY = 300   # passo vertical por camada (camadas de baixo descem)


def local_to_scene(lx: float, ly: float, layer_order: int, n_layers: int,
                   stair_dx: float = None, stair_dy: float = None) -> QPointF:
    """
    Convert local layer coordinates (lx, ly) in [0..PLANE_W] x [0..PLANE_H]
    to scene coordinates, applying oblique projection and staircase offset.

    layer_order: 0 = bottom layer (Negócios), n_layers-1 = top (Conhecimento)
    The topmost layer sits at the upper-left; the bottom at lower-right.
    stair_dx / stair_dy: passo da cascata diagonal (default = módulo).
    """
    dx = STAIR_DX if stair_dx is None else stair_dx
    dy = STAIR_DY if stair_dy is None else stair_dy
    # Staircase offset: top layer has (0,0); each lower layer shifts right+down
    step = (n_layers - 1 - layer_order)  # 0 for top layer, increases downward
    origin_x = step * dx
    origin_y = step * dy

    # Oblique projection of depth (ly → diagonal)
    sx = origin_x + lx + ly * COS_A
    sy = origin_y + ly * SIN_A

    return QPointF(sx, sy)


def plane_corners(layer_order: int, n_layers: int) -> list:
    """Return the 4 corner QPointFs of a layer plane in scene space."""
    corners_local = [
        (0,        0),
        (PLANE_W,  0),
        (PLANE_W,  PLANE_H),
        (0,        PLANE_H),
    ]
    return [local_to_scene(x, y, layer_order, n_layers) for x, y in corners_local]


# ─── Items ────────────────────────────────────────────────────────────────────

class NodeItem(QGraphicsEllipseItem):
    """Dark circle node — clean reference style."""

    RADIUS = 14
    FONT_SIZE = 11  # controlável em tempo de execução

    def __init__(self, actor_id: str, name: str,
                 x: float, y: float, layer_id: str):
        r = self.RADIUS
        super().__init__(-r, -r, r * 2, r * 2)
        self.actor_id = actor_id
        self.layer_id = layer_id

        self.setBrush(QBrush(QColor("#2C3E50")))
        self.setPen(QPen(QColor("white"), 1.5))

        # Label to the right
        self.label = QGraphicsTextItem(name, self)
        font = QFont("Helvetica", NodeItem.FONT_SIZE)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(QColor("#1A252F"))
        br = self.label.boundingRect()
        self.label.setPos(r + 4, -br.height() / 2)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setZValue(10)
        self.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if scene and hasattr(scene, 'node_moved'):
                scene.node_moved(self)
        return super().itemChange(change, value)

    def set_highlight(self, on: bool):
        self.setPen(QPen(QColor("#F1C40F"), 3) if on else QPen(QColor("white"), 1.5))
        self.setZValue(20 if on else 10)


class EdgeItem(QGraphicsPathItem):
    """Relationship edge."""

    def __init__(self, rel_id: str, src: QPointF, tgt: QPointF,
                 rel_type: str = "cooperação",
                 direction: str = "bidirectional",
                 label: str = "",
                 is_inter_layer: bool = False):
        super().__init__()
        self.rel_id = rel_id
        self._src = src
        self._tgt = tgt
        self._direction = direction
        self.is_inter_layer = is_inter_layer

        si = RELATION_TYPE_STYLES.get(rel_type, RELATION_TYPE_STYLES["outro"])

        if is_inter_layer:
            color = QColor("#2C3E50")
            color.setAlpha(70)
            width = 1.0
            pen = QPen(color, width)
            pen.setDashPattern([3, 6])
        else:
            color = QColor(si["color"])
            width = si["width"] * 0.75
            pen = QPen(color, width)
            pen.setCapStyle(Qt.RoundCap)
            if si["style"] == "dash":
                pen.setDashPattern([6, 4])
            elif si["style"] == "dot":
                pen.setDashPattern([2, 3])

        self.setPen(pen)
        self.setZValue(-1 if is_inter_layer else 2)

        self._build(src, tgt, direction)

        # Label (intra-layer only)
        if label and not is_inter_layer:
            mid = QPointF((src.x() + tgt.x()) / 2,
                          (src.y() + tgt.y()) / 2)
            lbl = QGraphicsTextItem(label, self)
            lbl.setFont(QFont("Helvetica", 8))
            lbl.setDefaultTextColor(QColor(si["color"]).darker(110))
            br = lbl.boundingRect()
            lbl.setPos(mid.x() - br.width() / 2, mid.y() - br.height() / 2)

    def _build(self, src: QPointF, tgt: QPointF, direction: str):
        path = QPainterPath()
        path.moveTo(src)
        path.lineTo(tgt)
        self.setPath(path)
        if direction in ("source_to_target", "target_to_source"):
            tip  = tgt if direction == "source_to_target" else src
            tail = src if direction == "source_to_target" else tgt
            self._arrow(tip, tail)

    def _arrow(self, tip: QPointF, tail: QPointF):
        dx, dy = tip.x() - tail.x(), tip.y() - tail.y()
        ln = math.sqrt(dx * dx + dy * dy)
        if ln < 1:
            return
        dx /= ln; dy /= ln
        R = NodeItem.RADIUS + 2
        tip2 = QPointF(tip.x() - dx * R, tip.y() - dy * R)
        sz = 7
        p1 = QPointF(tip2.x() - sz * (dx + dy * 0.45),
                     tip2.y() - sz * (dy - dx * 0.45))
        p2 = QPointF(tip2.x() - sz * (dx - dy * 0.45),
                     tip2.y() - sz * (dy + dx * 0.45))
        path = self.path()
        path.moveTo(tip2); path.lineTo(p1)
        path.moveTo(tip2); path.lineTo(p2)
        self.setPath(path)

    def update_positions(self, src: QPointF, tgt: QPointF):
        self._src, self._tgt = src, tgt
        self._build(src, tgt, self._direction)


class LayerPlane(QGraphicsPolygonItem):
    """Parallelogram plane for a layer with label."""

    def __init__(self, layer: Layer, corners: list):
        super().__init__()
        self.layer_id = layer.id

        polygon = QPolygonF(corners)
        self.setPolygon(polygon)

        fill = QColor(layer.color)
        fill.setAlpha(22)
        self.setBrush(QBrush(fill))

        border = QColor(layer.color)
        border.setAlpha(150)
        self.setPen(QPen(border, 2.0))
        self.setZValue(-10)
        # O rótulo do nome da camada é adicionado pela cena como item de
        # topo (z alto) para não ficar atrás dos nós (ver _add_layer_label).


# ─── Scene ────────────────────────────────────────────────────────────────────

class MultilayerScene(QGraphicsScene):
    """Scene with staircase-diagonal multilayer layout."""

    node_selected      = Signal(str)
    node_double_clicked = Signal(str)
    edge_selected      = Signal(str)
    scene_changed      = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project   = None
        self._nodes    = {}   # {(actor_id, layer_id): NodeItem}
        self._edges    = {}   # {rel_id: EdgeItem}
        self._n_layers = 0
        # Isolamento de camada: quando definido, renderiza apenas essa camada
        # de forma plana (2D de frente), sem a projeção oblíqua em escada.
        self.isolated_layer_id = None
        self._flat = False
        # passo da cascata diagonal (ajustável pelas Configurações)
        self.stair_dx = STAIR_DX
        self.stair_dy = STAIR_DY
        # modo de visualização: "diagonal", "vertical", "matrix", "flat"
        self.view_mode = "diagonal"
        # tamanho da fonte do nome das camadas
        self.layer_font_size = 14

    def set_project(self, project: Project):
        self.project = project
        self.rebuild()

    def set_view_mode(self, mode: str):
        """Define o modo de visualização das camadas e reconstrói a cena."""
        if mode in ("diagonal", "vertical", "matrix", "flat"):
            self.view_mode = mode
            self.rebuild()

    def set_layer_font_size(self, size: int):
        """Atualiza o tamanho da fonte dos nomes das camadas."""
        self.layer_font_size = max(8, min(int(size), 48))
        self.rebuild()

    def _eff_stair(self):
        """Passo efetivo da escada conforme o modo (vertical zera o dx)."""
        if self.view_mode == "vertical":
            return 0.0, self.stair_dy
        return self.stair_dx, self.stair_dy

    # ── projection helpers (respect flat / isolated mode) ──
    def _project(self, lx: float, ly: float, order: int, n: int) -> QPointF:
        """Projeta coordenadas locais para a cena.

        Em modo plano (camada isolada) usa projeção ortogonal de frente;
        caso contrário usa a projeção oblíqua em escada (diagonal/vertical)."""
        if self._flat:
            return QPointF(lx, ly)
        dx, dy = self._eff_stair()
        return local_to_scene(lx, ly, order, n, dx, dy)

    def _plane_corners(self, order: int, n: int) -> list:
        corners_local = [
            (0,        0),
            (PLANE_W,  0),
            (PLANE_W,  PLANE_H),
            (0,        PLANE_H),
        ]
        return [self._project(x, y, order, n) for x, y in corners_local]

    # ── layer isolation ──
    def set_isolated_layer(self, layer_id):
        """Isola uma camada (renderização plana 2D). None = mostrar todas."""
        self.isolated_layer_id = layer_id or None
        self.rebuild()

    def set_isolated_layer_by_name(self, name):
        """Isola uma camada pelo nome (útil ao comparar dois ecossistemas
        cujas camadas têm o mesmo nome mas IDs diferentes)."""
        if not name:
            self.isolated_layer_id = None
        else:
            layer = self.project.get_layer_by_name(name) if self.project else None
            # Sentinela inexistente => cena vazia (a camada não existe aqui)
            self.isolated_layer_id = layer.id if layer else "__missing__"
        self.rebuild()


    def spread_actors(self):
        """Redistribui atores de cada camada em grade, cobrindo o plano todo.

        Algoritmo:
          - Para N atores numa camada, calcula cols/rows preservando a proporção
            PLANE_W:PLANE_H do plano.
          - Espaça uniformemente em [0..PLANE_W] x [0..PLANE_H]; a normalização
            em _scene_pos acrescenta a margem de 9% automaticamente.
          - Atualiza actor.positions e reconstrói a cena.
        """
        if not self.project:
            return
        import math as _math
        for layer in self.project.layers:
            actors = self.project.get_actors_in_layer(layer.id)
            N = len(actors)
            if N == 0:
                continue
            # Dimensões da grade preservando proporção do plano
            aspect = PLANE_W / PLANE_H
            cols = max(1, round(_math.sqrt(N * aspect)))
            rows = _math.ceil(N / cols)
            # Ajuste fino: reduzir cols se sobram linhas vazias
            while cols > 1 and _math.ceil(N / (cols - 1)) <= rows:
                cols -= 1
                rows = _math.ceil(N / cols)
            # Posicionar de borda a borda: margem 5% em cada lado
            mx = PLANE_W * 0.05
            my = PLANE_H * 0.05
            usable_x = PLANE_W - 2 * mx
            usable_y = PLANE_H - 2 * my
            step_x = usable_x / max(cols - 1, 1) if cols > 1 else 0
            step_y = usable_y / max(rows - 1, 1) if rows > 1 else 0
            for idx, actor in enumerate(actors):
                c = idx % cols
                r = idx // cols
                x = mx + c * step_x if cols > 1 else PLANE_W / 2
                y = my + r * step_y if rows > 1 else PLANE_H / 2
                actor.positions[layer.id] = [round(x, 1), round(y, 1)]
        self.rebuild()

    def set_node_font_size(self, size: int):
        """Atualiza tamanho da fonte dos nós e reconstrói a cena."""
        NodeItem.FONT_SIZE = max(6, min(size, 60))
        self.rebuild()

    def set_node_radius(self, size: int):
        """Atualiza o raio (tamanho) dos nós e reconstrói a cena."""
        NodeItem.RADIUS = max(3, min(size, 48))
        self.rebuild()

    def align_actor_positions(self, W: float = 1040, H: float = 660,
                              alpha: float = 0.7, seed: int = 42):
        """Define UMA posição (x, y) por ator a partir da rede agregada e a
        aplica em todas as camadas em que o ator aparece, alinhando o mesmo
        ator entre camadas. Atores mais centrais (maior grau) vão para o
        centro; periféricos para as bordas."""
        if not self.project or not self.project.actors:
            return
        import networkx as nx
        G = nx.Graph()
        for aid in self.project.actors:
            G.add_node(aid)
        for r in self.project.relationships:
            if (r.source_id in self.project.actors
                    and r.target_id in self.project.actors
                    and r.source_id != r.target_id):
                G.add_edge(r.source_id, r.target_id)
        if G.number_of_nodes() == 0:
            return
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
        deg = dict(G.degree())
        dmax, dmin = (max(deg.values()), min(deg.values())) if deg else (0, 0)
        drange = (dmax - dmin) or 1
        cx, cy = W / 2.0, H / 2.0
        for aid, (x, y) in pos.items():
            sx = m + (x - minx) / rx * (W - 2 * m)
            sy = m + (y - miny) / ry * (H - 2 * m)
            f = 1.0 - alpha * ((deg.get(aid, 0) - dmin) / drange)
            fx = round(cx + (sx - cx) * f, 1)
            fy = round(cy + (sy - cy) * f, 1)
            actor = self.project.actors[aid]
            for lid in actor.layers:
                actor.positions[lid] = [fx, fy]
        self.rebuild()

    def set_stair(self, dx: float = None, dy: float = None):
        """Ajusta o passo da cascata diagonal entre camadas."""
        if dx is not None:
            self.stair_dx = max(0, dx)
        if dy is not None:
            self.stair_dy = max(0, dy)
        self.rebuild()


    def _add_layer_label(self, layer, corners):
        """Adiciona o nome da camada no canto superior esquerdo do plano,
        como item de topo (z alto) para ficar sempre visível."""
        tl = corners[0]  # canto local (0,0) = superior esquerdo do plano
        lbl = QGraphicsTextItem(tr(layer.name))
        f = QFont("Helvetica", self.layer_font_size)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setDefaultTextColor(QColor(layer.color))
        lbl.setZValue(25)
        lbl.setPos(tl.x() + 8, tl.y() - (self.layer_font_size + 16))
        self.addItem(lbl)

    def rebuild(self):
        self.clear()
        self._nodes.clear()
        self._edges.clear()

        if not self.project or not self.project.layers:
            return

        # ─── Modo camada isolada (plano 2D de frente) ───
        if self.isolated_layer_id:
            iso = self.project.get_layer_by_id(self.isolated_layer_id)
            if not iso:
                # Camada não existe neste ecossistema → cena vazia
                self.setSceneRect(QRectF(0, 0, PLANE_W, PLANE_H))
                return
            self._flat = True
            self._n_layers = 1
            # Plano único, plano e centrado
            corners = self._plane_corners(0, 1)
            self.addItem(LayerPlane(iso, corners))
            self._add_layer_label(iso, corners)
            # Apenas relações intra-camada desta camada
            for rel in self.project.get_relationships_in_layer(iso.id):
                self._draw_intra_edge(rel, 1)
            # Nós da camada
            for actor in self.project.get_actors_in_layer(iso.id):
                self._draw_node(actor, iso, 1)
            self.setSceneRect(self.itemsBoundingRect().adjusted(-60, -60, 100, 60))
            return

        # ─── Modos alternativos: matriz (grade) e plano agregado ───
        if self.view_mode == "matrix":
            self._rebuild_matrix()
            return
        if self.view_mode == "flat":
            self._rebuild_flat_aggregate()
            return

        # ─── Modo multicamada padrão (escada oblíqua: diagonal/vertical) ───
        self._flat = False
        layers = sorted(self.project.layers, key=lambda l: l.order)
        self._n_layers = len(layers)
        N = self._n_layers

        # 1. Layer planes
        for layer in layers:
            if not layer.visible:
                continue
            corners = self._plane_corners(layer.order, N)
            plane = LayerPlane(layer, corners)
            self.addItem(plane)
            self._add_layer_label(layer, corners)

        # 2. Intra-layer edges
        for rel in self.project.relationships:
            if rel.is_inter_layer or not rel.layer_id:
                continue
            self._draw_intra_edge(rel, N)

        # 3. Inter-layer + identity links
        self._draw_identity_links(layers, N)
        for rel in self.project.get_inter_layer_relationships():
            self._draw_inter_edge(rel, N)

        # 4. Nodes (drawn last = on top)
        for layer in layers:
            if not layer.visible:
                continue
            for actor in self.project.get_actors_in_layer(layer.id):
                self._draw_node(actor, layer, N)

        self.setSceneRect(self.itemsBoundingRect().adjusted(-60, -60, 100, 60))

    # ── helpers de posição em coordenadas planas ──
    def _cell_scene_pos(self, lpos, x0, y0, w, h):
        """Coloca uma posição local (lpos) dentro de um retângulo de célula."""
        fx = x0 + (lpos[0] / PLANE_W) * (w * 0.90) + w * 0.05
        fy = y0 + (lpos[1] / PLANE_H) * (h * 0.90) + h * 0.05
        return QPointF(fx, fy)

    def _actor_canonical_pos(self, actor):
        """Posição única do ator (já alinhada entre camadas)."""
        for lid in actor.layers:
            p = actor.positions.get(lid)
            if p:
                return p
        for p in actor.positions.values():
            if p:
                return p
        return None

    # ── Modo matriz (grade de pequenos múltiplos, planos 2D) ──
    def _rebuild_matrix(self):
        import math as _m
        self._flat = True
        layers = [l for l in sorted(self.project.layers, key=lambda l: l.order)
                  if l.visible]
        n = len(layers)
        self._n_layers = n
        if n == 0:
            return
        cols = max(1, round(_m.sqrt(n)))
        if cols * cols < n and cols * (cols + 1) >= n:
            rows = cols + 1
        else:
            rows = _m.ceil(n / cols)
        CW, CH = PLANE_W * 0.55, PLANE_H * 0.65
        GAPX, GAPY = CW * 0.14, CH * 0.34
        cell_pos = {}
        for i, layer in enumerate(layers):
            c = i % cols
            r = i // cols
            x0 = c * (CW + GAPX)
            y0 = r * (CH + GAPY)
            corners = [QPointF(x0, y0), QPointF(x0 + CW, y0),
                       QPointF(x0 + CW, y0 + CH), QPointF(x0, y0 + CH)]
            self.addItem(LayerPlane(layer, corners))
            self._add_layer_label(layer, corners)
            for actor in self.project.get_actors_in_layer(layer.id):
                lpos = actor.positions.get(layer.id)
                if not lpos:
                    continue
                sp = self._cell_scene_pos(lpos, x0, y0, CW, CH)
                node = NodeItem(actor.id, actor.name, sp.x(), sp.y(), layer.id)
                self.addItem(node)
                self._nodes[(actor.id, layer.id)] = node
                cell_pos[(actor.id, layer.id)] = sp
        for rel in self.project.relationships:
            if rel.is_inter_layer or not rel.layer_id:
                continue
            sp = cell_pos.get((rel.source_id, rel.layer_id))
            tp = cell_pos.get((rel.target_id, rel.layer_id))
            if sp is None or tp is None:
                continue
            edge = EdgeItem(rel.id, sp, tp, rel.rel_type, rel.direction,
                            rel.label, is_inter_layer=False)
            self.addItem(edge)
            self._edges[rel.id] = edge
        self.setSceneRect(self.itemsBoundingRect().adjusted(-60, -60, 100, 60))

    # ── Modo plano agregado (todas as relações em um único plano) ──
    def _rebuild_flat_aggregate(self):
        self._flat = True
        self._n_layers = 1
        corners = [QPointF(0, 0), QPointF(PLANE_W, 0),
                   QPointF(PLANE_W, PLANE_H), QPointF(0, PLANE_H)]
        plane = QGraphicsPolygonItem(QPolygonF(corners))
        fill = QColor("#7F8C8D")
        fill.setAlpha(18)
        plane.setBrush(QBrush(fill))
        border = QColor("#7F8C8D")
        border.setAlpha(140)
        plane.setPen(QPen(border, 2.0))
        plane.setZValue(-10)
        self.addItem(plane)
        lbl = QGraphicsTextItem(tr("Rede agregada (todas as relações)"))
        f = QFont("Helvetica", self.layer_font_size)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setDefaultTextColor(QColor("#566573"))
        lbl.setZValue(25)
        lbl.setPos(8, -(self.layer_font_size + 16))
        self.addItem(lbl)

        node_pos = {}
        for actor in self.project.actors.values():
            lpos = self._actor_canonical_pos(actor)
            if not lpos:
                continue
            sp = self._cell_scene_pos(lpos, 0, 0, PLANE_W, PLANE_H)
            node = NodeItem(actor.id, actor.name, sp.x(), sp.y(), "")
            self.addItem(node)
            self._nodes[(actor.id, "")] = node
            node_pos[actor.id] = sp
        for rel in self.project.relationships:
            if rel.source_id == rel.target_id:
                continue
            sp = node_pos.get(rel.source_id)
            tp = node_pos.get(rel.target_id)
            if sp is None or tp is None:
                continue
            edge = EdgeItem(rel.id, sp, tp, rel.rel_type, rel.direction,
                            "", is_inter_layer=False)
            self.addItem(edge)
            self._edges[rel.id] = edge
        self.setSceneRect(self.itemsBoundingRect().adjusted(-60, -60, 100, 60))

    # ── coordinate helper ──
    def _scene_pos(self, actor_id: str, layer_id: str) -> QPointF:
        actor = self.project.actors.get(actor_id)
        layer = self.project.get_layer_by_id(layer_id)
        if not actor or not layer:
            return None
        lpos = actor.positions.get(layer_id)
        if not lpos:
            return None
        # lpos is in [0..graph_engine_width] x [0..graph_engine_height]
        # Normalise to [0..PLANE_W] x [0..PLANE_H]
        lx = (lpos[0] / PLANE_W) * (PLANE_W * 0.92) + PLANE_W * 0.04
        ly = (lpos[1] / PLANE_H) * (PLANE_H * 0.92) + PLANE_H * 0.04
        order = 0 if self._flat else layer.order
        return self._project(lx, ly, order, self._n_layers)

    # ── drawing helpers ──
    def _draw_node(self, actor: Actor, layer: Layer, N: int):
        sp = self._scene_pos(actor.id, layer.id)
        if sp is None:
            return
        node = NodeItem(actor.id, actor.name, sp.x(), sp.y(), layer.id)
        self.addItem(node)
        self._nodes[(actor.id, layer.id)] = node

    def _draw_intra_edge(self, rel: Relationship, N: int):
        sp = self._scene_pos(rel.source_id, rel.layer_id)
        tp = self._scene_pos(rel.target_id, rel.layer_id)
        if sp is None or tp is None:
            return
        edge = EdgeItem(rel.id, sp, tp, rel.rel_type,
                        rel.direction, rel.label, is_inter_layer=False)
        self.addItem(edge)
        self._edges[rel.id] = edge

    def _draw_inter_edge(self, rel: Relationship, N: int):
        sp = self._scene_pos(rel.source_id, rel.source_layer_id)
        tp = self._scene_pos(rel.target_id, rel.target_layer_id)
        if sp is None or tp is None:
            return
        edge = EdgeItem(rel.id, sp, tp, rel.rel_type,
                        rel.direction, "", is_inter_layer=True)
        self.addItem(edge)
        self._edges[rel.id] = edge

    def _draw_identity_links(self, layers: list, N: int):
        """Thin dashed lines connecting same actor across adjacent layers."""
        for actor in self.project.actors.values():
            if len(actor.layers) < 2:
                continue
            actor_layers = [l for l in layers if l.id in actor.layers]
            for i in range(len(actor_layers) - 1):
                p1 = self._scene_pos(actor.id, actor_layers[i].id)
                p2 = self._scene_pos(actor.id, actor_layers[i + 1].id)
                if p1 and p2:
                    pen = QPen(QColor("#2C3E50"), 0.9)
                    pen.setDashPattern([3, 6])
                    c = QColor("#2C3E50")
                    c.setAlpha(55)
                    pen.setColor(c)
                    line = self.addLine(QLineF(p1, p2), pen)
                    line.setZValue(-5)

    # ── node drag ──
    def node_moved(self, node: NodeItem):
        for rel_id, edge in self._edges.items():
            rel = next((r for r in self.project.relationships if r.id == rel_id), None)
            if not rel:
                continue
            if self.view_mode == "flat":
                # plano agregado: um nó por ator, chave de camada vazia
                sk = (rel.source_id, "")
                tk = (rel.target_id, "")
            elif rel.is_inter_layer:
                sk = (rel.source_id, rel.source_layer_id)
                tk = (rel.target_id, rel.target_layer_id)
            else:
                sk = (rel.source_id, rel.layer_id)
                tk = (rel.target_id, rel.layer_id)
            sn = self._nodes.get(sk)
            tn = self._nodes.get(tk)
            if sn and tn:
                if node.actor_id in (rel.source_id, rel.target_id):
                    edge.update_positions(sn.pos(), tn.pos())
        self.scene_changed.emit()


# ─── View ─────────────────────────────────────────────────────────────────────

class MultilayerView(QGraphicsView):
    """Interactive view with zoom + pan."""

    zoom_changed = Signal(int)   # emitted when zoom level changes

    # Fator de zoom por passo. Menor = menos sensível (experiência mais suave).
    ZOOM_FACTOR = 1.08
    ZOOM_MIN = -40
    ZOOM_MAX = 40

    def __init__(self, scene: MultilayerScene, parent=None):
        super().__init__(scene, parent)
        self._wheel_accum = 0   # acumulador para suavizar scroll/trackpad
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self._zoom = 0
        self._pan  = False       # pan via botão do meio
        self._pan0 = QPointF()
        self._pan_mode = False   # modo mover permanente (botão na toolbar)
        self._space_held = False # Space para pan temporário
        self.setFocusPolicy(Qt.StrongFocus)

    def _apply_zoom_factor(self, factor: float):
        self.scale(factor, factor)

    def zoom_step(self, steps: int):
        """Zoom in (steps>0) or out (steps<0) by that many steps."""
        f = self.ZOOM_FACTOR
        new_zoom = self._zoom + steps
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, new_zoom))
        delta = new_zoom - self._zoom
        if delta == 0:
            return
        if delta > 0:
            for _ in range(delta):
                self.scale(f, f)
        else:
            for _ in range(-delta):
                self.scale(1/f, 1/f)
        self._zoom = new_zoom
        self.zoom_changed.emit(self._zoom)

    def set_zoom_level(self, level: int):
        """Jump directly to a zoom level (relative to fit-all baseline)."""
        level = max(self.ZOOM_MIN, min(self.ZOOM_MAX, level))
        if level == self._zoom:
            return
        # Reset to 1:1 then apply target
        f = self.ZOOM_FACTOR
        self.resetTransform()
        if level > 0:
            factor = f ** level
        elif level < 0:
            factor = (1/f) ** (-level)
        else:
            factor = 1.0
        self.scale(factor, factor)
        self._zoom = level
        self.zoom_changed.emit(self._zoom)

    def wheelEvent(self, e):
        # Acumula o delta da roda/trackpad e só dá um passo de zoom a cada
        # 120 unidades (um "entalhe" de mouse). Reduz drasticamente a
        # sensibilidade exagerada de trackpads e mouses de alta resolução.
        self._wheel_accum += e.angleDelta().y()
        steps = int(self._wheel_accum / 120)
        if steps != 0:
            self._wheel_accum -= steps * 120
            self.zoom_step(steps)
        e.accept()

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._pan  = True
            self._pan0 = e.position()
            self.setCursor(Qt.ClosedHandCursor)
        elif e.button() == Qt.LeftButton and (
            e.modifiers() & Qt.AltModifier or self._space_held
        ):
            # Alt+drag ou Space+drag: pan temporário
            self._pan  = True
            self._pan0 = e.position()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._pan:
            d = e.position() - self._pan0
            self._pan0 = e.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - d.x()))
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - d.y()))
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() in (Qt.MiddleButton, Qt.LeftButton) and self._pan:
            self._pan = False
            if self._pan_mode or self._space_held:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(e)

    def toggle_pan_mode(self, enabled: bool):
        """Alterna entre modo mover (ScrollHandDrag) e seleção (RubberBandDrag)."""
        self._pan_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space and not e.isAutoRepeat() and not self._pan_mode:
            self._space_held = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Space and not e.isAutoRepeat() and not self._pan_mode:
            self._space_held = False
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
        else:
            super().keyReleaseEvent(e)

    def fit_all(self):
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
        self._zoom = 0
        self.zoom_changed.emit(0)

    def export_to_image(self, filepath: str, width: int = 2400, height: int = 1800):
        from PySide6.QtGui import QImage
        scene  = self.scene()
        rect   = scene.sceneRect()
        scale  = min(width / max(rect.width(), 1),
                     height / max(rect.height(), 1))
        img_w  = int(rect.width()  * scale)
        img_h  = int(rect.height() * scale)
        image  = QImage(img_w, img_h, QImage.Format_ARGB32)
        image.fill(QColor("#FFFFFF"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        scene.render(painter, QRectF(0, 0, img_w, img_h), rect)
        painter.end()
        image.save(filepath)
        return filepath
