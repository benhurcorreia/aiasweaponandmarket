#!/usr/bin/env python3
"""
MultilayerEco — Visualização de Ecossistemas de Negócios Multinível
Aplicativo desktop para análise de ecossistemas multicamada.

Autor: Ben Hur Correia
Contexto: Tese de Doutorado — Dependência Estrutural em Ecossistemas de IA
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from ui.main_window import MainWindow
from core.models import Project


def create_demo_project() -> Project:
    """Create the NYT vs OpenAI demo project for testing."""
    project = Project(
        name="Ecossistema IA — NYT vs OpenAI",
        description="Análise multinível do caso NYT vs OpenAI (2023-2024). "
                    "Camadas: Conhecimento, Infraestrutura, Negócios."
    )

    # Create layers
    l_conhecimento = project.add_layer("Conhecimento", "#3498DB")
    l_infra = project.add_layer("Infraestrutura", "#27AE60")
    l_negocios = project.add_layer("Negócios", "#E74C3C")

    # Create actors
    nyt = project.add_actor("New York Times", "Mídia",
                            [l_conhecimento.id, l_negocios.id])
    openai = project.add_actor("OpenAI", "Empresa",
                               [l_conhecimento.id, l_infra.id, l_negocios.id])
    microsoft = project.add_actor("Microsoft", "Empresa",
                                  [l_infra.id, l_negocios.id])
    common_crawl = project.add_actor("Common Crawl", "Plataforma",
                                     [l_conhecimento.id])
    nvidia = project.add_actor("Nvidia", "Empresa",
                               [l_infra.id])
    chatgpt = project.add_actor("ChatGPT", "Tecnologia",
                                [l_negocios.id])
    copilot = project.add_actor("Microsoft Copilot", "Tecnologia",
                                [l_negocios.id])
    wirecutter = project.add_actor("Wirecutter", "Mídia",
                                   [l_conhecimento.id, l_negocios.id])
    gptbot = project.add_actor("GPTBot", "Tecnologia",
                               [l_conhecimento.id])
    tribunal = project.add_actor("Tribunal SDNY", "Regulador",
                                 [l_negocios.id])
    news_alliance = project.add_actor("News/Media Alliance", "ONG",
                                      [l_negocios.id])
    authors_guild = project.add_actor("Authors Guild", "ONG",
                                      [l_negocios.id])
    google = project.add_actor("Google", "Empresa",
                               [l_conhecimento.id, l_infra.id, l_negocios.id])
    aws = project.add_actor("Amazon AWS", "Empresa",
                            [l_infra.id])

    # ─── INTRA-LAYER RELATIONSHIPS ───

    # Conhecimento
    project.add_relationship(nyt.id, openai.id, l_conhecimento.id,
                             "extração", "source_to_target",
                             "dados de treino extraídos")
    project.add_relationship(common_crawl.id, openai.id, l_conhecimento.id,
                             "fornecimento", "source_to_target",
                             "corpus web para treino")
    project.add_relationship(gptbot.id, nyt.id, l_conhecimento.id,
                             "extração", "source_to_target",
                             "scraping de conteúdo")
    project.add_relationship(wirecutter.id, nyt.id, l_conhecimento.id,
                             "cooperação", "bidirectional",
                             "produção de conteúdo")
    project.add_relationship(common_crawl.id, google.id, l_conhecimento.id,
                             "fornecimento", "source_to_target",
                             "dados web")

    # Infraestrutura
    project.add_relationship(microsoft.id, openai.id, l_infra.id,
                             "investimento", "source_to_target",
                             "US$13bi + Azure cloud")
    project.add_relationship(nvidia.id, microsoft.id, l_infra.id,
                             "fornecimento", "source_to_target",
                             "GPUs H100/A100")
    project.add_relationship(nvidia.id, google.id, l_infra.id,
                             "fornecimento", "source_to_target",
                             "GPUs TPU alternatives")
    project.add_relationship(aws.id, openai.id, l_infra.id,
                             "competição", "bidirectional",
                             "cloud alternativa")

    # Negócios
    project.add_relationship(chatgpt.id, nyt.id, l_negocios.id,
                             "competição", "bidirectional",
                             "canibalização de mercado")
    project.add_relationship(copilot.id, nyt.id, l_negocios.id,
                             "competição", "bidirectional",
                             "substituição de conteúdo")
    project.add_relationship(openai.id, chatgpt.id, l_negocios.id,
                             "integração", "source_to_target",
                             "produto principal")
    project.add_relationship(nyt.id, tribunal.id, l_negocios.id,
                             "regulação", "source_to_target",
                             "ação judicial copyright")
    project.add_relationship(news_alliance.id, nyt.id, l_negocios.id,
                             "cooperação", "source_to_target",
                             "amicus brief apoio")
    project.add_relationship(authors_guild.id, openai.id, l_negocios.id,
                             "conflito", "source_to_target",
                             "ação coletiva autores")
    project.add_relationship(microsoft.id, copilot.id, l_negocios.id,
                             "integração", "source_to_target",
                             "produto Bing/Office")
    project.add_relationship(wirecutter.id, chatgpt.id, l_negocios.id,
                             "dependência", "source_to_target",
                             "conteúdo reproduzido")
    project.add_relationship(google.id, openai.id, l_negocios.id,
                             "competição", "bidirectional",
                             "mercado de IA generativa")

    # ─── INTER-LAYER RELATIONSHIPS ───

    # OpenAI across layers
    project.add_relationship(openai.id, openai.id,
                             rel_type="integração",
                             direction="source_to_target",
                             label="treino → infraestrutura",
                             source_layer_id=l_conhecimento.id,
                             target_layer_id=l_infra.id)
    project.add_relationship(openai.id, openai.id,
                             rel_type="integração",
                             direction="source_to_target",
                             label="deploy → mercado",
                             source_layer_id=l_infra.id,
                             target_layer_id=l_negocios.id)

    # NYT across layers
    project.add_relationship(nyt.id, nyt.id,
                             rel_type="dependência",
                             direction="source_to_target",
                             label="valor do arquivo centenário",
                             source_layer_id=l_conhecimento.id,
                             target_layer_id=l_negocios.id)

    # Microsoft across layers
    project.add_relationship(microsoft.id, microsoft.id,
                             rel_type="integração",
                             direction="source_to_target",
                             label="Azure → Copilot",
                             source_layer_id=l_infra.id,
                             target_layer_id=l_negocios.id)

    # Google across layers
    project.add_relationship(google.id, google.id,
                             rel_type="integração",
                             direction="source_to_target",
                             label="Search data → Gemini",
                             source_layer_id=l_conhecimento.id,
                             target_layer_id=l_negocios.id)

    return project


def main():
    # High DPI is enabled by default in Qt6, no need for the deprecated flag

    app = QApplication(sys.argv)
    app.setApplicationName("MultilayerEco")
    app.setOrganizationName("BenHurCorreia")

    # Set default font (use system font on macOS, Segoe UI on Windows)
    import platform
    if platform.system() == "Darwin":
        font = QFont(".AppleSystemUIFont", 10)
    else:
        font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()

    # Load demo project
    demo = create_demo_project()
    window.project = demo
    window._refresh_all()

    window.show()
    window.view.fit_all()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
