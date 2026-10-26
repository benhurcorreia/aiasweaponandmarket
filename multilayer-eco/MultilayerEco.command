#\!/bin/bash
# MultilayerEco — Inicialização rápida
# Duplo clique neste arquivo para abrir o app diretamente do Finder

# Ir para a pasta do script (independente de onde foi aberto)
cd "$(dirname "$0")"

echo "Iniciando MultilayerEco..."

# Tentar python3 padrão do sistema
if python3 -c "import PySide6" 2>/dev/null; then
    python3 main.py
elif python3.11 -c "import PySide6" 2>/dev/null; then
    python3.11 main.py
elif python3.12 -c "import PySide6" 2>/dev/null; then
    python3.12 main.py
else
    echo ""
    echo "ERRO: PySide6 não encontrado."
    echo "Instale com: pip install PySide6"
    echo ""
    read -p "Pressione Enter para fechar..."
fi
