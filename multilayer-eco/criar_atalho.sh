#\!/bin/bash
# ─────────────────────────────────────────────────────────────
# MultilayerEco — Criador de atalho para o Finder/Dock
# Execute UMA VEZ no Terminal: bash criar_atalho.sh
# ─────────────────────────────────────────────────────────────

set -e

# Pasta do projeto (resolve o caminho real, mesmo com iCloud)
PROJECT="$(cd "$(dirname "$0")" && pwd)"
APP_OUT="$PROJECT/MultilayerEco.app"

echo "Pasta do projeto: $PROJECT"
echo ""

# ── Encontrar python3 com PySide6 ──────────────────────────
PYTHON=""
for PY in python3 python3.12 python3.11 python3.10; do
    if command -v "$PY" &>/dev/null && "$PY" -c "import PySide6" 2>/dev/null; then
        PYTHON="$(command -v $PY)"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERRO: Nenhum python3 com PySide6 encontrado."
    echo "Instale com: pip install PySide6"
    exit 1
fi

echo "Python encontrado: $PYTHON"
echo ""

# ── Remover .app antigo se existir ─────────────────────────
if [ -d "$APP_OUT" ]; then
    echo "Removendo .app antigo..."
    rm -rf "$APP_OUT"
fi

# ── Compilar .app com osacompile ───────────────────────────
echo "Criando MultilayerEco.app..."

osacompile -o "$APP_OUT" -e "
do shell script \"cd \" & quoted form of \"$PROJECT\" & \" && '$PYTHON' main.py > /tmp/multilayereco.log 2>&1 &\"
"

# ── Ajustar nome exibido no Finder ─────────────────────────
# (osacompile cria um Info.plist básico; sobrescrevemos o nome)
PLIST="$APP_OUT/Contents/Info.plist"
if [ -f "$PLIST" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleName MultilayerEco"        "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName MultilayerEco" "$PLIST" 2>/dev/null || true
fi

chmod +x "$APP_OUT/Contents/MacOS/"*

echo ""
echo "✓ MultilayerEco.app criado em:"
echo "  $APP_OUT"
echo ""
echo "Próximos passos:"
echo "  • Duplo clique no MultilayerEco.app para abrir"
echo "  • Ou arraste para o Dock para fixar"
echo "  • Na 1ª abertura: clique direito → Abrir (bypass Gatekeeper)"
echo ""
