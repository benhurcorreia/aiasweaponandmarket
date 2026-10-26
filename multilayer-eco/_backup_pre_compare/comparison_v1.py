"""
MultilayerEco - Comparison Window
Compara dois ecossistemas lado a lado (situação "antes" e "depois"),
útil para análises processuais como a evolução do conflito Irã-EUA.

Cada lado pode receber:
  - o projeto atualmente aberto,
  - um snapshot ("momento") salvo dentro do projeto, ou
  - um arquivo .mleco/.json carregado do disco.

Suporta também isolar uma mesma camada (por nome) em ambos os lados,
para comparar camadas isoladas dos dois ecossistemas, e exportar a
comparação como uma única imagem PNG.
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QComboBox, QLineEdit, QFileDialog,
    QMessageBox, QFrame, QToolBar
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen

from core.models import Project
from core.graph_engine import GraphEngine
from ui.canvas import MultilayerScene, MultilayerView, PLANE_W, PLANE_H


def _clone_project(project: Project) -> Project:
    """Cópia profunda de um projeto via serialização (não muta o original)."""
    return Project.from_dict(project.to_dict())


def _ensure_positions(project: Project):
    """Garante que todos os atores tenham posição em suas camadas.
    Preserva posições já salvas; calcula apenas as ausentes."""
    if not project or not project.actors:
        return
    missing = any(
        lid not in (actor.positions or {})
        for actor in project.actors.values()
        for lid in actor.layers
    )
    if missing:
        try:
            GraphEngine(project).compute_all_layouts(
                width=PLANE_W, height=PLANE_H, algorithm="spring"
            )
        except Exception:
            pass


def render_scene_image(scene: MultilayerScene, target_h: int = 1500,
                       bg: str = "#FFFFFF") -> QImage:
    """Renderiza uma cena para um QImage com altura alvo, preservando proporção."""
    rect = scene.sceneRect()
    if rect.width() < 1 or rect.height() < 1:
        img = QImage(600, target_h, QImage.Format_ARGB32)
        img.fill(QColor(bg))
        return img
    scale = target_h / rect.height()
    w = max(1, int(rect.width() * scale))
    h = max(1, int(rect.height() * scale))
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(QColor(bg))
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    scene.render(painter, QRectF(0, 0, w, h), rect)
    painter.end()
    return img


class ComparePanel(QWidget):
    """Um lado da comparação: seletor de fonte + título editável + visualização."""

    def __init__(self, side_label: str, base_project: Project = None, parent=None):
        super().__init__(parent)
        self.base_project = base_project
        self.project = None
        self._sources = []   # list of (label, kind, ref)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Título editável (aparece na exportação) ──
        title_row = QHBoxLayout()
        tag = QLabel(side_label)
        tag.setStyleSheet("color:#89B4FA; font-weight:bold;")
        title_row.addWidget(tag)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título deste lado (ex.: Antes)")
        title_row.addWidget(self.title_edit, 1)
        layout.addLayout(title_row)

        # ── Fonte do ecossistema ──
        src_row = QHBoxLayout()
        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        src_row.addWidget(self.source_combo, 1)
        load_btn = QPushButton("Carregar arquivo…")
        load_btn.setToolTip("Carregar um ecossistema de um arquivo .mleco/.json")
        load_btn.clicked.connect(self._load_file)
        src_row.addWidget(load_btn)
        layout.addLayout(src_row)

        # ── Canvas ──
        self.scene = MultilayerScene()
        self.view = MultilayerView(self.scene)
        layout.addWidget(self.view, 1)

        # ── Controles do canvas ──
        ctl_row = QHBoxLayout()
        spread_btn = QPushButton("⊞ Espalhar")
        spread_btn.clicked.connect(lambda: (self.scene.spread_actors(), self.view.fit_all()))
        fit_btn = QPushButton("⊡ Ajustar")
        fit_btn.clicked.connect(self.view.fit_all)
        ctl_row.addWidget(spread_btn)
        ctl_row.addWidget(fit_btn)
        ctl_row.addStretch()
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color:#A6ADC8; font-size:11px;")
        ctl_row.addWidget(self.info_label)
        layout.addLayout(ctl_row)

        self._rebuild_sources()

    # ── sources ──
    def _rebuild_sources(self, select_index: int = 0):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self._sources = []
        if self.base_project is not None:
            self._sources.append(("● Projeto aberto", "current", None))
            for name in self.base_project.list_snapshots():
                self._sources.append((f"◷ Momento: {name}", "snapshot", name))
        # arquivos carregados são acrescentados ao final dinamicamente
        for label, kind, ref in getattr(self, "_loaded_files", []):
            self._sources.append((label, kind, ref))
        for label, kind, ref in self._sources:
            self.source_combo.addItem(label)
        self.source_combo.blockSignals(False)
        if self._sources:
            idx = min(select_index, len(self._sources) - 1)
            self.source_combo.setCurrentIndex(idx)
            self._on_source_changed(idx)

    def _on_source_changed(self, index: int):
        if index < 0 or index >= len(self._sources):
            return
        label, kind, ref = self._sources[index]
        proj = None
        try:
            if kind == "current" and self.base_project is not None:
                proj = _clone_project(self.base_project)
                proj.name = self.base_project.name
            elif kind == "snapshot" and self.base_project is not None:
                proj = self.base_project.get_snapshot_project(ref)
            elif kind == "file":
                proj = Project.load(ref)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar: {e}")
            return
        if proj is None:
            return
        self.set_project(proj, default_title=label)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Carregar Ecossistema", "",
            "Projeto MultilayerEco (*.mleco *.json)"
        )
        if not path:
            return
        name = os.path.basename(path)
        if not hasattr(self, "_loaded_files"):
            self._loaded_files = []
        self._loaded_files.append((f"📄 {name}", "file", path))
        # Reconstrói a lista e seleciona o arquivo recém-carregado (último item)
        self._rebuild_sources()
        self.source_combo.setCurrentIndex(self.source_combo.count() - 1)

    # ── project loading ──
    def set_project(self, project: Project, default_title: str = ""):
        self.project = project
        _ensure_positions(project)
        self.scene.set_project(project)
        # Reaplica isolamento atual (definido pela janela) por nome
        if getattr(self, "_isolated_name", None):
            self.scene.set_isolated_layer_by_name(self._isolated_name)
        self.view.fit_all()
        if not self.title_edit.text().strip():
            self.title_edit.setText(project.name or default_title)
        self._update_info()
        # Notifica a janela para atualizar o combo de camadas
        win = self.window()
        if hasattr(win, "refresh_layer_combo"):
            win.refresh_layer_combo()

    def _update_info(self):
        if not self.project:
            self.info_label.setText("")
            return
        nl = len(self.project.layers)
        na = len(self.project.actors)
        nr = len(self.project.relationships)
        self.info_label.setText(f"{nl} camadas · {na} atores · {nr} relações")

    def apply_isolation(self, layer_name):
        self._isolated_name = layer_name
        self.scene.set_isolated_layer_by_name(layer_name)
        self.view.fit_all()

    def layer_names(self):
        if not self.project:
            return []
        return [l.name for l in sorted(self.project.layers, key=lambda x: x.order)]

    def export_title(self):
        t = self.title_edit.text().strip()
        if t:
            return t
        return self.project.name if self.project else ""


class ComparisonWindow(QMainWindow):
    """Janela de comparação de dois ecossistemas lado a lado."""

    def __init__(self, base_project: Project = None, parent=None):
        super().__init__(parent)
        self.base_project = base_project
        self.setWindowTitle("Comparar Ecossistemas — Antes / Depois")
        self.setMinimumSize(1280, 820)
        self._isolated_name = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barra superior ──
        top = QWidget()
        top.setObjectName("cmpTop")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(10, 6, 10, 6)
        top_l.addWidget(QLabel("Isolar camada:"))
        self.layer_combo = QComboBox()
        self.layer_combo.setMinimumWidth(240)
        self.layer_combo.currentIndexChanged.connect(self._on_layer_combo)
        top_l.addWidget(self.layer_combo)
        top_l.addSpacing(20)
        fit_btn = QPushButton("⊡ Ajustar ambos")
        fit_btn.clicked.connect(self._fit_both)
        top_l.addWidget(fit_btn)
        export_btn = QPushButton("⤓ Exportar comparação (PNG)")
        export_btn.clicked.connect(self._export_png)
        top_l.addWidget(export_btn)
        top_l.addStretch()
        root.addWidget(top)

        # ── Dois painéis ──
        splitter = QSplitter(Qt.Horizontal)
        self.panel_a = ComparePanel("A", base_project)
        self.panel_b = ComparePanel("B", base_project)
        splitter.addWidget(self.panel_a)
        splitter.addWidget(self.panel_b)
        splitter.setSizes([640, 640])
        root.addWidget(splitter, 1)

        # Defaults: A = projeto aberto; B = primeiro snapshot, se houver
        if base_project is not None:
            self.panel_a.title_edit.setText("Antes")
            snaps = base_project.list_snapshots()
            if snaps:
                # B → primeiro snapshot (índice 1: 0=current)
                self.panel_b.source_combo.setCurrentIndex(
                    min(1, self.panel_b.source_combo.count() - 1)
                )
                self.panel_b.title_edit.setText("Depois")
            else:
                self.panel_b.title_edit.setText("Depois")

        self.refresh_layer_combo()
        self._apply_style()

    # ── layer isolation combo (compartilhado) ──
    def refresh_layer_combo(self):
        names = []
        for p in (self.panel_a, self.panel_b):
            for n in p.layer_names():
                if n not in names:
                    names.append(n)
        cur = self.layer_combo.currentText()
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        self.layer_combo.addItem("Todas as camadas (visão completa)")
        for n in names:
            self.layer_combo.addItem(n)
        # restaura seleção, se ainda existir
        i = self.layer_combo.findText(cur)
        self.layer_combo.setCurrentIndex(i if i >= 0 else 0)
        self.layer_combo.blockSignals(False)

    def _on_layer_combo(self, index: int):
        if index <= 0:
            self._isolated_name = None
        else:
            self._isolated_name = self.layer_combo.currentText()
        self.panel_a.apply_isolation(self._isolated_name)
        self.panel_b.apply_isolation(self._isolated_name)

    def _fit_both(self):
        self.panel_a.view.fit_all()
        self.panel_b.view.fit_all()

    # ── export ──
    def _export_png(self):
        if not self.panel_a.project and not self.panel_b.project:
            QMessageBox.warning(self, "Aviso", "Carregue ecossistemas nos dois lados.")
            return
        default = "comparacao.png"
        if self._isolated_name:
            safe = self._isolated_name.replace(" ", "_")
            default = f"comparacao_{safe}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Comparação", default, "PNG (*.png)"
        )
        if not path:
            return
        try:
            self._compose_and_save(path)
            QMessageBox.information(self, "Exportado",
                                    f"Comparação salva em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

    def _compose_and_save(self, path: str, target_h: int = 1500):
        img_a = render_scene_image(self.panel_a.scene, target_h)
        img_b = render_scene_image(self.panel_b.scene, target_h)

        pad = 50
        header = 96
        gap = 70
        content_h = max(img_a.height(), img_b.height())
        total_w = pad + img_a.width() + gap + img_b.width() + pad
        total_h = header + content_h + pad

        canvas = QImage(total_w, total_h, QImage.Format_ARGB32)
        canvas.fill(QColor("#FFFFFF"))
        p = QPainter(canvas)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Subtítulo global (camada isolada)
        sub = f"Camada isolada: {self._isolated_name}" if self._isolated_name \
            else "Visão completa do ecossistema"
        p.setPen(QPen(QColor("#7F8C8D")))
        p.setFont(QFont("Helvetica", 13))
        p.drawText(QRectF(0, header - 30, total_w, 26),
                   Qt.AlignHCenter, sub)

        # Posições das imagens
        x_a = pad
        x_b = pad + img_a.width() + gap
        y_img = header
        y_a = y_img + (content_h - img_a.height()) // 2
        y_b = y_img + (content_h - img_b.height()) // 2
        p.drawImage(x_a, y_a, img_a)
        p.drawImage(x_b, y_b, img_b)

        # Títulos de cada lado
        p.setPen(QPen(QColor("#1A252F")))
        title_font = QFont("Helvetica", 22)
        title_font.setBold(True)
        p.setFont(title_font)
        ta = self.panel_a.export_title() or "A"
        tb = self.panel_b.export_title() or "B"
        p.drawText(QRectF(x_a, 16, img_a.width(), 40), Qt.AlignHCenter, ta)
        p.drawText(QRectF(x_b, 16, img_b.width(), 40), Qt.AlignHCenter, tb)

        # Divisória central
        divx = x_a + img_a.width() + gap // 2
        pen = QPen(QColor("#CED4DA"), 2)
        pen.setDashPattern([6, 6])
        p.setPen(pen)
        p.drawLine(divx, header, divx, header + content_h)

        # Seta "antes → depois"
        p.setPen(QPen(QColor("#89B4FA"), 3))
        cy = header + content_h // 2
        p.drawLine(divx - 14, cy, divx + 14, cy)
        p.drawLine(divx + 14, cy, divx + 4, cy - 9)
        p.drawLine(divx + 14, cy, divx + 4, cy + 9)

        p.end()
        canvas.save(path)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E2E; }
            QWidget { color: #CDD6F4; }
            QWidget#cmpTop { background-color: #181825; border-bottom: 1px solid #313244; }
            QLabel { color: #CDD6F4; }
            QPushButton {
                background-color: #89B4FA; color: #1E1E2E; border: none;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74C7EC; }
            QLineEdit, QComboBox {
                background-color: #313244; border: 1px solid #45475A;
                border-radius: 4px; padding: 5px 8px; color: #CDD6F4;
            }
            QComboBox QAbstractItemView {
                background-color: #313244; border: 1px solid #45475A;
                color: #CDD6F4; selection-background-color: #89B4FA;
                selection-color: #1E1E2E;
            }
            QSplitter::handle { background-color: #313244; width: 2px; }
        """)
