import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas_postar.csv"
LOGO_FOLDER = "logos"
DEBUG_SCREENSHOT = "debug_action.png"


def gerar_texto(vaga):

    titulo = str(vaga["titulo"]).replace("\n", " ").upper()
    empresa = str(vaga["empresa"]).strip()
    link = vaga["link"]

    texto = f"""{titulo}
EMPRESA: {empresa}
INSCREVA-SE: {link}

Acesse pelo centralizador, todas as vagas abertas:
https://lnkd.in/ePRiUbXt

Obs: Não tenho qualquer envolvimento com a vaga, apenas divulgando no trabalho voluntário.

Sucesso
"""

    return texto


def postar():

    if not os.path.exists(CSV_FILE):
        print("CSV não encontrado:", CSV_FILE)
        return

    df = pd.read_csv(CSV_FILE)

    if df.empty:
        print("CSV vazio.")
        return

    print("Total de vagas:", len(df))

    linkedin_session = os.getenv("LINKEDIN_SESSION")

    if not linkedin_session:
        print("LINKEDIN_SESSION não encontrado nos Secrets.")
        return

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context()

        context.add_cookies([
            {
                "name": "li_at",
                "value": linkedin_session,
                "domain": ".linkedin.com",
                "path": "/"
            }
        ])

        page = context.new_page()

        print("Abrindo LinkedIn...")
        page.goto("https://www.linkedin.com/feed/")

        page.wait_for_timeout(5000)

        page.screenshot(path=DEBUG_SCREENSHOT)
        print("Screenshot inicial salva")

        # detectar tela "Olá novamente"
        try:

            botao = page.locator(
                "button:has-text('Continuar'), button:has-text('Continue'), button:has-text('Entrar')"
            ).first

            if botao.is_visible():

                print("Tela 'Olá novamente' detectada")

                botao.click()

                page.wait_for_load_state("networkidle")

        except:

            print("Nenhuma tela de login detectada")

        # confirmar feed
        try:

            page.wait_for_selector(
                "div.share-box-feed-entry__trigger",
                timeout=20000
            )

            print("Feed carregado com sucesso!")

        except:

            print("Feed não carregou")
            page.screenshot(path="erro_feed.png")
            browser.close()
            return

        for _, vaga in df.iterrows():

            titulo = vaga["titulo"]
            empresa = str(vaga["empresa"]).strip()

            print("Postando:", titulo)

            texto = gerar_texto(vaga)

            logo_path = os.path.join(LOGO_FOLDER, f"{empresa}.png")

            page.goto("https://www.linkedin.com/feed/")

            page.wait_for_timeout(4000)

            page.mouse.wheel(0, 800)

            page.wait_for_timeout(2000)

            # abrir caixa de postagem
            button = page.locator(
                "button:has-text('Começar publicação'), button:has-text('Start a post'), div.share-box-feed-entry__trigger"
            ).first

            button.click()

            page.wait_for_selector("div[role='textbox']")

            page.locator("div[role='textbox']").first.fill(texto)

            if os.path.exists(logo_path):

                print("Adicionando logo:", logo_path)

                page.set_input_files(
                    "input[type=file]",
                    logo_path
                )

                page.wait_for_timeout(4000)

            else:

                print("Logo não encontrada:", empresa)

            page.locator(
                "button:has-text('Publicar'), button:has-text('Post')"
            ).first.click()

            print("Post publicado!")

            time.sleep(10)

        browser.close()


postar()
