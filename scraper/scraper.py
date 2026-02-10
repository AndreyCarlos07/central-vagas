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
        "url": "https://bydbrasil.gupy.io"
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io"
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


def carregar_todas_vagas(page, tentativas=25):
    links_vistos = set()
    sem_novos = 0

    for _ in range(tentativas):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        cards = page.locator('a[href*="/jobs/"]')
        count = cards.count()

        novos = 0
        for i in range(count):
            link = cards.nth(i).get_attribute("href")
            if link and link not in links_vistos:
                links_vistos.add(link)
                novos += 1

        if novos == 0:
            sem_novos += 1
        else:
            sem_novos = 0

        if sem_novos >= 3:
            break

    return links_vistos


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
            page.wait_for_timeout(5000)

            links = carregar_todas_vagas(page)

            print(f"[{site['empresa']}] links encontrados: {len(links)}")

            for link in links:
                if not link.startswith("http"):
                    link = site["url"] + link

                page.goto(link, timeout=30000)
                page.wait_for_timeout(2000)

                try:
                    titulo = page.locator("h1").inner_text().strip()
                except Exception:
                    continue

                titulo_upper = titulo.upper()
                if not any(f in titulo_upper for f in FILTRO_BA):
                    continue

                links_encontrados.add(link)

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link,
                    "ativa": "1"
                })

        browser.close()

    # 🔄 marca vagas antigas como inativas
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

