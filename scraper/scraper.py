#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os

CSV_FILE = "vagas.csv"

SITES = [
    {
        "empresa": "BYD",
        "url": "https://bydbrasil.gupy.io",
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io",
    }
]

# 📍 Filtro Bahia
FILTRO_BA = [
    " BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]


def forcar_50_por_pagina(page):
    try:
        page.locator("select").first.select_option("50")
        page.wait_for_timeout(3000)
    except Exception:
        pass


def carregar_todas_vagas(page):
    last_count = 0

    for _ in range(20):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        count = page.locator('a[href*="/jobs/"]').count()
        if count == last_count:
            break

        last_count = count


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

            # 🔧 força 50 vagas por página
            forcar_50_por_pagina(page)

            # 🔄 garante carregamento completo
            carregar_todas_vagas(page)

            cards = page.locator('a[href*="/jobs/"]')
            total = cards.count()

            print(f"📄 Total de cards encontrados: {total}")

            for i in range(total):
                try:
                    el = cards.nth(i)
                    titulo = el.inner_text(timeout=3000).strip()
                    link = el.get_attribute("href")

                    if not titulo or not link:
                        continue

                    titulo_upper = titulo.upper()
                    if not any(f in titulo_upper for f in FILTRO_BA):
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

    # 🔄 Marca vagas antigas como inativas
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    salvar_vagas(vagas)

    print("\n✅ Finalizado")
    print(f"📌 Vagas BA ativas encontradas: {len(links_encontrados)}")


if __name__ == "__main__":
    main()
