import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas.csv"
LOGO_FOLDER = "logos"
SESSION_FILE = "linkedin_session.json"


def gerar_texto(vaga):

    titulo = str(vaga["titulo"]).upper()
    empresa = vaga["empresa"]
    link = vaga["link"]

    texto = f"""{titulo}

EMPRESA: {empresa}
INSCREVA-SE:
{link}

Acesse pelo centralizador, todas as vagas abertas:
https://lnkd.in/ePRiUbXt

Obs: Não tenho quaisquer envolvimento com a vaga, apenas divulgando no trabalho voluntário.

Sucesso
"""
    return texto


def postar():

    df = pd.read_csv(CSV_FILE)

    print("Total de vagas:", len(df))

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(storage_state=SESSION_FILE)

        page = context.new_page()

        print("Abrindo LinkedIn...")

        page.goto("https://www.linkedin.com/feed/")

        page.wait_for_load_state("networkidle")

        print("Página carregada:", page.url)

        for _, vaga in df.iterrows():

            texto = gerar_texto(vaga)

            empresa = str(vaga["empresa"]).upper()
            logo_path = f"{LOGO_FOLDER}/{empresa}.png"

            print("Postando vaga:", vaga["titulo"])

            try:

                page.wait_for_selector(
                    "div.share-box-feed-entry__trigger",
                    timeout=60000
                )

                page.click("div.share-box-feed-entry__trigger")

                time.sleep(3)

                page.wait_for_selector("div[role='textbox']")

                page.fill("div[role='textbox']", texto)

                if os.path.exists(logo_path):

                    print("Adicionando logo:", logo_path)

                    page.set_input_files(
                        "input[type=file]",
                        logo_path
                    )

                    time.sleep(3)

                else:

                    print("Logo não encontrada:", logo_path)

                page.click("button:has-text('Post')")

                print("Post publicado!")

                time.sleep(30)

            except Exception as e:

                print("Erro ao postar vaga:", e)

        browser.close()


if __name__ == "__main__":
    postar()
