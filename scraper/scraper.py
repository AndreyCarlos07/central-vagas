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
    }
]


def carregar_links_existentes():
    links = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                links.add(row["link"])
    return links


def salvar_vagas(vagas):
    arquivo_existe = os.path.exists(CSV_FILE)

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
    links_existentes = carregar_links_existentes()
    links_encontrados = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(4000)

            cards = page.locator(site["selector"])

            count = cards.count()

            for i in range(count):
                try:
                    el = cards.nth(i)
                    titulo = el.inner_text(timeout=3000).strip()
                    link = el.get_attribute("href")

                    if not titulo or not link:
                        continue

                    if not link.startswith("http"):
                        link = site["url"] + link

                    links_encontrados.add(link)

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link,
                        "ativa": "1"
                    })

                except Exception:
                    # ignora card bugado sem derrubar o job
                    continue

        browser.close()

    # 🔄 se a vaga existia antes e não foi encontrada agora → desativa
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    salvar_vagas(vagas)

if __name__ == "__main__":
    main()


