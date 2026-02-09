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
        "selector": 'a[href*="/jobs/"]'
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io",
        "selector": 'a[href*="/jobs/"]'
    }
]

FILTRO_BA = [
    " BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]

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
            page_num = 0
            links_pagina_anterior = set()

            while True:
                url = f"{site['url']}?page={page_num}"
                page.goto(url, timeout=60000)
                page.wait_for_timeout(2500)

                cards = page.locator(site["selector"])
                count = cards.count()

                print(f"[{site['empresa']}] página {page_num} → {count} cards")

                links_pagina_atual = set()

                for i in range(count):
                    try:
                        el = cards.nth(i)
                        titulo = el.inner_text(timeout=2000).strip()
                        link = el.get_attribute("href")

                        if not titulo or not link:
                            continue

                        titulo_upper = titulo.upper()
                        if not any(x in titulo_upper for x in FILTRO_BA):
                            continue

                        if not link.startswith("http"):
                            link = site["url"] + link

                        links_pagina_atual.add(link)
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

                # 🚨 CONDIÇÃO DE PARADA CORRETA
                if not links_pagina_atual or links_pagina_atual == links_pagina_anterior:
                    print(f"[{site['empresa']}] fim da paginação")
                    break

                links_pagina_anterior = links_pagina_atual
                page_num += 1

        browser.close()

    salvar_vagas(vagas)

if __name__ == "__main__":
    main()


