import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

CSV_FILE = "vagas_novas_postar.csv"
LOGO_FOLDER = "logos"
SESSION_FILE = "linkedin_session.json"
DEBUG_SCREENSHOT = "debug_screenshot.png"


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

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            storage_state=SESSION_FILE
        )

        page = context.new_page()

        print("Abrindo LinkedIn...")
        page.goto("https://www.linkedin.com/feed/")

        page.wait_for_timeout(5000)

        page.screenshot(path=DEBUG_SCREENSHOT)
        print("Screenshot inicial salva")

        # -------------------
        # LOGIN RÁPIDO
        # -------------------

        print("Verificando tela de login rápido...")

        perfil = page.locator("i.profile__pic--ghost")

        if perfil.count() > 0:

            print("Perfil salvo detectado. Clicando para entrar...")

            perfil.first.click()

            page.wait_for_timeout(6000)

            page.goto("https://www.linkedin.com/feed/")

            page.wait_for_timeout(5000)

        else:

            print("Nenhum perfil salvo detectado.")

        # -------------------
        # CONFIRMAR FEED
        # -------------------

        print("Aguardando feed carregar...")

        try:

            page.wait_for_selector("div[role='main']", timeout=30000)

            print("Feed carregado com sucesso!")

        except:

            print("Feed não carregou")

            page.screenshot(path="erro_feed.png")

            browser.close()

            return

        # -------------------
        # LOOP DE POSTAGEM
        # -------------------

        for _, vaga in df.iterrows():

            titulo = vaga["titulo"]
            empresa = str(vaga["empresa"]).strip()

            print("Postando:", titulo)

            texto = gerar_texto(vaga)

            logo_path = os.path.join(LOGO_FOLDER, f"{empresa}.png")

            page.goto("https://www.linkedin.com/feed/")

            page.wait_for_timeout(5000)

            page.mouse.wheel(0, 800)

            page.wait_for_timeout(2000)

            # -------------------
            # ABRIR POST
            # -------------------

            print("Procurando botão de nova publicação...")

            botao_post = page.locator(
                "div[componentkey='draft-text-replaceable-component']"
            ).first

            botao_post.wait_for(timeout=20000)

            botao_post.click()

            # -------------------
            # DIGITAR TEXTO
            # -------------------

            print("Abrindo caixa de texto...")

            page.wait_for_selector("div[role='textbox']")

            page.locator("div[role='textbox']").first.fill(texto)

            page.wait_for_timeout(3000)

            # -------------------
            # FECHAR PREVIEW DO LINK
            # -------------------

            print("Tentando fechar preview do link...")

            try:

                fechar_preview = page.locator("use[href='#close-small']").first

                if fechar_preview.count() > 0:

                    fechar_preview.click()

                    print("Preview fechado")

                    page.wait_for_timeout(2000)

            except:

                print("Preview não encontrado")

            # -------------------
            # ADICIONAR LOGO
            # -------------------

            if os.path.exists(logo_path):

                print("Adicionando logo:", logo_path)

                page.locator(
                    "button[aria-label='Adicionar mídia']"
                ).first.click()

                page.wait_for_timeout(2000)

                page.set_input_files("input[type=file]", logo_path)

                page.wait_for_timeout(3000)

                page.locator(
                    "button:has-text('Avançar')"
                ).first.click()

                page.wait_for_timeout(4000)

            else:

                print("Logo não encontrada:", empresa)

            # -------------------
            # PUBLICAR
            # -------------------

            print("Publicando...")

            botao_publicar = page.locator(
                "button:has(span:has-text('Publicar'))"
            ).first

            botao_publicar.wait_for(timeout=10000)

            botao_publicar.click()

            print("Post publicado!")

            time.sleep(12)

        browser.close()


postar()
