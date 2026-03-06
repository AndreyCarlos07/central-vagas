import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas.csv"
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

        context = browser.new_context()

        # ===============================
        # LOGIN VIA SESSION COOKIE
        # ===============================

        linkedin_session = os.environ["linkedin_session"]

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
        page.wait_for_load_state("networkidle")

        print("Login via sessão realizado!")

        for _, vaga in df.iterrows():

            texto = gerar_texto(vaga)

            empresa = str(vaga["empresa"]).strip()
            logo_path = f"{LOGO_FOLDER}/{empresa}.png"

            print("Postando vaga:", vaga["titulo"])

            try:

                page.goto("https://www.linkedin.com/feed/")
                page.wait_for_timeout(5000)

                page.wait_for_selector(
                    "div.share-box-feed-entry__trigger",
                    timeout=60000
                )

                page.click("div.share-box-feed-entry__trigger")

                page.wait_for_selector("div[role='textbox']")

                page.locator("div[role='textbox']").first.fill(texto)

                # ===============================
                # ADICIONAR LOGO
                # ===============================

                if os.path.exists(logo_path):

                    print("Adicionando logo:", logo_path)

                    page.set_input_files(
                        "input[type=file]",
                        logo_path
                    )

                    page.wait_for_timeout(4000)

                else:

                    print("Logo não encontrada:", logo_path)

                # ===============================
                # PUBLICAR POST
                # ===============================

                page.click("button:has-text('Post')")

                print("Post publicado!")

                # Delay para evitar bloqueio
                time.sleep(45)

            except Exception as e:

                print("Erro ao postar vaga:", e)

        browser.close()


if __name__ == "__main__":
    postar()
