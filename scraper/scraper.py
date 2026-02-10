#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os
import time

CSV_FILE = "vagas.csv"

SITES = [
    {
        "empresa": "BYD",
        "url": "https://bydbrasil.gupy.io",
        "selector": 'a[href*="/jobs/"]'
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io",
        "selector": 'a[href*="/jobs/"]'
    }
]

# 📍 palavras-chave para filtrar BAHIA
FILTRO_BA = [
    " - BA",
    " BAHIA",
    " SALVADOR",
    " CAMAÇARI",
    " LAURO DE FREITAS",
    " FEIRA DE SANTANA",
    " DIAS D'ÁVILA"
]


def clicar_carregar_mais(page):
    """
    Clica no botão 'Carregar mais' enquanto ele existir
    """
    while True:
        try:
            botao = page.locator("button:has-text('Carregar mais')")
            if botao.count() == 0:
                break

            botao.first.click()
            time.sleep(2)  # espera novas vagas renderizarem

        except Exception:
            break


def salvar_vagas(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "ativa"]
        )
        writer.writeheader()

        for vaga in vagas:
            writer.writerow(vaga)


def main():
    vagas = []
    links_encontrados = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['empresa']}")

            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(4000)

            # ✅ carrega TODAS as páginas clicando no botão
            clicar_carregar_mais(page)

            cards = page.locator(site["selector"])
            count = cards.count()

            print(f"[{site['empresa']}] Total de vagas encontradas: {count}")

            for i in range(count):
                try:
                    el = cards.nth(i)
                    titulo = el.inner_text(timeout=3000).strip()
                    link = el.get_attribute("href")

                    if not titulo or not link:
                        continue

                    titulo_upper = titulo.upper()

                    # 🎯 FILTRO BAHIA
                    if not any(x in titulo_upper for x in FILTRO_BA):
                        continue

                    if not link.startswith("http"):
                        link = site["url"] + link

                    if link in links_encontrados:
                        continue

                    links_encontrados.add(link)

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link,
                        "ativa": "1"
                    })

                except Exception:
                    continue

        browser.close()

    # 🔄 desativa vagas que sumiram do site
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    salvar_vagas(vagas)

    print("\n✅ Finalizado")
    print(f"📌 Vagas BA ativas: {len(links_encontrados)}")


if __name__ == "__main__":
    main()



