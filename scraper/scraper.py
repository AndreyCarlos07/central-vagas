#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CSV_FILE = "vagas.csv"
FIELDNAMES = ["titulo", "empresa", "link", "ativa", "inativa"]

def scrape_site(page, url, nome_site):
    print(f"\n🔎 Buscando vagas da {nome_site}")
    vagas = []

    try:
        page.goto(url, timeout=30000)  # aumenta timeout para 30s
        # Aguarda os cards aparecerem (ajuste seletor conforme necessário)
        page.wait_for_selector("a[href*='/jobs/']", timeout=20000)

        cards = page.locator("a[href*='/jobs/']")
        total = cards.count()
        print(f"[{nome_site}] Total de cards encontrados: {total}")

        for i in range(total):
            card = cards.nth(i)
            titulo = card.inner_text().strip()
            link = card.get_attribute("href")
            vagas.append({
                "titulo": titulo,
                "empresa": nome_site,
                "link": link,
                "ativa": "sim",
                "inativa": "não"
            })

    except PlaywrightTimeoutError:
        print(f"[{nome_site}] nenhum card encontrado (timeout)")
        # salva HTML para debug
        with open(f"{nome_site}_page.html", "w", encoding="utf-8") as f:
            f.write(page.content())

    return vagas

def scrape():
    all_vagas = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Sites que você quer raspar
        sites = {
            "CIBRA": "https://example.com/cibra-jobs",
            "BYD": "https://example.com/byd-jobs",
            "Motiva": "https://example.com/motiva-jobs"
        }

        for nome, url in sites.items():
            vagas = scrape_site(page, url, nome)
            all_vagas.extend(vagas)

        browser.close()

    # Escrevendo no CSV, filtrando apenas os fieldnames
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for vaga in all_vagas:
            writer.writerow({k: v for k, v in vaga.items() if k in FIELDNAMES})

    print(f"\n✅ Total de vagas salvas: {len(all_vagas)}")

if __name__ == "__main__":
    scrape()










