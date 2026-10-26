# MultilayerEco — Guia de Instalação e Uso

## Instalação Rápida (macOS/Windows/Linux)

### 1. Instalar Python 3.10+
Se ainda não tem, baixe em: https://www.python.org/downloads/

### 2. Instalar dependências
Abra o terminal, navegue até a pasta do projeto e execute:

```bash
cd multilayer-eco
pip install -r requirements.txt
```

### 3. Executar o app
```bash
python main.py
```

O app abrirá com o caso demonstrativo **NYT vs OpenAI** já carregado.

---

## Uso Rápido

### Modo Manual
1. **Camadas**: Use o painel esquerdo (botão "+") para criar camadas
2. **Atores**: Adicione atores e marque em quais camadas aparecem
3. **Relações**: Conecte atores com relações tipadas (cooperação, competição, etc.)

### Modo Extração LLM
1. Menu **Análise → Extrair de Documento (LLM)**
2. Selecione um PDF, DOCX ou TXT
3. Insira sua API key (Anthropic ou OpenAI)
4. Defina as camadas desejadas
5. Clique em "Extrair Ecossistema"
6. Revise e aceite o resultado

### Exportação
- **PNG**: Menu Exportar → Exportar Imagem
- **JSON**: Menu Exportar → Exportar Projeto
- **CSV**: Menu Exportar → Exportar Atores/Relações/Métricas

### Navegação no Canvas
- **Zoom**: Scroll do mouse
- **Pan**: Clique do meio + arrastar
- **Mover nós**: Arrastar diretamente
- **Ajustar zoom**: Botão "Fit" na toolbar

---

## API Keys

Para a extração automatizada via LLM, você precisa de uma API key:

- **Anthropic Claude**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/

Você pode definir via variável de ambiente ou nas Configurações do app:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Estrutura do Projeto Salvo (.mleco)

Os projetos são salvos como JSON comprimido. Você pode abrir/editar manualmente
se necessário. O formato contém: camadas, atores, relações e posições visuais.
