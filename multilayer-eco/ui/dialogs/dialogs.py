"""
MultilayerEco - Dialog Windows
Diálogos para entrada manual e configuração.
Tema escuro, layouts claros e organizados.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QDoubleSpinBox,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QTextEdit, QGroupBox, QProgressBar,
    QMessageBox, QDialogButtonBox, QPlainTextEdit,
    QSpinBox, QTabWidget, QWidget, QFrame, QApplication,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from core.models import (
    Project, Actor, Layer, Relationship,
    ACTOR_TYPE_COLORS, RELATION_TYPE_STYLES, LAYER_DEFAULT_COLORS
)
from core.i18n import tr

# ── Shared dark palette helper ────────────────────────────────────────────────
_DARK_DIALOG_STYLE = """
    QDialog {
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    QWidget {
        color: #CDD6F4;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #45475A;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 18px;
        background-color: #2A2A3C;
        color: #89B4FA;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #89B4FA;
    }
    QLabel {
        color: #CDD6F4;
        font-size: 13px;
    }
    QLabel.section-title {
        color: #89B4FA;
        font-weight: bold;
        font-size: 12px;
    }
    QLineEdit, QPlainTextEdit, QTextEdit, QDoubleSpinBox, QSpinBox {
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 4px;
        padding: 6px 8px;
        color: #CDD6F4;
        font-size: 13px;
    }
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
        border-color: #89B4FA;
    }
    QComboBox {
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 4px;
        padding: 6px 8px;
        color: #CDD6F4;
        font-size: 13px;
    }
    QComboBox:hover { border-color: #89B4FA; }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: #313244;
        border: 1px solid #45475A;
        color: #CDD6F4;
        selection-background-color: #89B4FA;
        selection-color: #1E1E2E;
    }
    QCheckBox {
        color: #CDD6F4;
        spacing: 8px;
        font-size: 13px;
    }
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
    QPushButton {
        background-color: #89B4FA;
        color: #1E1E2E;
        border: none;
        border-radius: 4px;
        padding: 7px 16px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover { background-color: #74C7EC; }
    QPushButton:pressed { background-color: #5B9BD5; }
    QPushButton.secondary {
        background-color: #45475A;
        color: #CDD6F4;
    }
    QPushButton.secondary:hover { background-color: #585B70; }
    QPushButton.danger {
        background-color: #F38BA8;
        color: #1E1E2E;
    }
    QPushButton.danger:hover { background-color: #EF6C8C; }
    QListWidget {
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 4px;
        color: #CDD6F4;
        font-size: 13px;
    }
    QListWidget::item { padding: 5px 8px; }
    QListWidget::item:selected {
        background-color: #89B4FA;
        color: #1E1E2E;
    }
    QListWidget::item:hover { background-color: #3B3B50; }
    QProgressBar {
        border: 1px solid #45475A;
        border-radius: 4px;
        text-align: center;
        background-color: #313244;
        color: #CDD6F4;
    }
    QProgressBar::chunk { background-color: #89B4FA; border-radius: 3px; }
    QDialogButtonBox QPushButton { min-width: 80px; }
    QScrollBar:vertical {
        background-color: #1E1E2E; width: 8px; border: none;
    }
    QScrollBar::handle:vertical {
        background-color: #45475A; border-radius: 4px; min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

def _separator(parent=None):
    """Horizontal separator line."""
    line = QFrame(parent)
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color: #45475A; background-color: #45475A;")
    line.setFixedHeight(1)
    return line


# ── Add / Edit Layer ──────────────────────────────────────────────────────────

class AddLayerDialog(QDialog):
    """Dialog to add or edit a layer."""

    def __init__(self, project: Project, layer: Layer = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.layer = layer
        is_edit = layer is not None
        self.setWindowTitle(tr("Editar Camada") if is_edit else tr("Nova Camada"))
        self.setMinimumWidth(420)
        self.setStyleSheet(_DARK_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title
        title = QLabel(tr("✦ Editar Camada") if is_edit else tr("✦ Nova Camada"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)
        root.addWidget(_separator())

        # Name field
        name_lbl = QLabel(tr("Nome da camada *"))
        name_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("Ex: Conhecimento, Infraestrutura, Negócios..."))
        self.name_edit.setMinimumHeight(36)
        root.addWidget(self.name_edit)

        # Color picker
        color_lbl = QLabel(tr("Cor de destaque"))
        color_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(color_lbl)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        self.color_btns = []
        self._selected_color = LAYER_DEFAULT_COLORS[0]

        for i, hex_color in enumerate(LAYER_DEFAULT_COLORS):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_color}; border: 2px solid transparent; "
                f"border-radius: 16px; }} "
                f"QPushButton:hover {{ border-color: white; }}"
            )
            btn.setProperty("hex_color", hex_color)
            btn.clicked.connect(lambda checked=False, c=hex_color, b=btn: self._pick_color(c, b))
            color_row.addWidget(btn)
            self.color_btns.append(btn)

        color_row.addStretch()
        root.addLayout(color_row)

        root.addStretch()
        root.addWidget(_separator())

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancelar"))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 7px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton(tr("Salvar") if is_edit else tr("Adicionar"))
        self.ok_btn.clicked.connect(self._validate_and_accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.ok_btn)
        root.addLayout(btn_row)

        # Pre-fill if editing
        if layer:
            self.name_edit.setText(layer.name)
            self._selected_color = layer.color
            for btn in self.color_btns:
                if btn.property("hex_color") == layer.color:
                    self._mark_selected_btn(btn)
                    break

    def _pick_color(self, hex_color: str, btn: QPushButton):
        self._selected_color = hex_color
        self._mark_selected_btn(btn)

    def _mark_selected_btn(self, selected_btn: QPushButton):
        for btn in self.color_btns:
            c = btn.property("hex_color")
            is_sel = (btn is selected_btn)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {c}; "
                f"border: {'3px solid white' if is_sel else '2px solid transparent'}; "
                f"border-radius: 16px; }}"
                f"QPushButton:hover {{ border-color: white; }}"
            )

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setStyleSheet(
                "background-color: #313244; border: 1px solid #F38BA8; "
                "border-radius: 4px; padding: 6px 8px; color: #CDD6F4;"
            )
            self.name_edit.setPlaceholderText(tr("⚠ Nome obrigatório"))
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "color": self._selected_color,
        }


# ── Add / Edit Actor ──────────────────────────────────────────────────────────

class AddActorDialog(QDialog):
    """Dialog to add or edit an actor, with custom type support."""

    def __init__(self, project: Project, actor: Actor = None,
                 custom_types: list = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.actor = actor
        self._custom_types = custom_types or []
        is_edit = actor is not None
        self.setWindowTitle(tr("Editar Ator") if is_edit else tr("Novo Ator"))
        self.setMinimumWidth(460)
        self.setMinimumHeight(480)
        self.setStyleSheet(_DARK_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Title
        title = QLabel(tr("✦ Editar Ator") if is_edit else tr("✦ Novo Ator"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)
        root.addWidget(_separator())

        # Name
        name_lbl = QLabel(tr("Nome do ator *"))
        name_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("Ex: OpenAI, NYT, Google, Governo EUA..."))
        self.name_edit.setMinimumHeight(36)
        root.addWidget(self.name_edit)

        # Type
        type_lbl = QLabel(tr("Tipo do ator"))
        type_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(type_lbl)

        type_row = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(36)
        self._populate_type_combo()
        type_row.addWidget(self.type_combo, 1)
        root.addLayout(type_row)

        # Layers section
        root.addWidget(_separator())
        layers_lbl = QLabel(tr("Camadas onde este ator aparece"))
        layers_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(layers_lbl)

        self.layer_checks = {}
        layers_widget = QWidget()
        layers_widget.setStyleSheet("background-color: #313244; border-radius: 4px;")
        layers_inner = QVBoxLayout(layers_widget)
        layers_inner.setContentsMargins(10, 8, 10, 8)
        layers_inner.setSpacing(4)

        if project.layers:
            for layer in sorted(project.layers, key=lambda l: l.order):
                cb = QCheckBox(f"  {tr(layer.name)}")
                cb.setProperty("layer_id", layer.id)
                cb.setStyleSheet(
                    f"QCheckBox {{ color: {layer.color}; font-size: 13px; }}"
                    f"QCheckBox::indicator {{ width: 16px; height: 16px; "
                    f"border: 1px solid #45475A; border-radius: 3px; "
                    f"background-color: #1E1E2E; }}"
                    f"QCheckBox::indicator:checked {{ background-color: {layer.color}; "
                    f"border-color: {layer.color}; }}"
                )
                layers_inner.addWidget(cb)
                self.layer_checks[layer.id] = cb
        else:
            no_layers = QLabel(tr("(Nenhuma camada criada ainda)"))
            no_layers.setStyleSheet("color: #585B70; font-style: italic;")
            layers_inner.addWidget(no_layers)

        root.addWidget(layers_widget)
        root.addStretch()
        root.addWidget(_separator())

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancelar"))
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 7px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton(tr("Salvar") if is_edit else tr("Adicionar Ator"))
        self.ok_btn.clicked.connect(self._validate_and_accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.ok_btn)
        root.addLayout(btn_row)

        # Pre-fill if editing
        if actor:
            self.name_edit.setText(actor.name)
            idx = self.type_combo.findData(actor.actor_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            for lid in actor.layers:
                if lid in self.layer_checks:
                    self.layer_checks[lid].setChecked(True)

    def _populate_type_combo(self):
        self.type_combo.clear()
        all_types = list(ACTOR_TYPE_COLORS.keys()) + [
            t for t in self._custom_types if t not in ACTOR_TYPE_COLORS
        ]
        for t in all_types:
            self.type_combo.addItem(tr(t), t)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setStyleSheet(
                "background-color: #313244; border: 1px solid #F38BA8; "
                "border-radius: 4px; padding: 6px 8px; color: #CDD6F4;"
            )
            self.name_edit.setPlaceholderText(tr("⚠ Nome obrigatório"))
            return
        if not any(cb.isChecked() for cb in self.layer_checks.values()):
            QMessageBox.warning(self, tr("Atenção"),
                                tr("Selecione pelo menos uma camada para o ator."))
            return
        self.accept()

    def get_data(self):
        layers = [lid for lid, cb in self.layer_checks.items() if cb.isChecked()]
        return {
            "name": self.name_edit.text().strip(),
            "actor_type": self.type_combo.currentData() or self.type_combo.currentText(),
            "layers": layers,
        }


# ── Actor Type Manager ────────────────────────────────────────────────────────

class ActorTypeManagerDialog(QDialog):
    """Dialog to manage custom actor types."""

    def __init__(self, custom_types: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Gerenciar Tipos de Ator"))
        self.setMinimumWidth(420)
        self.setMinimumHeight(460)
        self.setStyleSheet(_DARK_DIALOG_STYLE)
        self._custom_types = list(custom_types)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel(tr("✦ Tipos de Ator"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)

        info = QLabel(tr("Tipos padrão (não removíveis) + seus tipos personalizados:"))
        info.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        root.addWidget(info)
        root.addWidget(_separator())

        # Built-in types (read-only display)
        builtin_lbl = QLabel(tr("Tipos embutidos"))
        builtin_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(builtin_lbl)

        builtin_widget = QWidget()
        builtin_widget.setStyleSheet("background-color: #2A2A3C; border-radius: 4px;")
        builtin_inner = QHBoxLayout(builtin_widget)
        builtin_inner.setContentsMargins(10, 8, 10, 8)
        builtin_inner.setSpacing(6)

        for t, color in ACTOR_TYPE_COLORS.items():
            badge = QLabel(tr(t))
            badge.setStyleSheet(
                f"color: {color}; background-color: #1E1E2E; "
                f"border: 1px solid {color}; border-radius: 10px; "
                f"padding: 2px 8px; font-size: 11px;"
            )
            builtin_inner.addWidget(badge)
        builtin_inner.addStretch()
        root.addWidget(builtin_widget)

        root.addSpacing(8)

        # Custom types list
        custom_lbl = QLabel(tr("Tipos personalizados"))
        custom_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(custom_lbl)

        self.types_list = QListWidget()
        self.types_list.setMinimumHeight(140)
        for t in self._custom_types:
            self.types_list.addItem(t)
        root.addWidget(self.types_list)

        # Add new type
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self.new_type_edit = QLineEdit()
        self.new_type_edit.setPlaceholderText(tr("Novo tipo (ex: Investidor, Parceiro...)"))
        self.new_type_edit.setMinimumHeight(34)
        self.new_type_edit.returnPressed.connect(self._add_type)

        add_btn = QPushButton(tr("+ Adicionar"))
        add_btn.setFixedHeight(34)
        add_btn.clicked.connect(self._add_type)

        add_row.addWidget(self.new_type_edit, 1)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        rem_btn = QPushButton(tr("✕ Remover selecionado"))
        rem_btn.setStyleSheet(
            "QPushButton { background-color: #F38BA8; color: #1E1E2E; "
            "border-radius: 4px; padding: 6px 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #EF6C8C; }"
        )
        rem_btn.clicked.connect(self._remove_type)
        root.addWidget(rem_btn)

        root.addStretch()
        root.addWidget(_separator())

        btn_row = QHBoxLayout()
        close_btn = QPushButton(tr("Fechar"))
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _add_type(self):
        t = self.new_type_edit.text().strip()
        if not t:
            return
        if t in ACTOR_TYPE_COLORS or t in self._custom_types:
            QMessageBox.information(self, tr("Aviso"), tr("O tipo '{t}' já existe.").format(t=t))
            return
        self._custom_types.append(t)
        self.types_list.addItem(t)
        self.new_type_edit.clear()

    def _remove_type(self):
        row = self.types_list.currentRow()
        if row < 0:
            return
        t = self.types_list.item(row).text()
        self._custom_types.remove(t)
        self.types_list.takeItem(row)

    def get_custom_types(self):
        return list(self._custom_types)


# ── Add / Edit Relationship ───────────────────────────────────────────────────

class AddRelationDialog(QDialog):
    """Dialog to add or edit a relationship — clear two-section layout."""

    def __init__(self, project: Project, rel: Relationship = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.rel = rel
        is_edit = rel is not None
        self.setWindowTitle(tr("Editar Relação") if is_edit else tr("Nova Relação"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(560)
        self.setStyleSheet(_DARK_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Title
        title = QLabel(tr("✦ Editar Relação") if is_edit else tr("✦ Nova Relação"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)
        root.addWidget(_separator())

        # ── Section 1: Actors ──
        actors_lbl = QLabel(tr("ATORES"))
        actors_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(actors_lbl)

        actors_grid = QHBoxLayout()
        actors_grid.setSpacing(12)

        src_col = QVBoxLayout()
        src_col.setSpacing(4)
        src_col.addWidget(self._field_label(tr("Origem")))
        self.source_combo = QComboBox()
        self.source_combo.setMinimumHeight(36)
        for actor in sorted(project.actors.values(), key=lambda a: a.name):
            self.source_combo.addItem(actor.name, actor.id)
        src_col.addWidget(self.source_combo)

        arrow_lbl = QLabel("→")
        arrow_lbl.setStyleSheet("color: #89B4FA; font-size: 20px; font-weight: bold;")
        arrow_lbl.setAlignment(Qt.AlignCenter)
        arrow_lbl.setFixedWidth(24)

        tgt_col = QVBoxLayout()
        tgt_col.setSpacing(4)
        tgt_col.addWidget(self._field_label(tr("Destino")))
        self.target_combo = QComboBox()
        self.target_combo.setMinimumHeight(36)
        for actor in sorted(project.actors.values(), key=lambda a: a.name):
            self.target_combo.addItem(actor.name, actor.id)
        tgt_col.addWidget(self.target_combo)

        actors_grid.addLayout(src_col, 1)
        actors_grid.addWidget(arrow_lbl)
        actors_grid.addLayout(tgt_col, 1)
        root.addLayout(actors_grid)

        root.addWidget(_separator())

        # ── Section 2: Layer ──
        layer_lbl = QLabel(tr("CAMADA"))
        layer_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(layer_lbl)

        self.is_inter_check = QCheckBox(
            tr("Relação inter-camada  (conecta atores de camadas diferentes)")
        )
        self.is_inter_check.toggled.connect(self._toggle_inter_layer)
        root.addWidget(self.is_inter_check)

        # Intra-layer (single layer)
        self.intra_widget = QWidget()
        intra_layout = QHBoxLayout(self.intra_widget)
        intra_layout.setContentsMargins(0, 0, 0, 0)
        intra_layout.setSpacing(8)
        intra_layout.addWidget(self._field_label(tr("Camada:")))
        self.layer_combo = QComboBox()
        self.layer_combo.setMinimumHeight(34)
        for layer in project.layers:
            self.layer_combo.addItem(tr(layer.name), layer.id)
        intra_layout.addWidget(self.layer_combo, 1)
        root.addWidget(self.intra_widget)

        # Inter-layer (two layers)
        self.inter_widget = QWidget()
        inter_layout = QHBoxLayout(self.inter_widget)
        inter_layout.setContentsMargins(0, 0, 0, 0)
        inter_layout.setSpacing(8)

        src_layer_col = QVBoxLayout()
        src_layer_col.addWidget(self._field_label(tr("Camada Origem")))
        self.src_layer_combo = QComboBox()
        self.src_layer_combo.setMinimumHeight(34)
        for layer in project.layers:
            self.src_layer_combo.addItem(tr(layer.name), layer.id)
        src_layer_col.addWidget(self.src_layer_combo)

        inter_arrow = QLabel("→")
        inter_arrow.setStyleSheet("color: #89B4FA; font-size: 18px;")
        inter_arrow.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        inter_arrow.setFixedWidth(24)

        tgt_layer_col = QVBoxLayout()
        tgt_layer_col.addWidget(self._field_label(tr("Camada Destino")))
        self.tgt_layer_combo = QComboBox()
        self.tgt_layer_combo.setMinimumHeight(34)
        for layer in project.layers:
            self.tgt_layer_combo.addItem(tr(layer.name), layer.id)
        tgt_layer_col.addWidget(self.tgt_layer_combo)

        inter_layout.addLayout(src_layer_col, 1)
        inter_layout.addWidget(inter_arrow)
        inter_layout.addLayout(tgt_layer_col, 1)

        self.inter_widget.setVisible(False)
        root.addWidget(self.inter_widget)

        root.addWidget(_separator())

        # ── Section 3: Attributes ──
        attr_lbl = QLabel(tr("PROPRIEDADES"))
        attr_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(attr_lbl)

        attr_row1 = QHBoxLayout()
        attr_row1.setSpacing(12)

        type_col = QVBoxLayout()
        type_col.setSpacing(4)
        type_col.addWidget(self._field_label(tr("Tipo")))
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(34)
        for rt in RELATION_TYPE_STYLES.keys():
            self.type_combo.addItem(tr(rt), rt)
        type_col.addWidget(self.type_combo)

        dir_col = QVBoxLayout()
        dir_col.setSpacing(4)
        dir_col.addWidget(self._field_label(tr("Direção")))
        self.dir_combo = QComboBox()
        self.dir_combo.setMinimumHeight(34)
        self.dir_combo.addItem(tr("↔ Bidirecional"), "bidirectional")
        self.dir_combo.addItem(tr("→ Origem→Destino"), "source_to_target")
        self.dir_combo.addItem(tr("← Destino→Origem"), "target_to_source")
        dir_col.addWidget(self.dir_combo)

        attr_row1.addLayout(type_col, 1)
        attr_row1.addLayout(dir_col, 1)
        root.addLayout(attr_row1)

        attr_row2 = QHBoxLayout()
        attr_row2.setSpacing(12)

        lbl_col = QVBoxLayout()
        lbl_col.setSpacing(4)
        lbl_col.addWidget(self._field_label(tr("Rótulo (opcional)")))
        self.label_edit = QLineEdit()
        self.label_edit.setMinimumHeight(34)
        self.label_edit.setPlaceholderText(tr("Breve descrição da relação"))
        lbl_col.addWidget(self.label_edit)

        weight_col = QVBoxLayout()
        weight_col.setSpacing(4)
        weight_col.addWidget(self._field_label(tr("Peso")))
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setMinimumHeight(34)
        self.weight_spin.setRange(0.1, 5.0)
        self.weight_spin.setValue(1.0)
        self.weight_spin.setSingleStep(0.1)
        weight_col.addWidget(self.weight_spin)

        attr_row2.addLayout(lbl_col, 2)
        attr_row2.addLayout(weight_col, 1)
        root.addLayout(attr_row2)

        root.addStretch()
        root.addWidget(_separator())

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancelar"))
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 7px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton(tr("Salvar") if is_edit else tr("Adicionar Relação"))
        self.ok_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.ok_btn)
        root.addLayout(btn_row)

        # Pre-fill if editing
        if rel:
            src_idx = self.source_combo.findData(rel.source_id)
            if src_idx >= 0: self.source_combo.setCurrentIndex(src_idx)
            tgt_idx = self.target_combo.findData(rel.target_id)
            if tgt_idx >= 0: self.target_combo.setCurrentIndex(tgt_idx)
            if rel.is_inter_layer:
                self.is_inter_check.setChecked(True)
                sl_idx = self.src_layer_combo.findData(rel.source_layer_id)
                if sl_idx >= 0: self.src_layer_combo.setCurrentIndex(sl_idx)
                tl_idx = self.tgt_layer_combo.findData(rel.target_layer_id)
                if tl_idx >= 0: self.tgt_layer_combo.setCurrentIndex(tl_idx)
            else:
                l_idx = self.layer_combo.findData(rel.layer_id)
                if l_idx >= 0: self.layer_combo.setCurrentIndex(l_idx)
            rt_idx = self.type_combo.findData(rel.rel_type)
            if rt_idx >= 0: self.type_combo.setCurrentIndex(rt_idx)
            d_idx = self.dir_combo.findData(rel.direction)
            if d_idx >= 0: self.dir_combo.setCurrentIndex(d_idx)
            self.label_edit.setText(rel.label)
            self.weight_spin.setValue(rel.weight)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        return lbl

    def _toggle_inter_layer(self, checked: bool):
        self.intra_widget.setVisible(not checked)
        self.inter_widget.setVisible(checked)

    def get_data(self):
        data = {
            "source_id": self.source_combo.currentData(),
            "target_id": self.target_combo.currentData(),
            "rel_type": self.type_combo.currentData() or self.type_combo.currentText(),
            "direction": self.dir_combo.currentData(),
            "label": self.label_edit.text().strip(),
            "weight": self.weight_spin.value(),
        }
        if self.is_inter_check.isChecked():
            data["layer_id"] = ""
            data["source_layer_id"] = self.src_layer_combo.currentData()
            data["target_layer_id"] = self.tgt_layer_combo.currentData()
        else:
            data["layer_id"] = self.layer_combo.currentData()
            data["source_layer_id"] = ""
            data["target_layer_id"] = ""
        return data


# ── LLM Extraction ────────────────────────────────────────────────────────────

class ExtractionDialog(QDialog):
    """Dialog to configure and run LLM extraction (Claude, OpenAI, Gemini, local)."""

    extraction_done = Signal(dict)

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(tr("Extração Automatizada via LLM"))
        self.setMinimumWidth(620)
        self.setMinimumHeight(580)
        self.setStyleSheet(_DARK_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel(tr("✦ Extrair Ecossistema de Documento"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)
        root.addWidget(_separator())

        # ── File selection ──
        file_lbl = QLabel(tr("Documento de origem *"))
        file_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(file_lbl)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText(tr("Selecione um arquivo PDF, DOCX ou TXT..."))
        self.file_edit.setMinimumHeight(36)
        self.file_edit.setReadOnly(True)
        file_btn = QPushButton(tr("Selecionar..."))
        file_btn.setFixedHeight(36)
        file_btn.clicked.connect(self._select_file)
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(file_btn)
        root.addLayout(file_row)

        root.addWidget(_separator())

        # ── API / Model ──
        api_lbl = QLabel(tr("PROVEDOR DE IA"))
        api_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(api_lbl)

        # Provider selector (as tab-style buttons)
        provider_row = QHBoxLayout()
        provider_row.setSpacing(6)
        self._provider_btns = {}
        providers = [
            ("anthropic", "Anthropic Claude"),
            ("openai",    "OpenAI GPT"),
            ("gemini",    "Google Gemini"),
            ("local",     "SLM Local (Ollama)"),
        ]
        for pid, plabel in providers:
            btn = QPushButton(plabel)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, p=pid: self._select_provider(p))
            provider_row.addWidget(btn)
            self._provider_btns[pid] = btn
        root.addLayout(provider_row)

        # Stack for provider-specific fields
        self._provider_stack = {}

        # Anthropic fields
        ant_w = QWidget()
        ant_l = QHBoxLayout(ant_w)
        ant_l.setContentsMargins(0, 0, 0, 0)
        ant_l.setSpacing(8)
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.Password)
        self.anthropic_key.setPlaceholderText("API Key: sk-ant-...")
        self.anthropic_key.setMinimumHeight(34)
        self.anthropic_key.setText(os.environ.get("ANTHROPIC_API_KEY", ""))
        self.anthropic_model = QLineEdit("claude-sonnet-4-20250514")
        self.anthropic_model.setMinimumHeight(34)
        self.anthropic_model.setFixedWidth(220)
        ant_l.addWidget(self.anthropic_key, 1)
        ant_l.addWidget(self.anthropic_model)
        self._provider_stack["anthropic"] = ant_w
        root.addWidget(ant_w)

        # OpenAI fields
        oai_w = QWidget()
        oai_l = QHBoxLayout(oai_w)
        oai_l.setContentsMargins(0, 0, 0, 0)
        oai_l.setSpacing(8)
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.Password)
        self.openai_key.setPlaceholderText("API Key: sk-...")
        self.openai_key.setMinimumHeight(34)
        self.openai_key.setText(os.environ.get("OPENAI_API_KEY", ""))
        self.openai_model = QLineEdit("gpt-4o")
        self.openai_model.setMinimumHeight(34)
        self.openai_model.setFixedWidth(160)
        oai_l.addWidget(self.openai_key, 1)
        oai_l.addWidget(self.openai_model)
        oai_w.setVisible(False)
        self._provider_stack["openai"] = oai_w
        root.addWidget(oai_w)

        # Gemini fields
        gem_w = QWidget()
        gem_l = QHBoxLayout(gem_w)
        gem_l.setContentsMargins(0, 0, 0, 0)
        gem_l.setSpacing(8)
        self.gemini_key = QLineEdit()
        self.gemini_key.setEchoMode(QLineEdit.Password)
        self.gemini_key.setPlaceholderText("API Key: AIza...")
        self.gemini_key.setMinimumHeight(34)
        self.gemini_key.setText(os.environ.get("GOOGLE_API_KEY", ""))
        self.gemini_model = QLineEdit("gemini-2.0-flash")
        self.gemini_model.setMinimumHeight(34)
        self.gemini_model.setFixedWidth(200)
        gem_l.addWidget(self.gemini_key, 1)
        gem_l.addWidget(self.gemini_model)
        gem_w.setVisible(False)
        self._provider_stack["gemini"] = gem_w
        root.addWidget(gem_w)

        # Local / Ollama fields
        loc_w = QWidget()
        loc_l = QHBoxLayout(loc_w)
        loc_l.setContentsMargins(0, 0, 0, 0)
        loc_l.setSpacing(8)
        url_lbl = QLabel("URL:")
        url_lbl.setStyleSheet("color: #A6ADC8; font-size: 12px;")
        url_lbl.setFixedWidth(30)
        self.local_url = QLineEdit("http://localhost:11434")
        self.local_url.setMinimumHeight(34)
        model_lbl = QLabel(tr("Modelo:"))
        model_lbl.setStyleSheet("color: #A6ADC8; font-size: 12px;")
        self.local_model = QLineEdit("gemma3")
        self.local_model.setMinimumHeight(34)
        self.local_model.setFixedWidth(130)
        loc_l.addWidget(url_lbl)
        loc_l.addWidget(self.local_url, 1)
        loc_l.addWidget(model_lbl)
        loc_l.addWidget(self.local_model)
        loc_w.setVisible(False)
        self._provider_stack["local"] = loc_w
        root.addWidget(loc_w)

        self._current_provider = "anthropic"
        self._select_provider("anthropic")

        root.addWidget(_separator())

        # ── Layers ──
        layers_lbl = QLabel(tr("Camadas a extrair (uma por linha)"))
        layers_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(layers_lbl)

        self.layers_edit = QPlainTextEdit()
        self.layers_edit.setMaximumHeight(72)
        existing = "\n".join(l.name for l in project.layers) if project.layers else \
                   "\n".join([tr("Conhecimento"), tr("Infraestrutura"), tr("Negócios")])
        self.layers_edit.setPlainText(existing)
        root.addWidget(self.layers_edit)

        # ── Context ──
        ctx_lbl = QLabel(tr("Contexto adicional (opcional)"))
        ctx_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold;")
        root.addWidget(ctx_lbl)

        self.context_edit = QPlainTextEdit()
        self.context_edit.setMaximumHeight(52)
        self.context_edit.setPlaceholderText(
            tr("Ex: Foque em relações de dependência tecnológica entre empresas de IA...")
        )
        root.addWidget(self.context_edit)

        # ── Progress ──
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #A6ADC8; font-size: 11px; font-style: italic;")
        root.addWidget(self.status_label)

        root.addWidget(_separator())

        # ── Buttons ──
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancelar"))
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 7px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        cancel_btn.clicked.connect(self.reject)

        self.extract_btn = QPushButton(tr("⚡ Extrair Ecossistema"))
        self.extract_btn.clicked.connect(self._run_extraction)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.extract_btn)
        root.addLayout(btn_row)

        self._extraction_result = None

    def _select_provider(self, provider: str):
        self._current_provider = provider
        for pid, w in self._provider_stack.items():
            w.setVisible(pid == provider)
        # Style provider buttons
        _active = (
            "QPushButton { background-color: #89B4FA; color: #1E1E2E; "
            "border-radius: 4px; padding: 5px 10px; font-weight: bold; }"
        )
        _inactive = (
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        for pid, btn in self._provider_btns.items():
            btn.setStyleSheet(_active if pid == provider else _inactive)
            btn.setChecked(pid == provider)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Selecionar Documento"),
            "", tr("Documentos (*.pdf *.docx *.txt *.md)")
        )
        if path:
            self.file_edit.setText(path)

    def _run_extraction(self):
        filepath = self.file_edit.text().strip()
        provider = self._current_provider

        # Validate credentials
        if provider == "anthropic":
            api_key = self.anthropic_key.text().strip()
            model = self.anthropic_model.text().strip()
            if not api_key:
                QMessageBox.warning(self, tr("Erro"), tr("Insira a API Key da Anthropic."))
                return
        elif provider == "openai":
            api_key = self.openai_key.text().strip()
            model = self.openai_model.text().strip()
            if not api_key:
                QMessageBox.warning(self, tr("Erro"), tr("Insira a API Key da OpenAI."))
                return
        elif provider == "gemini":
            api_key = self.gemini_key.text().strip()
            model = self.gemini_model.text().strip()
            if not api_key:
                QMessageBox.warning(self, tr("Erro"), tr("Insira a API Key do Google Gemini."))
                return
        else:  # local
            api_key = ""
            model = self.local_model.text().strip()

        if not filepath:
            QMessageBox.warning(self, tr("Erro"), tr("Selecione um documento."))
            return

        layer_names = [l.strip() for l in self.layers_edit.toPlainText().split("\n") if l.strip()]
        if not layer_names:
            QMessageBox.warning(self, tr("Erro"), tr("Defina pelo menos uma camada."))
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText(tr("Lendo documento..."))
        self.extract_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            from extraction.llm_extractor import read_document
            text = read_document(filepath)
            self.status_label.setText(
                tr("Documento lido ({n} chars). Enviando ao {provider}...").format(
                    n=len(text), provider=provider)
            )
            QApplication.processEvents()

            context = self.context_edit.toPlainText().strip()

            if provider == "anthropic":
                from extraction.llm_extractor import extract_with_anthropic
                result = extract_with_anthropic(text, layer_names, api_key, model, context=context)
            elif provider == "openai":
                from extraction.llm_extractor import extract_with_openai
                result = extract_with_openai(text, layer_names, api_key, model, context=context)
            elif provider == "gemini":
                from extraction.llm_extractor import extract_with_gemini
                result = extract_with_gemini(text, layer_names, api_key, model, context=context)
            else:
                from extraction.llm_extractor import extract_with_local
                result = extract_with_local(
                    text, layer_names, model,
                    base_url=self.local_url.text().strip(),
                    context=context
                )

            self._extraction_result = result
            self._extraction_layer_names = layer_names

            n_actors = len(result.get("actors", []))
            n_intra  = len(result.get("intra_layer_relations", []))
            n_inter  = len(result.get("inter_layer_relations", []))

            self.status_label.setText(
                tr("✓ Concluído: {actors} atores, {intra} relações intra, "
                   "{inter} relações inter-camada").format(
                    actors=n_actors, intra=n_intra, inter=n_inter)
            )
            self.progress.setRange(0, 100)
            self.progress.setValue(100)

            reply = QMessageBox.question(
                self, tr("Extração Concluída"),
                tr("Resultados encontrados:\n• {actors} atores\n"
                   "• {intra} relações intra-camada\n"
                   "• {inter} relações inter-camada\n\n"
                   "Deseja aplicar ao projeto?").format(
                    actors=n_actors, intra=n_intra, inter=n_inter),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.extraction_done.emit(result)
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, tr("Erro na Extração"), str(e))
            self.progress.setVisible(False)
            self.status_label.setText(tr("Erro: {msg}").format(msg=str(e)[:120]))

        self.extract_btn.setEnabled(True)

    def get_result(self):
        return self._extraction_result, getattr(self, '_extraction_layer_names', [])


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.setWindowTitle(tr("Configurações"))
        self.setMinimumWidth(460)
        self.setStyleSheet(_DARK_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel(tr("✦ Configurações"))
        title.setStyleSheet("color: #89B4FA; font-size: 16px; font-weight: bold;")
        root.addWidget(title)
        root.addWidget(_separator())

        # API Keys section
        api_lbl = QLabel(tr("CHAVES DE API"))
        api_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(api_lbl)

        for field_name, key, placeholder in [
            ("Anthropic (Claude)", "api_key", "sk-ant-..."),
            ("OpenAI (GPT)",        "openai_api_key", "sk-..."),
            ("Google Gemini",       "gemini_api_key", "AIza..."),
        ]:
            lbl = QLabel(field_name)
            lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
            root.addWidget(lbl)
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(placeholder)
            edit.setText(settings.get(key, ""))
            edit.setMinimumHeight(34)
            setattr(self, f"_{key}_edit", edit)
            root.addWidget(edit)

        root.addWidget(_separator())

        # Layout
        layout_lbl = QLabel(tr("VISUALIZAÇÃO"))
        layout_lbl.setStyleSheet(
            "color: #89B4FA; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(layout_lbl)

        lbl2 = QLabel(tr("Algoritmo de Layout"))
        lbl2.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        root.addWidget(lbl2)

        self.layout_combo = QComboBox()
        self.layout_combo.setMinimumHeight(34)
        for alg in ["spring", "circular", "spectral", "kamada_kawai", "shell"]:
            self.layout_combo.addItem(alg)
        current = settings.get("layout_algorithm", "spring")
        idx = self.layout_combo.findText(current)
        if idx >= 0:
            self.layout_combo.setCurrentIndex(idx)
        root.addWidget(self.layout_combo)

        self.iso_check = QCheckBox(tr("Usar visualização isométrica (experimental)"))
        self.iso_check.setChecked(settings.get("isometric", True))
        root.addWidget(self.iso_check)

        arr_lbl = QLabel(tr("Modo de visualização das camadas"))
        arr_lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        root.addWidget(arr_lbl)
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.setMinimumHeight(34)
        self._view_modes = [
            (tr("Diagonal (cascata)"), "diagonal"),
            (tr("Vertical (mesmo eixo)"), "vertical"),
            (tr("Matriz (grade)"), "matrix"),
            (tr("Plano agregado (1 plano)"), "flat"),
        ]
        for rotulo, val in self._view_modes:
            self.view_mode_combo.addItem(rotulo, val)
        cur_mode = settings.get("view_mode", "diagonal")
        idx = next((i for i, (_r, v) in enumerate(self._view_modes)
                    if v == cur_mode), 0)
        self.view_mode_combo.setCurrentIndex(idx)
        root.addWidget(self.view_mode_combo)

        def _spin_row(rotulo, lo, hi, val, suffix=""):
            lbl = QLabel(rotulo)
            lbl.setStyleSheet("color: #A6ADC8; font-size: 11px;")
            root.addWidget(lbl)
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setValue(int(val))
            if suffix:
                sp.setSuffix(suffix)
            sp.setMinimumHeight(30)
            root.addWidget(sp)
            return sp

        self.layer_font_spin = _spin_row(
            tr("Tamanho da fonte do nome das camadas"), 8, 48,
            settings.get("layer_font", 14), " pt")
        self.node_font_spin = _spin_row(
            tr("Tamanho da fonte dos atores"), 6, 60,
            settings.get("node_font", 11), " pt")
        self.node_radius_spin = _spin_row(
            tr("Tamanho do nó (raio)"), 3, 48,
            settings.get("node_radius", 14), " px")
        self.stair_dx_spin = _spin_row(
            tr("Passo diagonal horizontal (entre camadas)"), 0, 1200,
            settings.get("stair_dx", 380), " px")
        self.stair_dy_spin = _spin_row(
            tr("Passo diagonal vertical (entre camadas)"), 0, 1200,
            settings.get("stair_dy", 300), " px")

        root.addStretch()
        root.addWidget(_separator())

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancelar"))
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #45475A; color: #CDD6F4; "
            "border-radius: 4px; padding: 7px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #585B70; }"
        )
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton(tr("Salvar Configurações"))
        ok_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    def get_settings(self):
        return {
            "api_key":          self._api_key_edit.text(),
            "openai_api_key":   self._openai_api_key_edit.text(),
            "gemini_api_key":   self._gemini_api_key_edit.text(),
            "layout_algorithm": self.layout_combo.currentText(),
            "isometric":        self.iso_check.isChecked(),
            "view_mode":        self.view_mode_combo.currentData(),
            "layer_font":       self.layer_font_spin.value(),
            "node_font":        self.node_font_spin.value(),
            "node_radius":      self.node_radius_spin.value(),
            "stair_dx":         self.stair_dx_spin.value(),
            "stair_dy":         self.stair_dy_spin.value(),
        }
