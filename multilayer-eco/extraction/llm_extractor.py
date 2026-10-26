"""
MultilayerEco - LLM Extractor
Extração automatizada de ecossistemas a partir de documentos via API Claude/OpenAI.
"""
import json
import os
import re


def read_document(filepath: str) -> str:
    """Extract text from PDF, DOCX, or TXT file."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.pdf':
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text

    elif ext == '.docx':
        from docx import Document
        doc = Document(filepath)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text

    elif ext in ('.txt', '.md'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    else:
        raise ValueError(f"Formato não suportado: {ext}")


def build_extraction_prompt(text: str, layer_names: list,
                            relation_types: list = None,
                            context: str = "") -> str:
    """Build the structured prompt for LLM extraction."""

    if not relation_types:
        relation_types = [
            "cooperação", "competição", "dependência",
            "fornecimento", "extração", "regulação",
            "investimento", "conflito", "integração"
        ]

    layers_str = ", ".join(f'"{name}"' for name in layer_names)
    rel_types_str = ", ".join(f'"{rt}"' for rt in relation_types)

    prompt = f"""Você é um analista especializado em ecossistemas de negócios multiníveis.
Analise o documento abaixo e extraia a estrutura do ecossistema em múltiplas camadas.

CAMADAS A IDENTIFICAR: [{layers_str}]

TIPOS DE RELAÇÃO POSSÍVEIS: [{rel_types_str}]

{f"CONTEXTO ADICIONAL: {context}" if context else ""}

PARA CADA CAMADA, identifique:
1. ATORES: organizações, instituições, tecnologias, reguladores, produtos, plataformas que participam
2. RELAÇÕES INTRA-CAMADA: como os atores se relacionam DENTRO de cada camada
3. RELAÇÕES INTER-CAMADA: como atores se conectam ENTRE camadas diferentes

REGRAS FUNDAMENTAIS:
- Um ator PODE e DEVE aparecer em múltiplas camadas se relevante
- Mantenha EXATAMENTE o mesmo nome do ator em todas as camadas (não mude nomes entre camadas)
- Cada relação deve ter: origem, destino, camada, tipo, direção
- Para relações inter-camada, indique camada_origem e camada_destino
- Os tipos de ator podem ser: Empresa, Governo, ONG, Tecnologia, Regulador, Plataforma, Mídia, Academia

Retorne EXCLUSIVAMENTE um JSON válido (sem markdown, sem comentários) no seguinte formato:
{{
  "actors": [
    {{
      "name": "Nome do Ator",
      "type": "Empresa",
      "layers": ["camada1", "camada2"]
    }}
  ],
  "intra_layer_relations": [
    {{
      "source": "Nome Ator 1",
      "target": "Nome Ator 2",
      "layer": "camada1",
      "type": "cooperação",
      "direction": "bidirectional",
      "label": "descrição curta da relação"
    }}
  ],
  "inter_layer_relations": [
    {{
      "source": "Nome Ator",
      "target": "Nome Ator",
      "source_layer": "camada1",
      "target_layer": "camada2",
      "type": "integração",
      "direction": "source_to_target",
      "label": "descrição curta"
    }}
  ]
}}

DOCUMENTO A ANALISAR:
---
{text[:15000]}
---

Retorne APENAS o JSON, sem nenhum texto adicional."""

    return prompt


def extract_with_anthropic(text: str, layer_names: list,
                           api_key: str, model: str = "claude-sonnet-4-20250514",
                           relation_types: list = None,
                           context: str = "") -> dict:
    """Extract ecosystem using Anthropic Claude API."""
    import anthropic

    prompt = build_extraction_prompt(text, layer_names, relation_types, context)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    return _parse_llm_response(response_text)


def extract_with_openai(text: str, layer_names: list,
                        api_key: str, model: str = "gpt-4o",
                        relation_types: list = None,
                        context: str = "") -> dict:
    """Extract ecosystem using OpenAI API."""
    import openai

    prompt = build_extraction_prompt(text, layer_names, relation_types, context)

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.1,
    )

    response_text = response.choices[0].message.content.strip()
    return _parse_llm_response(response_text)


def extract_with_gemini(text: str, layer_names: list,
                        api_key: str, model: str = "gemini-2.0-flash",
                        relation_types: list = None,
                        context: str = "") -> dict:
    """Extract ecosystem using Google Gemini API (via google-generativeai)."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "Biblioteca 'google-generativeai' não instalada. "
            "Execute: pip install google-generativeai"
        )

    prompt = build_extraction_prompt(text, layer_names, relation_types, context)

    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        prompt,
        generation_config={"temperature": 0.1, "max_output_tokens": 4096}
    )
    response_text = response.text.strip()
    return _parse_llm_response(response_text)


def extract_with_local(text: str, layer_names: list,
                       model: str = "gemma3",
                       base_url: str = "http://localhost:11434",
                       relation_types: list = None,
                       context: str = "") -> dict:
    """Extract ecosystem using a local Ollama model (e.g. Gemma via Ollama).

    Requires Ollama running locally: https://ollama.com
    Install model: ollama pull gemma3
    """
    import urllib.request
    import json as _json

    prompt = build_extraction_prompt(text, layer_names, relation_types, context)

    # Use Ollama's /api/generate endpoint
    url = base_url.rstrip("/") + "/api/generate"
    payload = _json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4096}
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise ConnectionError(
            f"Erro ao conectar ao Ollama em {base_url}.\n"
            f"Verifique se o Ollama está rodando e o modelo '{model}' está instalado.\n"
            f"Detalhe: {e}"
        )

    response_text = data.get("response", "").strip()
    if not response_text:
        raise ValueError("Ollama retornou resposta vazia. Verifique se o modelo está instalado.")

    return _parse_llm_response(response_text)


def _parse_llm_response(response_text: str) -> dict:
    """Parse LLM response, handling markdown code blocks."""
    # Remove markdown code block if present
    text = response_text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        try:
            data = json.loads(text)
        except:
            raise ValueError(f"Erro ao parsear JSON do LLM: {e}\nResposta: {text[:500]}")

    # Validate structure
    if "actors" not in data:
        raise ValueError("JSON não contém campo 'actors'")

    return data


def apply_extraction_to_project(project, extraction_data: dict):
    """Apply extracted data to a Project instance.

    Args:
        project: Project instance (should already have layers created)
        extraction_data: Dict from LLM extraction
    """
    from core.models import Project

    # Add actors
    actor_map = {}  # name -> actor
    for actor_data in extraction_data.get("actors", []):
        name = actor_data["name"].strip()
        actor_type = actor_data.get("type", "Empresa")
        layer_names = actor_data.get("layers", [])

        # Map layer names to IDs
        layer_ids = []
        for ln in layer_names:
            layer = project.get_layer_by_name(ln.strip())
            if layer:
                layer_ids.append(layer.id)

        # Check if actor already exists
        existing = project.find_actor_by_name(name)
        if existing:
            # Merge layers
            for lid in layer_ids:
                if lid not in existing.layers:
                    existing.layers.append(lid)
            actor_map[name] = existing
        else:
            actor = project.add_actor(name, actor_type, layer_ids)
            actor_map[name] = actor

    # Add intra-layer relations
    for rel_data in extraction_data.get("intra_layer_relations", []):
        src_name = rel_data["source"].strip()
        tgt_name = rel_data["target"].strip()
        layer_name = rel_data.get("layer", "").strip()

        src_actor = actor_map.get(src_name) or project.find_actor_by_name(src_name)
        tgt_actor = actor_map.get(tgt_name) or project.find_actor_by_name(tgt_name)
        layer = project.get_layer_by_name(layer_name)

        if src_actor and tgt_actor and layer:
            # Ensure actors are in this layer
            if layer.id not in src_actor.layers:
                src_actor.layers.append(layer.id)
            if layer.id not in tgt_actor.layers:
                tgt_actor.layers.append(layer.id)

            project.add_relationship(
                source_id=src_actor.id,
                target_id=tgt_actor.id,
                layer_id=layer.id,
                rel_type=rel_data.get("type", "cooperação"),
                direction=rel_data.get("direction", "bidirectional"),
                label=rel_data.get("label", ""),
            )

    # Add inter-layer relations
    for rel_data in extraction_data.get("inter_layer_relations", []):
        src_name = rel_data["source"].strip()
        tgt_name = rel_data["target"].strip()
        src_layer_name = rel_data.get("source_layer", "").strip()
        tgt_layer_name = rel_data.get("target_layer", "").strip()

        src_actor = actor_map.get(src_name) or project.find_actor_by_name(src_name)
        tgt_actor = actor_map.get(tgt_name) or project.find_actor_by_name(tgt_name)
        src_layer = project.get_layer_by_name(src_layer_name)
        tgt_layer = project.get_layer_by_name(tgt_layer_name)

        if src_actor and tgt_actor and src_layer and tgt_layer:
            project.add_relationship(
                source_id=src_actor.id,
                target_id=tgt_actor.id,
                rel_type=rel_data.get("type", "integração"),
                direction=rel_data.get("direction", "source_to_target"),
                label=rel_data.get("label", ""),
                source_layer_id=src_layer.id,
                target_layer_id=tgt_layer.id,
            )
