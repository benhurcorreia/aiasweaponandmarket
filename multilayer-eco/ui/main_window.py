"""
MultilayerEco - Main Window
Janela principal do aplicativo.
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QGroupBox, QMessageBox,
    QFileDialog, QApplication, QDockWidget, QFrame,
    QSizePolicy, QComboBox, QSpinBox,
    QInputDialog, QDialog, QDialogButtonBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QKeySequence, QAction

from core.models import (
    Project, Actor, Layer, Relationship,
    ACTOR_TYPE_COLORS, RELATION_TYPE_STYLES
)
from core.graph_engine import GraphEngine
from core.i18n import tr, tr_parts, get_language, set_language
from core.versatility import VersatilityEngine
from ui.canvas import MultilayerScene, MultilayerView
from ui.comparison import ComparisonWindow
from ui.dialogs.dialogs import (
    AddLayerDialog, AddActorDialog, AddRelationDialog,
    ExtractionDialog, SettingsDialog, ActorTypeManagerDialog
)
from export.exporters import (
    export_json, export_actors_csv,
    export_relationships_csv, export_metrics_csv
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.project = Project(name="Novo Projeto")
        self.settings = {
            "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "gemini_api_key": os.environ.get("GOOGLE_API_KEY", ""),
            "layout_algorithm": "spring",
            "isometric": True,
            "view_mode": "diagonal",
            "layer_font": 14,
            "node_font": 11,
            "node_radius": 14,
            "stair_dx": 380,
            "stair_dy": 300,
        }
        self._custom_actor_types = []   # user-defined actor types
        self._current_file = None

        self.setWindowTitle(tr("MultilayerEco — Ecossistemas de Negócios Multinível"))
        self.setMinimumSize(1200, 800)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()

        # Apply stylesheet
        self._apply_style()

    def _setup_ui(self):
        """Setup the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ─── LEFT PANEL ───
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_panel.setMaximumWidth(280)
        left_panel.setMinimumWidth(220)

        # Layers section
        layers_group = QGroupBox(tr("Camadas"))
        layers_layout = QVBoxLayout(layers_group)
        self.layers_list = QListWidget()
        self.layers_list.setMaximumHeight(150)
        self.layers_list.itemClicked.connect(self._on_layer_selected)
        layers_layout.addWidget(self.layers_list)

        layers_btn_layout = QHBoxLayout()
        add_layer_btn = QPushButton("+")
        add_layer_btn.setToolTip(tr("Adicionar Camada"))
        add_layer_btn.setFixedSize(32, 32)
        add_layer_btn.clicked.connect(self._add_layer)
        del_layer_btn = QPushButton("−")
        del_layer_btn.setToolTip(tr("Remover Camada"))
        del_layer_btn.setFixedSize(32, 32)
        del_layer_btn.clicked.connect(self._remove_layer)
        up_layer_btn = QPushButton("↑")
        up_layer_btn.setToolTip(tr("Mover camada para cima"))
        up_layer_btn.setFixedSize(32, 32)
        up_layer_btn.clicked.connect(self._move_layer_up)
        dn_layer_btn = QPushButton("↓")
        dn_layer_btn.setToolTip(tr("Mover camada para baixo"))
        dn_layer_btn.setFixedSize(32, 32)
        dn_layer_btn.clicked.connect(self._move_layer_down)
        layers_btn_layout.addWidget(add_layer_btn)
        layers_btn_layout.addWidget(del_layer_btn)
        layers_btn_layout.addWidget(up_layer_btn)
        layers_btn_layout.addWidget(dn_layer_btn)
        layers_btn_layout.addStretch()
        layers_layout.addLayout(layers_btn_layout)
        left_layout.addWidget(layers_group)

        # Actors section
        actors_group = QGroupBox(tr("Atores"))
        actors_layout = QVBoxLayout(actors_group)
        self.actors_list = QListWidget()
        self.actors_list.itemClicked.connect(self._on_actor_selected)
        self.actors_list.itemDoubleClicked.connect(self._edit_actor)
        actors_layout.addWidget(self.actors_list)

        actors_btn_layout = QHBoxLayout()
        add_actor_btn = QPushButton("+")
        add_actor_btn.setToolTip(tr("Adicionar Ator"))
        add_actor_btn.setFixedSize(32, 32)
        add_actor_btn.clicked.connect(self._add_actor)
        del_actor_btn = QPushButton("−")
        del_actor_btn.setToolTip(tr("Remover Ator"))
        del_actor_btn.setFixedSize(32, 32)
        del_actor_btn.clicked.connect(self._remove_actor)
        edit_actor_btn = QPushButton("✎")
        edit_actor_btn.setToolTip(tr("Editar Ator"))
        edit_actor_btn.setFixedSize(32, 32)
        edit_actor_btn.clicked.connect(self._edit_actor)
        actors_btn_layout.addWidget(add_actor_btn)
        actors_btn_layout.addWidget(edit_actor_btn)
        actors_btn_layout.addWidget(del_actor_btn)
        actors_btn_layout.addStretch()
        actors_layout.addLayout(actors_btn_layout)
        left_layout.addWidget(actors_group)

        # Relations section
        relations_group = QGroupBox(tr("Relações"))
        relations_layout = QVBoxLayout(relations_group)
        self.relations_list = QListWidget()
        self.relations_list.setMaximumHeight(200)
        self.relations_list.itemDoubleClicked.connect(self._edit_relation)
        relations_layout.addWidget(self.relations_list)

        rel_btn_layout = QHBoxLayout()
        add_rel_btn = QPushButton("+")
        add_rel_btn.setToolTip(tr("Adicionar Relação"))
        add_rel_btn.setFixedSize(32, 32)
        add_rel_btn.clicked.connect(self._add_relation)
        del_rel_btn = QPushButton("−")
        del_rel_btn.setToolTip(tr("Remover Relação"))
        del_rel_btn.setFixedSize(32, 32)
        del_rel_btn.clicked.connect(self._remove_relation)
        rel_btn_layout.addWidget(add_rel_btn)
        rel_btn_layout.addWidget(del_rel_btn)
        rel_btn_layout.addStretch()
        relations_layout.addLayout(rel_btn_layout)
        left_layout.addWidget(relations_group)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # ─── CENTER: CANVAS + ZOOM BAR ───
        canvas_container = QWidget()
        canvas_container.setObjectName("canvasContainer")
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.scene = MultilayerScene()
        self.view = MultilayerView(self.scene)
        canvas_layout.addWidget(self.view)

        # Zoom control bar (below canvas)
        zoom_bar = QWidget()
        zoom_bar.setObjectName("zoomBar")
        zoom_bar.setFixedHeight(36)
        zoom_bar.setStyleSheet(
            "QWidget#zoomBar { background-color: #181825; border-top: 1px solid #313244; }"
        )
        zoom_bar_layout = QHBoxLayout(zoom_bar)
        zoom_bar_layout.setContentsMargins(10, 0, 10, 0)
        zoom_bar_layout.setSpacing(6)

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(28, 24)
        zoom_out_btn.setToolTip(tr("Diminuir zoom"))
        zoom_out_btn.clicked.connect(lambda: self.view.zoom_step(-1))

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(28, 24)
        zoom_in_btn.setToolTip(tr("Aumentar zoom"))
        zoom_in_btn.clicked.connect(lambda: self.view.zoom_step(+1))

        from PySide6.QtWidgets import QSlider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(-40, 40)
        self.zoom_slider.setValue(0)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.setToolTip(tr("Nível de zoom"))
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(44)
        self.zoom_label.setStyleSheet("color: #A6ADC8; font-size: 11px;")

        fit_zoom_btn = QPushButton("⊡ Fit")
        fit_zoom_btn.setFixedHeight(24)
        fit_zoom_btn.setToolTip(tr("Ajustar toda a cena na janela"))
        fit_zoom_btn.clicked.connect(self._fit_all)

        pan_hint = QLabel(tr("Scroll: zoom  |  Meio/Espaço: mover"))
        pan_hint.setStyleSheet("color: #585B70; font-size: 10px;")

        zoom_bar_layout.addWidget(zoom_out_btn)
        zoom_bar_layout.addWidget(self.zoom_slider)
        zoom_bar_layout.addWidget(zoom_in_btn)
        zoom_bar_layout.addWidget(self.zoom_label)
        zoom_bar_layout.addSpacing(10)
        zoom_bar_layout.addWidget(fit_zoom_btn)
        zoom_bar_layout.addSpacing(12)

        # ─── Botão modo Mover ───
        self.pan_btn = QPushButton(tr("✋ Mover"))
        self.pan_btn.setCheckable(True)
        self.pan_btn.setFixedHeight(24)
        self.pan_btn.setToolTip(
            tr("Modo Mover: clique+arraste para navegar no mapa\n"
               "Atalho: segure Espaço para mover temporariamente")
        )
        self.pan_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border: 1px solid #585B70; border-radius: 4px; padding: 0 10px; font-weight: normal; }"
            "QPushButton:checked { background-color: #89B4FA; color: #1E1E2E; border-color: #89B4FA; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
            "QPushButton:checked:hover { background-color: #74C7EC; }"
        )
        self.pan_btn.toggled.connect(self.view.toggle_pan_mode)
        zoom_bar_layout.addWidget(self.pan_btn)
        zoom_bar_layout.addSpacing(4)

        spread_btn = QPushButton(tr("⊞ Espalhar"))
        spread_btn.setFixedHeight(24)
        spread_btn.setToolTip(
            tr("Redistribui automaticamente os atores de cada camada\n"
               "em grade, eliminando sobreposições")
        )
        spread_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border: 1px solid #585B70; border-radius: 4px; padding: 0 10px; font-weight: normal; }"
            "QPushButton:hover { background-color: #585B70; }"
            "QPushButton:pressed { background-color: #74C7EC; color: #1E1E2E; }"
        )
        spread_btn.clicked.connect(lambda: (
            self.scene.spread_actors(),
            self._fit_all()
        ))
        zoom_bar_layout.addWidget(spread_btn)
        zoom_bar_layout.addSpacing(20)

        # ─── Controle de tamanho da fonte dos nós ───
        font_lbl = QLabel(tr("Fonte nós:"))
        font_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        zoom_bar_layout.addWidget(font_lbl)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 60)
        self.font_size_spin.setValue(self.settings.get("node_font", 11))
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.setFixedWidth(64)
        self.font_size_spin.setFixedHeight(24)
        self.font_size_spin.setToolTip(tr("Tamanho da fonte dos nomes dos atores (6–60 pt)"))
        self.font_size_spin.valueChanged.connect(
            lambda v: self.scene.set_node_font_size(v)
        )
        zoom_bar_layout.addWidget(self.font_size_spin)

        # ─── Controle de tamanho do nó ───
        node_lbl = QLabel(tr("Tamanho nó:"))
        node_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        zoom_bar_layout.addWidget(node_lbl)

        self.node_size_spin = QSpinBox()
        self.node_size_spin.setRange(3, 48)
        self.node_size_spin.setValue(self.settings.get("node_radius", 14))
        self.node_size_spin.setSuffix(" px")
        self.node_size_spin.setFixedWidth(64)
        self.node_size_spin.setFixedHeight(24)
        self.node_size_spin.setToolTip(tr("Tamanho (raio) dos nós dos atores (3–48 px)"))
        self.node_size_spin.valueChanged.connect(
            lambda v: self.scene.set_node_radius(v)
        )
        zoom_bar_layout.addWidget(self.node_size_spin)

        # ─── Fonte do nome das camadas ───
        lfont_lbl = QLabel(tr("Fonte camada:"))
        lfont_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        zoom_bar_layout.addWidget(lfont_lbl)

        self.layer_font_spin = QSpinBox()
        self.layer_font_spin.setRange(8, 48)
        self.layer_font_spin.setValue(self.settings.get("layer_font", 14))
        self.layer_font_spin.setSuffix(" pt")
        self.layer_font_spin.setFixedWidth(64)
        self.layer_font_spin.setFixedHeight(24)
        self.layer_font_spin.setToolTip(tr("Tamanho da fonte do nome das camadas (8–48 pt)"))
        self.layer_font_spin.valueChanged.connect(
            lambda v: self.scene.set_layer_font_size(v)
        )
        zoom_bar_layout.addWidget(self.layer_font_spin)

        # ─── Modo de visualização das camadas ───
        view_lbl = QLabel(tr("Vista:"))
        view_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        zoom_bar_layout.addWidget(view_lbl)

        self.view_mode_combo = QComboBox()
        for rotulo, val in ((tr("Diagonal"), "diagonal"),
                            (tr("Vertical"), "vertical"),
                            (tr("Matriz"), "matrix"),
                            (tr("Agregado"), "flat")):
            self.view_mode_combo.addItem(rotulo, val)
        i0 = self.view_mode_combo.findData(self.settings.get("view_mode", "diagonal"))
        if i0 >= 0:
            self.view_mode_combo.setCurrentIndex(i0)
        self.view_mode_combo.setFixedHeight(24)
        self.view_mode_combo.setToolTip(tr("Modo de visualização das camadas"))
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        zoom_bar_layout.addWidget(self.view_mode_combo)

        zoom_bar_layout.addStretch()
        zoom_bar_layout.addWidget(pan_hint)

        canvas_layout.addWidget(zoom_bar)
        splitter.addWidget(canvas_container)

        # ─── RIGHT PANEL ───
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_panel.setMaximumWidth(260)
        right_panel.setMinimumWidth(200)

        # Properties
        props_group = QGroupBox(tr("Propriedades"))
        props_layout = QVBoxLayout(props_group)
        self.props_label = QLabel(tr("Selecione um ator ou relação\npara ver propriedades."))
        self.props_label.setWordWrap(True)
        self.props_label.setStyleSheet("color: #A6ADC8; font-style: italic;")
        props_layout.addWidget(self.props_label)
        right_layout.addWidget(props_group)

        # Metrics
        metrics_group = QGroupBox(tr("Métricas da Rede"))
        metrics_layout = QVBoxLayout(metrics_group)
        self.metrics_label = QLabel(tr("Adicione camadas e atores\npara ver métricas."))
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        metrics_layout.addWidget(self.metrics_label)
        right_layout.addWidget(metrics_group)

        # View / layer isolation controls
        view_group = QGroupBox(tr("Visualização"))
        view_v = QVBoxLayout(view_group)
        iso_lbl = QLabel(tr("Camada isolada (2D):"))
        iso_lbl.setStyleSheet("color:#A6ADC8; font-size:11px;")
        view_v.addWidget(iso_lbl)
        self.isolate_combo = QComboBox()
        self.isolate_combo.setToolTip(
            tr("Mostra apenas uma camada, de frente (2D plano).\n"
               "Escolha 'Todas as camadas' para a visão completa em escada.")
        )
        self.isolate_combo.currentIndexChanged.connect(self._on_isolate_changed)
        view_v.addWidget(self.isolate_combo)
        right_layout.addWidget(view_group)

        # Layout controls
        layout_group = QGroupBox("Layout")
        layout_controls = QVBoxLayout(layout_group)

        self.layout_combo = QComboBox()
        for alg in ["spring", "circular", "spectral", "kamada_kawai", "shell"]:
            self.layout_combo.addItem(alg)
        layout_controls.addWidget(self.layout_combo)

        relayout_btn = QPushButton(tr("↻ Recalcular Layout"))
        relayout_btn.clicked.connect(self._recalculate_layout)
        layout_controls.addWidget(relayout_btn)

        right_layout.addWidget(layout_group)
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([250, 700, 250])

        # Connect view zoom → sync slider/label
        self.view.zoom_changed.connect(self._sync_zoom_slider)

    def _setup_menus(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(tr("Arquivo"))

        new_action = file_menu.addAction(tr("Novo Projeto"))
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_project)

        open_action = file_menu.addAction(tr("Abrir Projeto..."))
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_project)

        save_action = file_menu.addAction(tr("Salvar Projeto"))
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_project)

        save_as_action = file_menu.addAction(tr("Salvar Como..."))
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_project_as)

        file_menu.addSeparator()
        quit_action = file_menu.addAction(tr("Sair"))
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)

        # Edit menu
        edit_menu = menubar.addMenu(tr("Editar"))
        edit_menu.addAction(tr("Adicionar Camada"), self._add_layer)
        edit_menu.addAction(tr("Adicionar Ator"), self._add_actor)
        edit_menu.addAction(tr("Adicionar Relação"), self._add_relation)
        edit_menu.addSeparator()
        edit_menu.addAction(tr("Gerenciar Tipos de Ator..."), self._manage_actor_types)
        edit_menu.addSeparator()
        edit_menu.addAction(tr("Configurações..."), self._show_settings)

        # Analysis menu
        analysis_menu = menubar.addMenu(tr("Análise"))
        analysis_menu.addAction(tr("Extrair de Documento (LLM)..."), self._run_extraction)
        analysis_menu.addSeparator()
        analysis_menu.addAction(tr("Comparar Ecossistemas (Antes/Depois)..."), self._open_comparison)
        analysis_menu.addSeparator()
        analysis_menu.addAction(tr("Recalcular Layout"), self._recalculate_layout)
        analysis_menu.addAction(tr("Calcular Métricas"), self._update_metrics)
        analysis_menu.addAction(tr("Versatilidade e Participação..."), self._open_versatility)
        analysis_menu.addAction(tr("Alinhar atores entre camadas (posição única)"),
                                self._align_actors)

        # Snapshots ("momentos") menu
        snap_menu = menubar.addMenu(tr("Momentos"))
        snap_menu.addAction(tr("Salvar Momento Atual..."), self._save_snapshot)
        snap_menu.addAction(tr("Gerenciar Momentos..."), self._manage_snapshots)
        snap_menu.addSeparator()
        snap_menu.addAction(tr("Comparar Momentos..."), self._open_comparison)

        # Export menu
        export_menu = menubar.addMenu(tr("Exportar"))
        export_menu.addAction(tr("Exportar Imagem (PNG)..."), self._export_png)
        export_menu.addSeparator()
        export_menu.addAction(tr("Exportar Projeto (JSON)..."), self._export_json)
        export_menu.addAction(tr("Exportar Atores (CSV)..."), self._export_actors_csv)
        export_menu.addAction(tr("Exportar Relações (CSV)..."), self._export_relations_csv)
        export_menu.addAction(tr("Exportar Métricas (CSV)..."), self._export_metrics_csv)

        # Language menu
        lang_menu = menubar.addMenu(tr("Idioma / Language"))
        self._lang_pt_action = QAction("Português", self, checkable=True)
        self._lang_en_action = QAction("English", self, checkable=True)
        self._lang_pt_action.setChecked(get_language() == "pt")
        self._lang_en_action.setChecked(get_language() == "en")
        self._lang_pt_action.triggered.connect(lambda: self._set_language("pt"))
        self._lang_en_action.triggered.connect(lambda: self._set_language("en"))
        lang_menu.addAction(self._lang_pt_action)
        lang_menu.addAction(self._lang_en_action)

    def _set_language(self, lang: str):
        """Troca o idioma, atualiza a cena/listas e avisa sobre reinício."""
        if lang == get_language():
            self._lang_pt_action.setChecked(lang == "pt")
            self._lang_en_action.setChecked(lang == "en")
            return
        set_language(lang)
        self._lang_pt_action.setChecked(lang == "pt")
        self._lang_en_action.setChecked(lang == "en")
        # Figuras e listas atualizam imediatamente; menus exigem reinício
        self.scene.rebuild()
        self._refresh_layers_list()
        self._refresh_actors_list()
        self._refresh_relations_list()
        self._update_statusbar()
        self._update_metrics()
        QMessageBox.information(
            self, tr("Idioma / Language"),
            tr("Idioma alterado. Reinicie o aplicativo para aplicar "
               "em toda a interface."))

    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = self.addToolBar(tr("Principal"))
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)

        toolbar.addAction(tr("Novo"), self._new_project)
        toolbar.addAction(tr("Abrir"), self._open_project)
        toolbar.addAction(tr("Salvar"), self._save_project)
        toolbar.addSeparator()
        toolbar.addAction(tr("+ Camada"), self._add_layer)
        toolbar.addAction(tr("+ Ator"), self._add_actor)
        toolbar.addAction(tr("+ Relação"), self._add_relation)
        toolbar.addSeparator()
        toolbar.addAction("LLM Extract", self._run_extraction)
        toolbar.addSeparator()
        toolbar.addAction(tr("⇄ Comparar"), self._open_comparison)
        toolbar.addAction("Vi / Pi", self._open_versatility)
        toolbar.addSeparator()
        toolbar.addAction("PNG", self._export_png)
        toolbar.addSeparator()
        toolbar.addAction("Fit", lambda: self.view.fit_all())

    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self._update_statusbar()

    def _apply_style(self):
        """Apply dark theme stylesheet."""
        self.setStyleSheet("""
            /* ── Global Dark Theme ── */
            QMainWindow { background-color: #1E1E2E; }
            QWidget { color: #CDD6F4; }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #45475A;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 18px;
                background-color: #2A2A3C;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #89B4FA;
            }

            QListWidget {
                border: 1px solid #45475A;
                border-radius: 4px;
                background-color: #313244;
                color: #CDD6F4;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-bottom: 1px solid #3B3B50;
            }
            QListWidget::item:selected {
                background-color: #89B4FA;
                color: #1E1E2E;
            }
            QListWidget::item:hover {
                background-color: #3B3B50;
            }

            QPushButton {
                background-color: #89B4FA;
                color: #1E1E2E;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #74C7EC; }
            QPushButton:pressed { background-color: #5B9BD5; }
            QPushButton:disabled { background-color: #45475A; color: #6C7086; }

            QToolBar {
                background-color: #181825;
                border: none;
                border-bottom: 1px solid #313244;
                spacing: 4px;
                padding: 4px;
            }
            QToolBar QToolButton {
                color: #CDD6F4;
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QToolBar QToolButton:hover {
                background-color: #313244;
                border-color: #89B4FA;
            }

            QMenuBar {
                background-color: #181825;
                color: #CDD6F4;
                border-bottom: 1px solid #313244;
            }
            QMenuBar::item:selected { background-color: #313244; }
            QMenu {
                background-color: #2A2A3C;
                border: 1px solid #45475A;
                color: #CDD6F4;
            }
            QMenu::item:selected { background-color: #89B4FA; color: #1E1E2E; }
            QMenu::separator { background-color: #45475A; height: 1px; margin: 4px 8px; }

            QStatusBar {
                background-color: #181825;
                color: #A6ADC8;
                border-top: 1px solid #313244;
            }

            QComboBox {
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 5px 8px;
                background-color: #313244;
                color: #CDD6F4;
            }
            QComboBox:hover { border-color: #89B4FA; }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                border: 1px solid #45475A;
                color: #CDD6F4;
                selection-background-color: #89B4FA;
                selection-color: #1E1E2E;
            }

            QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 5px 8px;
                color: #CDD6F4;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
                border-color: #89B4FA;
            }

            QLabel { color: #CDD6F4; }

            QCheckBox { color: #CDD6F4; spacing: 6px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #45475A;
                border-radius: 3px;
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #89B4FA;
                border-color: #89B4FA;
            }

            QProgressBar {
                border: 1px solid #45475A;
                border-radius: 4px;
                text-align: center;
                background-color: #313244;
                color: #CDD6F4;
            }
            QProgressBar::chunk {
                background-color: #89B4FA;
                border-radius: 3px;
            }

            QSplitter::handle { background-color: #313244; width: 2px; }

            QScrollBar:vertical {
                background-color: #1E1E2E;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #45475A;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background-color: #585B70; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

            QScrollBar:horizontal {
                background-color: #1E1E2E;
                height: 10px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #45475A;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background-color: #585B70; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

            QDialogButtonBox QPushButton {
                min-width: 80px;
                padding: 6px 16px;
            }

            QTabWidget::pane {
                border: 1px solid #45475A;
                background-color: #2A2A3C;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #CDD6F4;
                padding: 6px 16px;
                border: 1px solid #45475A;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2A2A3C;
                color: #89B4FA;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background-color: #45475A;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #89B4FA;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover { background-color: #74C7EC; }
        """)

    # ─── LAYER ACTIONS ───

    def _add_layer(self):
        dlg = AddLayerDialog(self.project, self)
        if dlg.exec():
            data = dlg.get_data()
            if data["name"]:
                self.project.add_layer(data["name"], data["color"])
                self._refresh_all()

    def _remove_layer(self):
        item = self.layers_list.currentItem()
        if not item:
            return
        layer_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, tr("Remover Camada"),
            tr("Remover a camada '{name}'?\n"
               "Atores exclusivos desta camada serão removidos.").format(name=item.text()),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.project.remove_layer(layer_id)
            self._refresh_all()

    def _move_layer_up(self):
        """Aumenta a ordem da camada selecionada (move para cima na cena)."""
        item = self.layers_list.currentItem()
        if not item:
            return
        layer_id = item.data(Qt.UserRole)
        layers = sorted(self.project.layers, key=lambda l: l.order)
        idx = next((i for i, l in enumerate(layers) if l.id == layer_id), None)
        if idx is None or idx >= len(layers) - 1:
            return  # já é a camada do topo
        # Troca a ordem com a camada acima
        layers[idx].order, layers[idx + 1].order = layers[idx + 1].order, layers[idx].order
        self._refresh_layers_list()
        self.scene.set_project(self.project)
        self._fit_all()
        # Re-selecionar a camada movida
        for i in range(self.layers_list.count()):
            if self.layers_list.item(i).data(Qt.UserRole) == layer_id:
                self.layers_list.setCurrentRow(i)
                break

    def _move_layer_down(self):
        """Diminui a ordem da camada selecionada (move para baixo na cena)."""
        item = self.layers_list.currentItem()
        if not item:
            return
        layer_id = item.data(Qt.UserRole)
        layers = sorted(self.project.layers, key=lambda l: l.order)
        idx = next((i for i, l in enumerate(layers) if l.id == layer_id), None)
        if idx is None or idx == 0:
            return  # já é a camada mais baixa
        # Troca a ordem com a camada abaixo
        layers[idx].order, layers[idx - 1].order = layers[idx - 1].order, layers[idx].order
        self._refresh_layers_list()
        self.scene.set_project(self.project)
        self._fit_all()
        # Re-selecionar a camada movida
        for i in range(self.layers_list.count()):
            if self.layers_list.item(i).data(Qt.UserRole) == layer_id:
                self.layers_list.setCurrentRow(i)
                break

    def _on_layer_selected(self, item):
        layer_id = item.data(Qt.UserRole)
        layer = self.project.get_layer_by_id(layer_id)
        if layer:
            actors = self.project.get_actors_in_layer(layer_id)
            rels = self.project.get_relationships_in_layer(layer_id)
            self.props_label.setText(
                tr("Camada: {name}\nOrdem: {order}\nAtores: {actors}\nRelações: {rels}").format(
                    name=tr(layer.name), order=layer.order,
                    actors=len(actors), rels=len(rels))
            )

    # ─── ACTOR ACTIONS ───

    def _add_actor(self):
        if not self.project.layers:
            QMessageBox.warning(self, tr("Aviso"), tr("Adicione pelo menos uma camada primeiro."))
            return
        dlg = AddActorDialog(self.project, custom_types=self._custom_actor_types, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if data["name"]:
                self.project.add_actor(data["name"], data["actor_type"], data["layers"])
                self._refresh_all()

    def _edit_actor(self, item=None):
        if not item:
            item = self.actors_list.currentItem()
        if not item:
            return
        actor_id = item.data(Qt.UserRole)
        actor = self.project.actors.get(actor_id)
        if not actor:
            return
        dlg = AddActorDialog(self.project, actor,
                             custom_types=self._custom_actor_types, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            actor.name = data["name"]
            actor.actor_type = data["actor_type"]
            actor.layers = data["layers"]
            self._refresh_all()

    def _manage_actor_types(self):
        dlg = ActorTypeManagerDialog(self._custom_actor_types, self)
        dlg.exec()
        self._custom_actor_types = dlg.get_custom_types()

    def _remove_actor(self):
        item = self.actors_list.currentItem()
        if not item:
            return
        actor_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, tr("Remover Ator"),
            tr("Remover '{name}' e todas as suas relações?").format(name=item.text()),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.project.remove_actor(actor_id)
            self._refresh_all()

    def _on_actor_selected(self, item):
        actor_id = item.data(Qt.UserRole)
        actor = self.project.actors.get(actor_id)
        if actor:
            layer_names = []
            for lid in actor.layers:
                l = self.project.get_layer_by_id(lid)
                if l:
                    layer_names.append(l.name)
            rels = self.project.get_actor_relationships(actor_id)
            text = tr("Ator: {name}\nTipo: {type}\nCamadas: {layers}\nRelações: {rels}").format(
                name=actor.name, type=tr(actor.actor_type),
                layers=', '.join(tr(n) for n in layer_names), rels=len(rels))
            # Centrality
            try:
                engine = GraphEngine(self.project)
                cent = engine.get_actor_centrality(actor_id)
                for lid, metrics in cent.items():
                    l = self.project.get_layer_by_id(lid)
                    if l:
                        deg_lbl = "degree" if get_language() == "en" else "grau"
                        text += f"\n  {tr(l.name)}: {deg_lbl}={metrics['degree']}, cent={metrics['degree_centrality']:.3f}"
            except:
                pass
            self.props_label.setText(text)

    # ─── RELATION ACTIONS ───

    def _add_relation(self):
        if len(self.project.actors) < 2:
            QMessageBox.warning(self, tr("Aviso"), tr("Adicione pelo menos dois atores primeiro."))
            return
        dlg = AddRelationDialog(self.project, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.project.add_relationship(**data)
            self._refresh_all()

    def _edit_relation(self, item=None):
        if not item:
            item = self.relations_list.currentItem()
        if not item:
            return
        rel_id = item.data(Qt.UserRole)
        rel = None
        for r in self.project.relationships:
            if r.id == rel_id:
                rel = r
                break
        if not rel:
            return
        dlg = AddRelationDialog(self.project, rel, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            # Update relationship
            rel.source_id = data["source_id"]
            rel.target_id = data["target_id"]
            rel.layer_id = data["layer_id"]
            rel.rel_type = data["rel_type"]
            rel.direction = data["direction"]
            rel.label = data["label"]
            rel.weight = data["weight"]
            rel.source_layer_id = data["source_layer_id"]
            rel.target_layer_id = data["target_layer_id"]
            self._refresh_all()

    def _remove_relation(self):
        item = self.relations_list.currentItem()
        if not item:
            return
        rel_id = item.data(Qt.UserRole)
        self.project.remove_relationship(rel_id)
        self._refresh_all()

    # ─── EXTRACTION ───

    def _run_extraction(self):
        dlg = ExtractionDialog(self.project, self)
        dlg.extraction_done.connect(self._apply_extraction)
        dlg.exec()

    def _apply_extraction(self, result: dict):
        from extraction.llm_extractor import apply_extraction_to_project

        # Create layers if needed
        for actor_data in result.get("actors", []):
            for layer_name in actor_data.get("layers", []):
                if not self.project.get_layer_by_name(layer_name.strip()):
                    self.project.add_layer(layer_name.strip())

        # Also from relations
        for rel in result.get("intra_layer_relations", []):
            ln = rel.get("layer", "").strip()
            if ln and not self.project.get_layer_by_name(ln):
                self.project.add_layer(ln)
        for rel in result.get("inter_layer_relations", []):
            for key in ("source_layer", "target_layer"):
                ln = rel.get(key, "").strip()
                if ln and not self.project.get_layer_by_name(ln):
                    self.project.add_layer(ln)

        apply_extraction_to_project(self.project, result)
        self._recalculate_layout()
        self._refresh_all()
        self.statusbar.showMessage(tr("Extração aplicada com sucesso!"), 5000)

    # ─── LAYOUT & REFRESH ───

    def _recalculate_layout(self):
        engine = GraphEngine(self.project)
        algorithm = self.layout_combo.currentText()
        engine.compute_all_layouts(
            width=600,
            height=400,
            algorithm=algorithm
        )
        self.scene.set_project(self.project)
        self._fit_all()
        self._update_metrics()

    def _refresh_all(self):
        """Refresh all UI elements."""
        self._refresh_layers_list()
        self._refresh_actors_list()
        self._refresh_relations_list()
        self._recalculate_layout()
        self._update_statusbar()

    def _refresh_layers_list(self):
        self.layers_list.clear()
        for layer in sorted(self.project.layers, key=lambda l: l.order):
            n_actors = len(self.project.get_actors_in_layer(layer.id))
            item = QListWidgetItem(
                f"  {tr(layer.name)} ({tr('{n} atores').format(n=n_actors)})")
            item.setData(Qt.UserRole, layer.id)
            item.setForeground(QColor(layer.color))
            self.layers_list.addItem(item)
        self._refresh_isolate_combo()

    def _refresh_actors_list(self):
        self.actors_list.clear()
        for actor in sorted(self.project.actors.values(), key=lambda a: a.name):
            color = actor.color or ACTOR_TYPE_COLORS.get(actor.actor_type, "#4A90D9")
            item = QListWidgetItem(f"  {actor.name}")
            item.setData(Qt.UserRole, actor.id)
            item.setToolTip(tr("Tipo: {type} | Camadas: {n}").format(
                type=tr(actor.actor_type), n=len(actor.layers)))
            item.setForeground(QColor(color))
            self.actors_list.addItem(item)

    def _refresh_relations_list(self):
        self.relations_list.clear()
        for rel in self.project.relationships:
            src = self.project.actors.get(rel.source_id)
            tgt = self.project.actors.get(rel.target_id)
            if not src or not tgt:
                continue

            if rel.is_inter_layer:
                sl = self.project.get_layer_by_id(rel.source_layer_id)
                tl = self.project.get_layer_by_id(rel.target_layer_id)
                text = f"  {src.name} → {tgt.name} [{tr(rel.rel_type)}] (inter)"
            else:
                layer = self.project.get_layer_by_id(rel.layer_id)
                ln = tr(layer.name) if layer else "?"
                arrow = "↔" if rel.direction == "bidirectional" else "→"
                text = f"  {src.name} {arrow} {tgt.name} [{tr(rel.rel_type)}] ({ln})"

            style = RELATION_TYPE_STYLES.get(rel.rel_type, {})
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, rel.id)
            item.setForeground(QColor(style.get("color", "#7F8C8D")))
            self.relations_list.addItem(item)

    def _update_statusbar(self):
        n_layers = len(self.project.layers)
        n_actors = len(self.project.actors)
        n_rels = len(self.project.relationships)
        self.statusbar.showMessage(
            "  " + tr("{name} | {layers} camadas | {actors} atores | {rels} relações").format(
                name=self.project.name, layers=n_layers,
                actors=n_actors, rels=n_rels)
        )

    def _update_metrics(self):
        if not self.project.layers:
            self.metrics_label.setText(tr("Adicione camadas e atores\npara ver métricas."))
            return
        try:
            engine = GraphEngine(self.project)
            text = ""
            for layer in self.project.layers:
                m = engine.get_layer_metrics(layer.id)
                text += tr("▸ {name}\n  Nós: {nodes} | Arestas: {edges}\n  Densidade: {density:.4f}\n").format(
                    name=tr(layer.name), nodes=m['nodes'],
                    edges=m['edges'], density=m['density'])
            stats = engine.get_cross_layer_stats()
            if stats["shared_actors"]:
                text += tr("\n▸ Inter-Camada\n")
                for pair, count in stats["shared_actors"].items():
                    text += tr("  {pair}: {count} compartilhados\n").format(
                        pair=pair, count=count)
            self.metrics_label.setText(text)
        except Exception as e:
            self.metrics_label.setText(tr("Erro: {msg}").format(msg=str(e)[:100]))

    def _open_versatility(self):
        if not self.project.layers or not self.project.actors:
            QMessageBox.information(
                self, tr("Versatilidade"),
                tr("Adicione camadas, atores e relações antes de calcular "
                   "a versatilidade."))
            return
        dlg = VersatilityDialog(self.project, self)
        dlg.exec()

    def _on_view_mode_changed(self, _idx):
        mode = self.view_mode_combo.currentData()
        self.settings["view_mode"] = mode
        if mode == "vertical":
            self.scene.stair_dy = max(self.settings.get("stair_dy", 300), 360)
        else:
            self.scene.stair_dy = self.settings.get("stair_dy", 300)
        self.scene.set_view_mode(mode)
        if hasattr(self, "view"):
            self.view.fit_all()

    def _align_actors(self):
        if not self.project or not self.project.actors:
            QMessageBox.information(
                self, tr("Alinhar atores"),
                tr("Carregue um ecossistema com atores e relações primeiro."))
            return
        self.scene.align_actor_positions()
        self.view.fit_all()
        self.statusbar.showMessage(
            tr("Posições alinhadas: cada ator ocupa a mesma posição em todas as "
               "suas camadas (centralidade → centro)."), 6000)

    # ─── FILE OPERATIONS ───

    def _new_project(self):
        reply = QMessageBox.question(
            self, tr("Novo Projeto"),
            tr("Criar novo projeto? Mudanças não salvas serão perdidas."),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.project = Project(name="Novo Projeto")
            self._current_file = None
            self._refresh_all()

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Abrir Projeto"),
            "", tr("Projeto MultilayerEco (*.mleco *.json)")
        )
        if path:
            try:
                self.project = Project.load(path)
                self._current_file = path
                self._refresh_all()
                self.statusbar.showMessage(tr("Projeto carregado: {path}").format(path=path), 5000)
            except Exception as e:
                QMessageBox.critical(self, tr("Erro"), tr("Erro ao abrir: {e}").format(e=e))

    def _save_project(self):
        if self._current_file:
            try:
                self.project.save(self._current_file)
                self.statusbar.showMessage(tr("Salvo: {path}").format(path=self._current_file), 5000)
            except Exception as e:
                QMessageBox.critical(self, tr("Erro"), tr("Erro ao salvar: {e}").format(e=e))
        else:
            self._save_project_as()

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Salvar Projeto"),
            f"{self.project.name}.mleco",
            tr("Projeto MultilayerEco (*.mleco);;JSON (*.json)")
        )
        if path:
            try:
                self.project.save(path)
                self._current_file = path
                self.statusbar.showMessage(tr("Salvo: {path}").format(path=path), 5000)
            except Exception as e:
                QMessageBox.critical(self, tr("Erro"), tr("Erro ao salvar: {e}").format(e=e))

    # ─── EXPORT ───

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar Imagem"), "ecossistema.png",
            "PNG (*.png)"
        )
        if path:
            self.view.export_to_image(path)
            self.statusbar.showMessage(tr("Imagem exportada: {path}").format(path=path), 5000)

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar JSON"), f"{self.project.name}.json",
            "JSON (*.json)"
        )
        if path:
            export_json(self.project, path)
            self.statusbar.showMessage(tr("JSON exportado: {path}").format(path=path), 5000)

    def _export_actors_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar Atores CSV"), "atores.csv", "CSV (*.csv)"
        )
        if path:
            export_actors_csv(self.project, path)
            self.statusbar.showMessage(tr("CSV exportado: {path}").format(path=path), 5000)

    def _export_relations_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar Relações CSV"), "relacoes.csv", "CSV (*.csv)"
        )
        if path:
            export_relationships_csv(self.project, path)
            self.statusbar.showMessage(tr("CSV exportado: {path}").format(path=path), 5000)

    def _export_metrics_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar Métricas CSV"), "metricas.csv", "CSV (*.csv)"
        )
        if path:
            export_metrics_csv(self.project, path)
            self.statusbar.showMessage(tr("CSV exportado: {path}").format(path=path), 5000)

    # ─── ZOOM CONTROLS ───

    def _fit_all(self):
        """Fit all content in view and sync slider."""
        self.view.fit_all()
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(0)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText("100%")

    def _on_zoom_slider(self, value: int):
        """Sync zoom slider → view."""
        self.view.set_zoom_level(value)
        pct = int(100 * (self.view.ZOOM_FACTOR ** value))
        self.zoom_label.setText(f"{pct}%")

    def _sync_zoom_slider(self, level: int):
        """Called by view when zoom changes via wheel."""
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(level)
        self.zoom_slider.blockSignals(False)
        pct = int(100 * (self.view.ZOOM_FACTOR ** level))
        self.zoom_label.setText(f"{pct}%")

    # ─── LAYER ISOLATION (2D) ───

    def _refresh_isolate_combo(self):
        """Atualiza o combo de camada isolada, preservando a seleção."""
        if not hasattr(self, "isolate_combo"):
            return
        prev = self.isolate_combo.currentData()
        self.isolate_combo.blockSignals(True)
        self.isolate_combo.clear()
        self.isolate_combo.addItem(tr("Todas as camadas"), None)
        for layer in sorted(self.project.layers, key=lambda l: l.order):
            self.isolate_combo.addItem(tr(layer.name), layer.id)
        idx = 0
        if prev:
            for i in range(self.isolate_combo.count()):
                if self.isolate_combo.itemData(i) == prev:
                    idx = i
                    break
        self.isolate_combo.setCurrentIndex(idx)
        self.isolate_combo.blockSignals(False)
        # Sincroniza a cena sem disparar rebuild extra (o layout faz o rebuild)
        self.scene.isolated_layer_id = self.isolate_combo.currentData() or None

    def _on_isolate_changed(self, index: int):
        layer_id = self.isolate_combo.currentData()
        self.scene.set_isolated_layer(layer_id)
        self._fit_all()

    # ─── COMPARISON ───

    def _open_comparison(self):
        """Abre a janela de comparação de dois ecossistemas lado a lado."""
        self._cmp_win = ComparisonWindow(self.project, self)
        self._cmp_win.setWindowFlag(Qt.Window, True)
        self._cmp_win.show()
        self._cmp_win.raise_()
        self._cmp_win.activateWindow()

    # ─── SNAPSHOTS ("MOMENTOS") ───

    def _save_snapshot(self):
        if not self.project.layers:
            QMessageBox.warning(self, tr("Aviso"),
                                tr("Adicione camadas e atores antes de salvar um momento."))
            return
        default = tr("Momento {n}").format(n=len(self.project.snapshots) + 1)
        name, ok = QInputDialog.getText(
            self, tr("Salvar Momento"),
            tr("Nome do momento (ex.: Antes, Depois, 2023):"), text=default
        )
        if ok and name.strip():
            existed = self.project.get_snapshot_data(name.strip()) is not None
            self.project.add_snapshot(name.strip())
            verb = tr("atualizado") if existed else tr("salvo")
            self.statusbar.showMessage(
                tr("Momento '{name}' {verb}.").format(name=name.strip(), verb=verb), 5000)

    def _manage_snapshots(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("Gerenciar Momentos"))
        dlg.setMinimumWidth(360)
        v = QVBoxLayout(dlg)
        info = QLabel(tr("Momentos salvos neste projeto:"))
        v.addWidget(info)
        lst = QListWidget()
        for n in self.project.list_snapshots():
            lst.addItem(n)
        v.addWidget(lst)
        btns = QHBoxLayout()
        ren = QPushButton(tr("Renomear"))
        rem = QPushButton(tr("Remover"))
        btns.addWidget(ren)
        btns.addWidget(rem)
        btns.addStretch()
        v.addLayout(btns)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        v.addWidget(bb)

        def do_ren():
            it = lst.currentItem()
            if not it:
                return
            new, ok = QInputDialog.getText(dlg, tr("Renomear"), tr("Novo nome:"), text=it.text())
            if ok and new.strip():
                self.project.rename_snapshot(it.text(), new.strip())
                it.setText(new.strip())

        def do_rem():
            it = lst.currentItem()
            if not it:
                return
            self.project.remove_snapshot(it.text())
            lst.takeItem(lst.row(it))

        ren.clicked.connect(do_ren)
        rem.clicked.connect(do_rem)
        bb.rejected.connect(dlg.reject)
        bb.accepted.connect(dlg.accept)
        dlg.exec()

    # ─── SETTINGS ───

    def _show_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            self.settings.update(dlg.get_settings())
            self.scene.use_isometric = self.settings.get("isometric", True)
            self._apply_view_settings()
            self._recalculate_layout()

    def _apply_view_settings(self):
        """Aplica à cena os parâmetros visuais das Configurações e sincroniza
        os controles da barra (fonte e tamanho do nó)."""
        font = self.settings.get("node_font", 11)
        radius = self.settings.get("node_radius", 14)
        layer_font = self.settings.get("layer_font", 14)
        dx = self.settings.get("stair_dx", 380)
        dy = self.settings.get("stair_dy", 300)
        mode = self.settings.get("view_mode", "diagonal")
        # garante separação vertical dos planos no modo vertical
        if mode == "vertical":
            dy = max(dy, 360)
        # sincroniza os controles da barra sem disparar rebuilds repetidos
        for spin, val in ((getattr(self, "font_size_spin", None), font),
                          (getattr(self, "node_size_spin", None), radius),
                          (getattr(self, "layer_font_spin", None), layer_font)):
            if spin is not None:
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        if getattr(self, "view_mode_combo", None) is not None:
            i = self.view_mode_combo.findData(mode)
            if i >= 0:
                self.view_mode_combo.blockSignals(True)
                self.view_mode_combo.setCurrentIndex(i)
                self.view_mode_combo.blockSignals(False)
        from ui.canvas import NodeItem
        NodeItem.FONT_SIZE = max(6, min(int(font), 60))
        NodeItem.RADIUS = max(3, min(int(radius), 48))
        self.scene.layer_font_size = max(8, min(int(layer_font), 48))
        self.scene.stair_dx = max(0, dx)
        self.scene.stair_dy = max(0, dy)
        self.scene.view_mode = mode
        self.scene.rebuild()
        if hasattr(self, "view"):
            self.view.fit_all()


class VersatilityDialog(QDialog):
    """Painel de métricas multiplex: versatilidade, participação e cartografia.

    Mostra, por ator, a versatilidade multinível (Vi), o coeficiente de
    participação de Battiston et al. (2014), o grau de sobreposição (o_i), o
    z-score do grau e a categoria multiplex. Permite escolher o estado
    (projeto atual ou um momento salvo), excluir a camada de Competição do
    cálculo, usar pesos e exportar a tabela em CSV.
    """

    _CAT_COLORS = {
        "focado": "#F38BA8",     # vermelho suave
        "misto": "#F9E2AF",      # amarelo
        "multiplex": "#A6E3A1",  # verde
    }

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(tr("Versatilidade e Participação Multiplex"))
        self.resize(760, 520)

        root = QVBoxLayout(self)

        # ── controles ────────────────────────────────────────────────
        controls = QHBoxLayout()

        controls.addWidget(QLabel(tr("Estado:")))
        self.source_combo = QComboBox()
        self.source_combo.addItem(tr("Projeto atual"))
        for name in self.project.list_snapshots():
            self.source_combo.addItem(tr("Momento: {name}").format(name=name))
        self.source_combo.currentIndexChanged.connect(self._recompute)
        controls.addWidget(self.source_combo)

        # camadas candidatas a exclusão (Competição, grafo completo)
        self._competition_layers = [
            l.name for l in self.project.layers
            if "competi" in l.name.lower()
        ]
        self.exclude_check = QCheckBox(tr("Excluir Competição"))
        self.exclude_check.setToolTip(
            tr("A camada de Competição costuma ser um grafo completo "
               "(densidade 1 por definição) e infla a participação de "
               "todos os labs ao mesmo tempo."))
        self.exclude_check.setEnabled(bool(self._competition_layers))
        self.exclude_check.stateChanged.connect(self._recompute)
        controls.addWidget(self.exclude_check)

        self.weighted_check = QCheckBox(tr("Ponderar por peso"))
        self.weighted_check.setToolTip(
            tr("Usa a soma de pesos das arestas em vez do grau simples."))
        self.weighted_check.stateChanged.connect(self._recompute)
        controls.addWidget(self.weighted_check)

        controls.addStretch()

        self.export_btn = QPushButton(tr("Exportar CSV..."))
        self.export_btn.clicked.connect(self._export_csv)
        controls.addWidget(self.export_btn)

        root.addLayout(controls)

        # ── resumo ───────────────────────────────────────────────────
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color:#A6ADC8; font-size:11px;")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        # ── tabela ───────────────────────────────────────────────────
        self.table = QTableWidget()
        self.headers = [tr("Ator"), tr("Tipo"), "Vi", "Pi",
                        "o_i", "z", tr("# cam."), tr("Categoria")]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, len(self.headers)):
            hh.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        root.addWidget(self.table)

        # ── legenda + fechar ─────────────────────────────────────────
        legend = QLabel(
            tr("Vi: versatilidade multinível.  Pi: participação (0 = papel "
               "concentrado num tipo de relação, 1 = distribuído entre os "
               "tipos).  o_i: grau de sobreposição.  Categoria: faixa de "
               "participação (focado / misto / multiplex) e hub quando z ≥ 1."))
        legend.setStyleSheet("color:#A6ADC8; font-size:10px;")
        legend.setWordWrap(True)
        root.addWidget(legend)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

        self._recompute()

    # ── helpers ──────────────────────────────────────────────────────
    def _current_project(self) -> Project:
        idx = self.source_combo.currentIndex()
        if idx <= 0:
            return self.project
        name = self.project.list_snapshots()[idx - 1]
        proj = self.project.get_snapshot_project(name)
        return proj if proj is not None else self.project

    def _exclude(self):
        return self._competition_layers if self.exclude_check.isChecked() else None

    def _make_engine(self) -> VersatilityEngine:
        return VersatilityEngine(self._current_project())

    def _num_item(self, value, decimals=3) -> QTableWidgetItem:
        item = QTableWidgetItem()
        item.setData(Qt.DisplayRole, round(float(value), decimals))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item

    # ── preenchimento ────────────────────────────────────────────────
    def _recompute(self, *args):
        try:
            engine = self._make_engine()
            exclude = self._exclude()
            weighted = self.weighted_check.isChecked()
            rows = engine.report_rows(exclude=exclude, weighted=weighted)
            densities = engine.density_by_layer(exclude=exclude)
        except Exception as e:
            QMessageBox.critical(self, tr("Erro"),
                                 tr("Erro ao calcular métricas: {e}").format(e=e))
            return

        proj = self._current_project()
        n_layers = len(engine._layer_ids(exclude))
        dens_txt = "  ".join(f"{tr(k)}={v:.3f}" for k, v in densities.items())
        self.summary_label.setText(
            tr("{n} camadas consideradas | {actors} atores | {rels} relações\n"
               "Densidade por camada: {dens}").format(
                n=n_layers, actors=len(proj.actors),
                rels=len(proj.relationships), dens=dens_txt))

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, m in enumerate(rows):
            name_item = QTableWidgetItem(m["name"])
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(tr(m["actor_type"])))
            self.table.setItem(r, 2, self._num_item(m["versatility"]))
            self.table.setItem(r, 3, self._num_item(m["participation"]))
            self.table.setItem(r, 4, self._num_item(m["overlapping_degree"], 1))
            self.table.setItem(r, 5, self._num_item(m["z_overlap"], 2))
            ncam = QTableWidgetItem()
            ncam.setData(Qt.DisplayRole, int(m["n_layers_present"]))
            ncam.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 6, ncam)
            cat_item = QTableWidgetItem(tr_parts(m["category"]))
            papel = m["category"].split("/")[0]
            color = self._CAT_COLORS.get(papel)
            if color:
                cat_item.setForeground(QColor(color))
            if m["category"].endswith("hub"):
                f = cat_item.font()
                f.setBold(True)
                cat_item.setFont(f)
            self.table.setItem(r, 7, cat_item)
        self.table.setSortingEnabled(True)
        self.table.sortItems(2, Qt.DescendingOrder)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar Métricas de Versatilidade"),
            "versatilidade.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            engine = self._make_engine()
            engine.export_csv(path, exclude=self._exclude(),
                              weighted=self.weighted_check.isChecked())
            QMessageBox.information(self, tr("Exportado"),
                                    tr("Métricas salvas em:\n{path}").format(path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("Erro"), tr("Erro ao exportar: {e}").format(e=e))
