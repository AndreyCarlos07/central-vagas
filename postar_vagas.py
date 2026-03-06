import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os
import re

CSV_FILE = "vagas_novas_postar.csv"
LOGO_FOLDER = "logos"
DEBUG_SCREENSHOT = "debug_screenshot.png"


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
            headless=False,  # Mudar para False para debug
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            storage_state="linkedin_session.json",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        print("Abrindo LinkedIn...")
        page.goto("https://www.linkedin.com/feed/")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(8000)

        # Verificar login
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

                # Scroll humano extra
                for _ in range(5):
                    page.mouse.wheel(0, 500)
                    page.wait_for_timeout(1500)

                # Screenshot para debug
                page.screenshot(path=DEBUG_SCREENSHOT)
                print(f"Screenshot salva: {DEBUG_SCREENSHOT}")

                # Tentar localizar botão de criar publicação
                try:
                    button = page.locator(
                        "button:has-text('Começar publicação'), button:has-text('Start a post'), div.share-box-feed-entry__trigger"
                    ).first

                    button.wait_for(state="visible", timeout=30000)
                    button.click()
                    print("Botão de criar publicação clicado!")

                except Exception:
                    print("Não encontrou botão de criar publicação!")
                    continue

                # Caixa de texto
                page.wait_for_selector("div[role='textbox']", timeout=20000)
                page.locator("div[role='textbox']").first.fill(texto)

                # =========================
                # ADICIONAR LOGO
                # =========================
                if os.path.exists(logo_path):
                    print("Adicionando logo:", logo_path)
                    page.wait_for_selector("input[type=file]", timeout=15000)
                    page.set_input_files("input[type=file]", logo_path)
                    page.wait_for_timeout(5000)
                else:
                    print("Logo não encontrada:", empresa)

                # =========================
                # PUBLICAR
                # =========================
                page.wait_for_selector("button:has-text('Publicar'), button:has-text('Post')", timeout=20000)
                page.locator("button:has-text('Publicar'), button:has-text('Post')").first.click()
                print("Post publicado!")

                # Delay anti-bloqueio
                time.sleep(40)

            except Exception as e:
                print("Erro ao postar vaga:", e)
                page.screenshot(path="erro_post.png")
                print("Screenshot do erro salva: erro_post.png")

        browser.close()


if __name__ == "__main__":
    postar()
