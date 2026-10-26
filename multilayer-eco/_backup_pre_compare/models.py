"""
MultilayerEco - Core Data Models
Modelos de dados para ecossistemas de negócios multiníveis.
"""
import json
import gzip
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Actor:
    """Um ator no ecossistema (empresa, governo, tecnologia, etc.)"""
    id: str = ""
    name: str = ""
    actor_type: str = "Empresa"  # Empresa, Governo, ONG, Tecnologia, Regulador, Plataforma
    color: str = ""  # hex color, empty = use type default
    layers: list = field(default_factory=list)  # layer IDs where this actor appears
    attributes: dict = field(default_factory=dict)
    # Position per layer: {layer_id: (x, y)}
    positions: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


ACTOR_TYPE_COLORS = {
    "Empresa": "#4A90D9",
    "Governo": "#D94A4A",
    "ONG": "#4AD98A",
    "Tecnologia": "#D9A04A",
    "Regulador": "#9B59B6",
    "Plataforma": "#1ABC9C",
    "Mídia": "#E67E22",
    "Academia": "#3498DB",
    "Outro": "#95A5A6",
}

RELATION_TYPE_STYLES = {
    "cooperação": {"color": "#27AE60", "style": "solid", "width": 2},
    "competição": {"color": "#E74C3C", "style": "dash", "width": 2},
    "dependência": {"color": "#F39C12", "style": "solid", "width": 2},
    "fornecimento": {"color": "#3498DB", "style": "solid", "width": 2},
    "extração": {"color": "#E74C3C", "style": "solid", "width": 3},
    "regulação": {"color": "#9B59B6", "style": "dot", "width": 2},
    "investimento": {"color": "#2ECC71", "style": "solid", "width": 3},
    "conflito": {"color": "#C0392B", "style": "dash", "width": 3},
    "integração": {"color": "#16A085", "style": "solid", "width": 2},
    "outro": {"color": "#7F8C8D", "style": "solid", "width": 1},
}


@dataclass
class Relationship:
    """Uma relação entre dois atores."""
    id: str = ""
    source_id: str = ""  # Actor ID
    target_id: str = ""  # Actor ID
    layer_id: str = ""   # Layer where this relation occurs ("" = inter-layer)
    rel_type: str = "cooperação"
    direction: str = "bidirectional"  # bidirectional, source_to_target, target_to_source
    weight: float = 1.0
    label: str = ""
    attributes: dict = field(default_factory=dict)
    # For inter-layer relations
    source_layer_id: str = ""
    target_layer_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def is_inter_layer(self) -> bool:
        return self.layer_id == "" and self.source_layer_id and self.target_layer_id


@dataclass
class Layer:
    """Uma camada do ecossistema multinível."""
    id: str = ""
    name: str = ""
    color: str = "#4A90D9"  # background color (with transparency)
    order: int = 0  # vertical position (0 = bottom)
    visible: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


LAYER_DEFAULT_COLORS = [
    "#E74C3C",  # Red
    "#27AE60",  # Green
    "#3498DB",  # Blue
    "#F39C12",  # Orange
    "#9B59B6",  # Purple
    "#1ABC9C",  # Teal
    "#E67E22",  # Dark Orange
    "#2C3E50",  # Dark Blue
]


@dataclass
class Project:
    """Um projeto completo de ecossistema multinível."""
    name: str = "Novo Projeto"
    description: str = ""
    layers: list = field(default_factory=list)    # List[Layer]
    actors: dict = field(default_factory=dict)     # {actor_id: Actor}
    relationships: list = field(default_factory=list)  # List[Relationship]
    settings: dict = field(default_factory=dict)

    def add_layer(self, name: str, color: str = "") -> Layer:
        order = len(self.layers)
        if not color:
            color = LAYER_DEFAULT_COLORS[order % len(LAYER_DEFAULT_COLORS)]
        layer = Layer(name=name, color=color, order=order)
        self.layers.append(layer)
        return layer

    def remove_layer(self, layer_id: str):
        self.layers = [l for l in self.layers if l.id != layer_id]
        # Remove actors that were only in this layer
        to_remove = []
        for aid, actor in self.actors.items():
            actor.layers = [lid for lid in actor.layers if lid != layer_id]
            if not actor.layers:
                to_remove.append(aid)
        for aid in to_remove:
            del self.actors[aid]
        # Remove relationships in this layer
        self.relationships = [
            r for r in self.relationships
            if r.layer_id != layer_id
            and r.source_layer_id != layer_id
            and r.target_layer_id != layer_id
        ]
        # Reorder remaining layers
        for i, layer in enumerate(sorted(self.layers, key=lambda l: l.order)):
            layer.order = i

    def add_actor(self, name: str, actor_type: str = "Empresa",
                  layer_ids: list = None) -> Actor:
        actor = Actor(name=name, actor_type=actor_type,
                      layers=layer_ids or [])
        self.actors[actor.id] = actor
        return actor

    def find_actor_by_name(self, name: str) -> Optional[Actor]:
        for actor in self.actors.values():
            if actor.name.lower().strip() == name.lower().strip():
                return actor
        return None

    def remove_actor(self, actor_id: str):
        if actor_id in self.actors:
            del self.actors[actor_id]
        self.relationships = [
            r for r in self.relationships
            if r.source_id != actor_id and r.target_id != actor_id
        ]

    def add_relationship(self, source_id: str, target_id: str,
                         layer_id: str = "", rel_type: str = "cooperação",
                         direction: str = "bidirectional", label: str = "",
                         source_layer_id: str = "", target_layer_id: str = "",
                         weight: float = 1.0) -> Relationship:
        rel = Relationship(
            source_id=source_id, target_id=target_id,
            layer_id=layer_id, rel_type=rel_type,
            direction=direction, label=label,
            source_layer_id=source_layer_id,
            target_layer_id=target_layer_id,
            weight=weight
        )
        self.relationships.append(rel)
        return rel

    def remove_relationship(self, rel_id: str):
        self.relationships = [r for r in self.relationships if r.id != rel_id]

    def get_layer_by_id(self, layer_id: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def get_layer_by_name(self, name: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.name.lower().strip() == name.lower().strip():
                return layer
        return None

    def get_actors_in_layer(self, layer_id: str) -> list:
        return [a for a in self.actors.values() if layer_id in a.layers]

    def get_relationships_in_layer(self, layer_id: str) -> list:
        return [r for r in self.relationships if r.layer_id == layer_id]

    def get_inter_layer_relationships(self) -> list:
        return [r for r in self.relationships if r.is_inter_layer]

    def get_actor_relationships(self, actor_id: str) -> list:
        return [r for r in self.relationships
                if r.source_id == actor_id or r.target_id == actor_id]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "layers": [asdict(l) for l in self.layers],
            "actors": {aid: asdict(a) for aid, a in self.actors.items()},
            "relationships": [asdict(r) for r in self.relationships],
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        project = cls()
        project.name = data.get("name", "")
        project.description = data.get("description", "")
        project.layers = [Layer(**ld) for ld in data.get("layers", [])]
        project.actors = {
            aid: Actor(**ad)
            for aid, ad in data.get("actors", {}).items()
        }
        project.relationships = [
            Relationship(**rd) for rd in data.get("relationships", [])
        ]
        project.settings = data.get("settings", {})
        return project

    def save(self, filepath: str):
        data = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        if filepath.endswith('.mleco'):
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(data)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data)

    @classmethod
    def load(cls, filepath: str) -> 'Project':
        try:
            if filepath.endswith('.mleco'):
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.loads(f.read())
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.loads(f.read())
            return cls.from_dict(data)
        except Exception as e:
            raise ValueError(f"Erro ao carregar projeto: {e}")
