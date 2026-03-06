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

Obs: Não tenho quaisquer envolvimento com a vaga, apenas divulgando no trabalho voluntário.

Sucesso
"""
    return texto


def postar():

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

        # USER AGENT (reduz detecção de automação)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # ===============================
        # LOGIN VIA COOKIE LI_AT
        # ===============================

        linkedin_session = os.environ["LINKEDIN_LI_AT"]
        linkedin_jsession = os.environ["LINKEDIN_JSESSIONID"]

        context.add_cookies([
            {
                "name": "li_at",
                "value": linkedin_session,
                "domain": ".linkedin.com",
                "path": "/"
            },
            {
                "name": "JSESSIONID",
                "value": linkedin_jsession,
                "domain": ".linkedin.com",
                "path": "/"
            }
        ])

        page = context.new_page()

        print("Abrindo LinkedIn...")

        # IR DIRETO AO FEED (evita redirect)
        page.goto("https://www.linkedin.com/feed/")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(6000)

        print("Sessão carregada!")

        for _, vaga in df.iterrows():

            texto = gerar_texto(vaga)

            empresa = str(vaga["empresa"]).strip()
            logo_path = f"{LOGO_FOLDER}/{empresa}.png"

            print("Postando vaga:", vaga["titulo"])

            try:

                page.goto("https://www.linkedin.com/feed/")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(5000)

                # scroll humano
                page.mouse.wheel(0, 600)

                page.wait_for_selector("text=Começar publicação", timeout=60000)
                page.locator("text=Começar publicação").first.click()

                page.wait_for_selector("div[role='textbox']", timeout=20000)

                page.locator("div[role='textbox']").first.fill(texto)

                # ===============================
                # ADICIONAR LOGO
                # ===============================

                if os.path.exists(logo_path):

                    print("Adicionando logo:", logo_path)

                    page.wait_for_selector("input[type=file]", timeout=10000)

                    page.set_input_files(
                        "input[type=file]",
                        logo_path
                    )

                    page.wait_for_timeout(5000)

                else:

                    print("Logo não encontrada:", logo_path)

                # ===============================
                # PUBLICAR POST
                # ===============================

                page.wait_for_selector("button:has-text('Publicar')", timeout=20000)

                page.locator("button:has-text('Publicar')").first.click()

                print("Post publicado!")

                # Delay para evitar bloqueio
                time.sleep(45)

            except Exception as e:

                print("Erro ao postar vaga:", e)

        browser.close()


if __name__ == "__main__":
    postar()
