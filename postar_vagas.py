import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas.csv"
LOGO_FOLDER = "logos"

def gerar_texto(vaga):
    
    titulo = vaga['titulo'].upper()
    empresa = vaga['empresa']
    link = vaga['link']

    texto = f"""
{titulo}

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

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="linkedin_session.json")
        page = context.new_page()

        page.goto("https://www.linkedin.com/feed/")

        time.sleep(5)

        for _, vaga in df.iterrows():

            texto = gerar_texto(vaga)

            empresa = vaga["empresa"].upper()
            logo_path = f"{LOGO_FOLDER}/{empresa}.png"

            print("Postando:", vaga["titulo"])

            page.click("button[aria-label='Start a post']")

            time.sleep(2)

            page.fill("div[role='textbox']", texto)

            if os.path.exists(logo_path):

                page.set_input_files(
                    "input[type=file]",
                    logo_path
                )

            time.sleep(2)

            page.click("button:has-text('Post')")

            time.sleep(15)

        browser.close()


if __name__ == "__main__":
    postar()
