#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import os
from playwright.sync_api import sync_playwright

CSV_FILE = "vagas.csv"

BA_FILTER = ["BA", "SALVADOR", "FEIRA DE SANTANA"]  # você pode adicionar outras cidades da Bahia

SITES = [
    {
        "nome": "CIBRA",
        "url": "https://www.gupy.io/company/cibra/jobs",
        "card_selector": ".job-card",
        "title_selector": ".job-card-title",
        "location_selector": ".job-card-location a",
        "link_selector": "a[href]",
    },
]

def scrape():
    vagas = []
    links_encontrados = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['nome']}")
            page.goto(site["url"])

            cards = page.locator(site["card_selector"]).all()
            print(f"[{site['nome']}] Total de cards encontrados: {len(cards)}")

            for card in cards:
                try:
                    title = card.locator(site["title_selector"]).inner_text(timeout=2000).strip()
                    location = card.locator(site["location_selector"]).inner_text(timeout=2000).upper().strip()
                    link = card.locator(site["link_selector"]).get_attribute("href").strip()
                except:
                    continue

                # DEBUG: ver exatamente o que vem
                # print(f"DEBUG: {site['nome']} | {title} | {location} | {link}")

                if not any(f in location for f in BA_FILTER):
                    continue  # só pega vagas da Bahia

                if link not in links_encontrados:
                    vagas.append({"titulo": title, "empresa": site["nome"], "link": link, "ativa": "1"})
                    links_encontrados.add(link)

        browser.close()

    # Atualizar vagas antigas no CSV
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    # Salvar CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["titulo", "empresa", "link", "ativa"])
        writer.writeheader()
        for vaga in vagas:
            writer.writerow(vaga)

    print(f"\n✅ Finalizado. Total de vagas BA ativas: {len([v for v in vagas if v['ativa']=='1'])}")

if __name__ == "__main__":
    scrape()







