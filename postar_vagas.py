import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas_postar.csv"
LOGO_FOLDER = "logos"


def gerar_texto(vaga):

    titulo = str(vaga["titulo"]).replace("\n", " ").upper()
    empresa = str(vaga["empresa"]).strip()
    link = vaga["link"]

    texto = f"""{titulo}

EMPRESA: {empresa}
INSCREVA-SE:
{link}

Acesse pelo centralizador, todas as vagas abertas:
https://lnkd.in/ePRiUbXt

Obs: Não tenho qualquer envolvimento com a vaga, apenas divulgando no trabalho voluntário.

Sucesso
"""

    return texto


def postar():

    if not os.path.exists(CSV_FILE):
        print("Arquivo CSV não encontrado.")
        return

    df = pd.read_csv(CSV_FILE)

    if df.empty:
        print("Nenhuma vaga para postar.")
        return

    print("Total de vagas:", len(df))

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        # USAR STORAGE STATE (sessão salva do LinkedIn)
        context = browser.new_context(
            storage_state="linkedin_session.json",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        print("Abrindo LinkedIn...")

        page.goto("https://www.linkedin.com/feed/")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(8000)

        # verificar login
        if "feed" not in page.url:
            print("Sessão do LinkedIn inválida.")
            browser.close()
            return

        print("Sessão carregada com sucesso!")

        for _, vaga in df.iterrows():

            try:

                titulo = vaga["titulo"]
                print("Postando vaga:", titulo)

                texto = gerar_texto(vaga)

                empresa = str(vaga["empresa"]).strip()
                logo_path = f"{LOGO_FOLDER}/{empresa}.png"

                page.goto("https://www.linkedin.com/feed/")
                page.wait_for_timeout(5000)

                # scroll humano para carregar botão
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(2000)
                page.mouse.wheel(0, 300)
                page.wait_for_timeout(2000)

                # botão criar publicação (PT / EN)
                try:
                    page.wait_for_selector("button:has-text('Começar publicação')", timeout=15000)
                    page.locator("button:has-text('Começar publicação')").first.click()
                except:
                    page.wait_for_selector("button:has-text('Start a post')", timeout=15000)
                    page.locator("button:has-text('Start a post')").first.click()

                # caixa de texto
                page.wait_for_selector("div[role='textbox'], div[contenteditable='true']", timeout=20000)
                page.locator("div[role='textbox'], div[contenteditable='true']").first.fill(texto)

                # =========================
                # ADICIONAR LOGO
                # =========================

                if os.path.exists(logo_path):

                    print("Adicionando logo:", logo_path)

                    page.wait_for_selector("input[type=file]", timeout=15000)

                    page.set_input_files(
                        "input[type=file]",
                        logo_path
                    )

                    page.wait_for_timeout(5000)

                else:

                    print("Logo não encontrada:", empresa)

                # =========================
                # PUBLICAR
                # =========================

                page.wait_for_selector("button:has-text('Publicar'), button:has-text('Post')", timeout=20000)
                page.locator("button:has-text('Publicar'), button:has-text('Post')").first.click()

                print("Post publicado!")

                # delay anti-bloqueio
                time.sleep(40)

            except Exception as e:

                print("Erro ao postar vaga:", e)

        browser.close()


if __name__ == "__main__":
    postar()
