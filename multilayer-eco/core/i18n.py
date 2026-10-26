"""
MultilayerEco - Internationalization (i18n)
Suporte a idiomas: Português (pt, padrão) e English (en).

Uso:
    from core.i18n import tr, get_language, set_language
    label = tr("Camadas")   # "Camadas" em pt, "Layers" em en

A preferência de idioma é salva em ~/.multilayereco.json e carregada
na inicialização. Strings não encontradas no dicionário são retornadas
sem alteração (nomes próprios de atores, por exemplo).
"""
import json
import os

_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".multilayereco.json")

_language = "pt"


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg: dict):
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_language() -> str:
    return _language


def set_language(lang: str):
    """Define o idioma ('pt' ou 'en') e persiste a preferência."""
    global _language
    if lang not in ("pt", "en"):
        return
    _language = lang
    cfg = _load_config()
    cfg["language"] = lang
    _save_config(cfg)


def tr(text: str) -> str:
    """Traduz uma string PT para o idioma atual. Fallback: string original."""
    if _language == "en" and text is not None:
        return _PT_EN.get(text, text)
    return text


def tr_parts(text: str, sep: str = "/") -> str:
    """Traduz cada parte de uma string composta (ex.: 'focado/hub')."""
    if _language != "en" or not text:
        return text
    return sep.join(_PT_EN.get(p, p) for p in text.split(sep))


# ─── Dicionário PT → EN ───────────────────────────────────────────────────────

_PT_EN = {
    # ── Nomes de camadas (dados) ──
    "Fornecimento": "Supply",
    "Investimento": "Investment",
    "Extração": "Extraction",
    "Regulação": "Regulation",
    "Dependência": "Dependence",
    "Conflito": "Conflict",
    "Integração": "Integration",
    "Cooperação": "Cooperation",
    "Competição": "Competition",
    "Conhecimento": "Knowledge",
    "Infraestrutura": "Infrastructure",
    "Negócios": "Business",

    # ── Tipos de relação (dados) ──
    "cooperação": "cooperation",
    "competição": "competition",
    "dependência": "dependence",
    "fornecimento": "supply",
    "extração": "extraction",
    "regulação": "regulation",
    "investimento": "investment",
    "conflito": "conflict",
    "integração": "integration",
    "outro": "other",

    # ── Tipos de ator (dados) ──
    "Empresa": "Company",
    "Governo": "Government",
    "ONG": "NGO",
    "Tecnologia": "Technology",
    "Regulador": "Regulator",
    "Plataforma": "Platform",
    "Mídia": "Media",
    "Academia": "Academia",
    "Outro": "Other",

    # ── Categorias multiplex ──
    "focado": "focused",
    "misto": "mixed",
    "multiplex": "multiplex",
    "hub": "hub",
    "regular": "regular",

    # ── Canvas ──
    "Rede agregada (todas as relações)": "Aggregated network (all relationships)",

    # ── Janela principal ──
    "MultilayerEco — Ecossistemas de Negócios Multinível":
        "MultilayerEco — Multilevel Business Ecosystems",
    "Camadas": "Layers",
    "Atores": "Actors",
    "Relações": "Relationships",
    "Propriedades": "Properties",
    "Métricas da Rede": "Network Metrics",
    "Visualização": "View",
    "Adicionar Camada": "Add Layer",
    "Remover Camada": "Remove Layer",
    "Mover camada para cima": "Move layer up",
    "Mover camada para baixo": "Move layer down",
    "Adicionar Ator": "Add Actor",
    "Remover Ator": "Remove Actor",
    "Editar Ator": "Edit Actor",
    "Adicionar Relação": "Add Relationship",
    "Remover Relação": "Remove Relationship",
    "Diminuir zoom": "Zoom out",
    "Aumentar zoom": "Zoom in",
    "Nível de zoom": "Zoom level",
    "Ajustar toda a cena na janela": "Fit entire scene in window",
    "Scroll: zoom  |  Meio/Espaço: mover": "Scroll: zoom  |  Middle/Space: pan",
    "✋ Mover": "✋ Pan",
    "Modo Mover: clique+arraste para navegar no mapa\nAtalho: segure Espaço para mover temporariamente":
        "Pan mode: click+drag to navigate the map\nShortcut: hold Space to pan temporarily",
    "⊞ Espalhar": "⊞ Spread",
    "Redistribui automaticamente os atores de cada camada\nem grade, eliminando sobreposições":
        "Automatically redistributes the actors of each layer\nin a grid, eliminating overlaps",
    "Fonte nós:": "Node font:",
    "Tamanho da fonte dos nomes dos atores (6–60 pt)": "Font size of actor names (6–60 pt)",
    "Tamanho nó:": "Node size:",
    "Tamanho (raio) dos nós dos atores (3–48 px)": "Size (radius) of actor nodes (3–48 px)",
    "Fonte camada:": "Layer font:",
    "Tamanho da fonte do nome das camadas (8–48 pt)": "Font size of layer names (8–48 pt)",
    "Vista:": "View:",
    "Diagonal": "Diagonal",
    "Vertical": "Vertical",
    "Matriz": "Matrix",
    "Agregado": "Aggregated",
    "Modo de visualização das camadas": "Layer view mode",
    "Selecione um ator ou relação\npara ver propriedades.":
        "Select an actor or relationship\nto see properties.",
    "Adicione camadas e atores\npara ver métricas.":
        "Add layers and actors\nto see metrics.",
    "Camada isolada (2D):": "Isolated layer (2D):",
    "Mostra apenas uma camada, de frente (2D plano).\nEscolha 'Todas as camadas' para a visão completa em escada.":
        "Shows a single layer, front-facing (flat 2D).\nChoose 'All layers' for the full staircase view.",
    "Todas as camadas": "All layers",
    "↻ Recalcular Layout": "↻ Recompute Layout",
    # menus
    "Arquivo": "File",
    "Novo Projeto": "New Project",
    "Abrir Projeto...": "Open Project...",
    "Salvar Projeto": "Save Project",
    "Salvar Como...": "Save As...",
    "Sair": "Quit",
    "Editar": "Edit",
    "Gerenciar Tipos de Ator...": "Manage Actor Types...",
    "Configurações...": "Settings...",
    "Análise": "Analysis",
    "Extrair de Documento (LLM)...": "Extract from Document (LLM)...",
    "Comparar Ecossistemas (Antes/Depois)...": "Compare Ecosystems (Before/After)...",
    "Recalcular Layout": "Recompute Layout",
    "Calcular Métricas": "Compute Metrics",
    "Versatilidade e Participação...": "Versatility and Participation...",
    "Alinhar atores entre camadas (posição única)":
        "Align actors across layers (single position)",
    "Momentos": "Snapshots",
    "Salvar Momento Atual...": "Save Current Snapshot...",
    "Gerenciar Momentos...": "Manage Snapshots...",
    "Comparar Momentos...": "Compare Snapshots...",
    "Exportar": "Export",
    "Exportar Imagem (PNG)...": "Export Image (PNG)...",
    "Exportar Projeto (JSON)...": "Export Project (JSON)...",
    "Exportar Atores (CSV)...": "Export Actors (CSV)...",
    "Exportar Relações (CSV)...": "Export Relationships (CSV)...",
    "Exportar Métricas (CSV)...": "Export Metrics (CSV)...",
    "Idioma / Language": "Idioma / Language",
    "Português": "Português",
    "English": "English",
    "Idioma alterado. Reinicie o aplicativo para aplicar em toda a interface.":
        "Language changed. Restart the application to apply it to the whole interface.",
    # toolbar
    "Principal": "Main",
    "Novo": "New",
    "Abrir": "Open",
    "Salvar": "Save",
    "+ Camada": "+ Layer",
    "+ Ator": "+ Actor",
    "+ Relação": "+ Relationship",
    "⇄ Comparar": "⇄ Compare",
    # ações e mensagens
    "Remover a camada '{name}'?\nAtores exclusivos desta camada serão removidos.":
        "Remove layer '{name}'?\nActors exclusive to this layer will be removed.",
    "Camada: {name}\nOrdem: {order}\nAtores: {actors}\nRelações: {rels}":
        "Layer: {name}\nOrder: {order}\nActors: {actors}\nRelationships: {rels}",
    "Aviso": "Warning",
    "Adicione pelo menos uma camada primeiro.": "Add at least one layer first.",
    "Adicione pelo menos dois atores primeiro.": "Add at least two actors first.",
    "Remover '{name}' e todas as suas relações?":
        "Remove '{name}' and all its relationships?",
    "Ator: {name}\nTipo: {type}\nCamadas: {layers}\nRelações: {rels}":
        "Actor: {name}\nType: {type}\nLayers: {layers}\nRelationships: {rels}",
    "Extração aplicada com sucesso!": "Extraction applied successfully!",
    "{n} atores": "{n} actors",
    "Tipo: {type} | Camadas: {n}": "Type: {type} | Layers: {n}",
    "{name} | {layers} camadas | {actors} atores | {rels} relações":
        "{name} | {layers} layers | {actors} actors | {rels} relationships",
    "▸ {name}\n  Nós: {nodes} | Arestas: {edges}\n  Densidade: {density:.4f}\n":
        "▸ {name}\n  Nodes: {nodes} | Edges: {edges}\n  Density: {density:.4f}\n",
    "\n▸ Inter-Camada\n": "\n▸ Inter-Layer\n",
    "  {pair}: {count} compartilhados\n": "  {pair}: {count} shared\n",
    "Erro: {msg}": "Error: {msg}",
    "Versatilidade": "Versatility",
    "Adicione camadas, atores e relações antes de calcular a versatilidade.":
        "Add layers, actors and relationships before computing versatility.",
    "Alinhar atores": "Align actors",
    "Carregue um ecossistema com atores e relações primeiro.":
        "Load an ecosystem with actors and relationships first.",
    "Posições alinhadas: cada ator ocupa a mesma posição em todas as suas camadas (centralidade → centro).":
        "Positions aligned: each actor occupies the same position in all its layers (centrality → center).",
    "Criar novo projeto? Mudanças não salvas serão perdidas.":
        "Create a new project? Unsaved changes will be lost.",
    "Abrir Projeto": "Open Project",
    "Projeto MultilayerEco (*.mleco *.json)": "MultilayerEco Project (*.mleco *.json)",
    "Projeto carregado: {path}": "Project loaded: {path}",
    "Erro": "Error",
    "Erro ao abrir: {e}": "Error opening: {e}",
    "Erro ao salvar: {e}": "Error saving: {e}",
    "Salvo: {path}": "Saved: {path}",
    "Projeto MultilayerEco (*.mleco);;JSON (*.json)":
        "MultilayerEco Project (*.mleco);;JSON (*.json)",
    "Exportar Imagem": "Export Image",
    "Imagem exportada: {path}": "Image exported: {path}",
    "Exportar JSON": "Export JSON",
    "JSON exportado: {path}": "JSON exported: {path}",
    "Exportar Atores CSV": "Export Actors CSV",
    "Exportar Relações CSV": "Export Relationships CSV",
    "Exportar Métricas CSV": "Export Metrics CSV",
    "CSV exportado: {path}": "CSV exported: {path}",
    "Novo Projeto": "New Project",
    "Adicione camadas e atores antes de salvar um momento.":
        "Add layers and actors before saving a snapshot.",
    "Momento {n}": "Snapshot {n}",
    "Salvar Momento": "Save Snapshot",
    "Nome do momento (ex.: Antes, Depois, 2023):":
        "Snapshot name (e.g.: Before, After, 2023):",
    "atualizado": "updated",
    "salvo": "saved",
    "Momento '{name}' {verb}.": "Snapshot '{name}' {verb}.",
    "Gerenciar Momentos": "Manage Snapshots",
    "Momentos salvos neste projeto:": "Snapshots saved in this project:",
    "Renomear": "Rename",
    "Remover": "Remove",
    "Novo nome:": "New name:",

    # ── Diálogo de versatilidade ──
    "Versatilidade e Participação Multiplex": "Multiplex Versatility and Participation",
    "Estado:": "State:",
    "Projeto atual": "Current project",
    "Momento: {name}": "Snapshot: {name}",
    "Excluir Competição": "Exclude Competition",
    "A camada de Competição costuma ser um grafo completo (densidade 1 por definição) e infla a participação de todos os labs ao mesmo tempo.":
        "The Competition layer is usually a complete graph (density 1 by definition) and inflates the participation of all labs at once.",
    "Ponderar por peso": "Weight by edge weight",
    "Usa a soma de pesos das arestas em vez do grau simples.":
        "Uses the sum of edge weights instead of simple degree.",
    "Exportar CSV...": "Export CSV...",
    "Ator": "Actor",
    "Tipo": "Type",
    "# cam.": "# lay.",
    "Categoria": "Category",
    "Vi: versatilidade multinível.  Pi: participação (0 = papel concentrado num tipo de relação, 1 = distribuído entre os tipos).  o_i: grau de sobreposição.  Categoria: faixa de participação (focado / misto / multiplex) e hub quando z ≥ 1.":
        "Vi: multilevel versatility.  Pi: participation (0 = role concentrated in one relationship type, 1 = distributed across types).  o_i: overlapping degree.  Category: participation range (focused / mixed / multiplex) and hub when z ≥ 1.",
    "Erro ao calcular métricas: {e}": "Error computing metrics: {e}",
    "{n} camadas consideradas | {actors} atores | {rels} relações\nDensidade por camada: {dens}":
        "{n} layers considered | {actors} actors | {rels} relationships\nDensity per layer: {dens}",
    "Exportar Métricas de Versatilidade": "Export Versatility Metrics",
    "Exportado": "Exported",
    "Métricas salvas em:\n{path}": "Metrics saved to:\n{path}",
    "Erro ao exportar: {e}": "Error exporting: {e}",

    # ── Diálogos ──
    "Editar Camada": "Edit Layer",
    "Nova Camada": "New Layer",
    "✦ Editar Camada": "✦ Edit Layer",
    "✦ Nova Camada": "✦ New Layer",
    "Nome da camada *": "Layer name *",
    "Ex: Conhecimento, Infraestrutura, Negócios...":
        "E.g.: Knowledge, Infrastructure, Business...",
    "Cor de destaque": "Highlight color",
    "Cancelar": "Cancel",
    "Adicionar": "Add",
    "⚠ Nome obrigatório": "⚠ Name required",
    "Editar Ator": "Edit Actor",
    "Novo Ator": "New Actor",
    "✦ Editar Ator": "✦ Edit Actor",
    "✦ Novo Ator": "✦ New Actor",
    "Nome do ator *": "Actor name *",
    "Ex: OpenAI, NYT, Google, Governo EUA...": "E.g.: OpenAI, NYT, Google, US Government...",
    "Tipo do ator": "Actor type",
    "Camadas onde este ator aparece": "Layers where this actor appears",
    "(Nenhuma camada criada ainda)": "(No layers created yet)",
    "Adicionar Ator": "Add Actor",
    "Atenção": "Attention",
    "Selecione pelo menos uma camada para o ator.":
        "Select at least one layer for the actor.",
    "Gerenciar Tipos de Ator": "Manage Actor Types",
    "✦ Tipos de Ator": "✦ Actor Types",
    "Tipos padrão (não removíveis) + seus tipos personalizados:":
        "Default types (not removable) + your custom types:",
    "Tipos embutidos": "Built-in types",
    "Tipos personalizados": "Custom types",
    "Novo tipo (ex: Investidor, Parceiro...)": "New type (e.g.: Investor, Partner...)",
    "+ Adicionar": "+ Add",
    "✕ Remover selecionado": "✕ Remove selected",
    "Fechar": "Close",
    "O tipo '{t}' já existe.": "Type '{t}' already exists.",
    "Editar Relação": "Edit Relationship",
    "Nova Relação": "New Relationship",
    "✦ Editar Relação": "✦ Edit Relationship",
    "✦ Nova Relação": "✦ New Relationship",
    "ATORES": "ACTORS",
    "Origem": "Source",
    "Destino": "Target",
    "CAMADA": "LAYER",
    "Relação inter-camada  (conecta atores de camadas diferentes)":
        "Inter-layer relationship  (connects actors from different layers)",
    "Camada:": "Layer:",
    "Camada Origem": "Source Layer",
    "Camada Destino": "Target Layer",
    "PROPRIEDADES": "PROPERTIES",
    "Direção": "Direction",
    "↔ Bidirecional": "↔ Bidirectional",
    "→ Origem→Destino": "→ Source→Target",
    "← Destino→Origem": "← Target→Source",
    "Rótulo (opcional)": "Label (optional)",
    "Breve descrição da relação": "Brief description of the relationship",
    "Peso": "Weight",
    "Adicionar Relação": "Add Relationship",
    "Extração Automatizada via LLM": "Automated LLM Extraction",
    "✦ Extrair Ecossistema de Documento": "✦ Extract Ecosystem from Document",
    "Documento de origem *": "Source document *",
    "Selecione um arquivo PDF, DOCX ou TXT...": "Select a PDF, DOCX or TXT file...",
    "Selecionar...": "Select...",
    "PROVEDOR DE IA": "AI PROVIDER",
    "Camadas a extrair (uma por linha)": "Layers to extract (one per line)",
    "Contexto adicional (opcional)": "Additional context (optional)",
    "Ex: Foque em relações de dependência tecnológica entre empresas de IA...":
        "E.g.: Focus on technological dependence relationships between AI companies...",
    "Modelo:": "Model:",
    "Selecionar Documento": "Select Document",
    "Documentos (*.pdf *.docx *.txt *.md)": "Documents (*.pdf *.docx *.txt *.md)",
    "Insira a API Key da Anthropic.": "Enter the Anthropic API Key.",
    "Insira a API Key da OpenAI.": "Enter the OpenAI API Key.",
    "Insira a API Key do Google Gemini.": "Enter the Google Gemini API Key.",
    "Selecione um documento.": "Select a document.",
    "Defina pelo menos uma camada.": "Define at least one layer.",
    "Lendo documento...": "Reading document...",
    "Documento lido ({n} chars). Enviando ao {provider}...":
        "Document read ({n} chars). Sending to {provider}...",
    "✓ Concluído: {actors} atores, {intra} relações intra, {inter} relações inter-camada":
        "✓ Done: {actors} actors, {intra} intra-layer, {inter} inter-layer relationships",
    "Extração Concluída": "Extraction Complete",
    "Resultados encontrados:\n• {actors} atores\n• {intra} relações intra-camada\n• {inter} relações inter-camada\n\nDeseja aplicar ao projeto?":
        "Results found:\n• {actors} actors\n• {intra} intra-layer relationships\n• {inter} inter-layer relationships\n\nApply to the project?",
    "Erro na Extração": "Extraction Error",
    "⚡ Extrair Ecossistema": "⚡ Extract Ecosystem",
    "Configurações": "Settings",
    "✦ Configurações": "✦ Settings",
    "CHAVES DE API": "API KEYS",
    "VISUALIZAÇÃO": "VIEW",
    "Algoritmo de Layout": "Layout Algorithm",
    "Usar visualização isométrica (experimental)": "Use isometric view (experimental)",
    "Diagonal (cascata)": "Diagonal (staircase)",
    "Vertical (mesmo eixo)": "Vertical (same axis)",
    "Matriz (grade)": "Matrix (grid)",
    "Plano agregado (1 plano)": "Aggregated plane (1 plane)",
    "Tamanho da fonte do nome das camadas": "Layer name font size",
    "Tamanho da fonte dos atores": "Actor font size",
    "Tamanho do nó (raio)": "Node size (radius)",
    "Passo diagonal horizontal (entre camadas)": "Horizontal diagonal step (between layers)",
    "Passo diagonal vertical (entre camadas)": "Vertical diagonal step (between layers)",
    "Salvar Configurações": "Save Settings",

    # ── Janela de comparação ──
    "Comparar Ecossistemas — Antes / Depois": "Compare Ecosystems — Before / After",
    "Isolar camada:": "Isolate layer:",
    "⊡ Ajustar ambos": "⊡ Fit both",
    "⤓ Exportar comparação (PNG)": "⤓ Export comparison (PNG)",
    "Todas as camadas (visão completa)": "All layers (full view)",
    "Antes": "Before",
    "Depois": "After",
    "Título deste lado (ex.: Antes)": "Title of this side (e.g.: Before)",
    "Carregar projeto…": "Load project…",
    "Carregar um ecossistema de um arquivo .mleco/.json (render ao vivo)":
        "Load an ecosystem from a .mleco/.json file (live render)",
    "Carregar PNG…": "Load PNG…",
    "Carregar uma imagem PNG já pronta de um ecossistema":
        "Load a ready-made PNG image of an ecosystem",
    "⊡ Ajustar": "⊡ Fit",
    "● Projeto aberto": "● Open project",
    "◷ Momento: {name}": "◷ Snapshot: {name}",
    "Falha ao carregar: {e}": "Failed to load: {e}",
    "Carregar Ecossistema": "Load Ecosystem",
    "Carregar Imagem PNG": "Load PNG Image",
    "Imagem PNG (*.png)": "PNG Image (*.png)",
    "Não foi possível abrir a imagem:\n{path}": "Could not open the image:\n{path}",
    "Imagem PNG · {w}×{h} px": "PNG image · {w}×{h} px",
    "{nl} camadas · {na} atores · {nr} relações":
        "{nl} layers · {na} actors · {nr} relationships",
    "Tamanho da fonte dos nomes dos atores (render ao vivo)":
        "Font size of actor names (live render)",
    "Carregue ecossistemas nos dois lados.": "Load ecosystems on both sides.",
    "Exportar Comparação": "Export Comparison",
    "Comparação salva em:\n{path}": "Comparison saved to:\n{path}",
    "Falha ao exportar: {e}": "Failed to export: {e}",
    "Camada isolada: {name}": "Isolated layer: {name}",
    "Visão completa do ecossistema": "Full ecosystem view",
}


# Carrega a preferência salva na importação do módulo
_language = _load_config().get("language", "pt")
