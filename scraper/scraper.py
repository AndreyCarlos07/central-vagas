#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import os
from playwright.sync_api import sync_playwright, TimeoutError

CSV_FILE = "vagas.csv"

BA_FILTER = ["BA", "SALVADOR", "FEIRA DE SANTANA"]  # filtro por cidade/estado

SITES = [
    {
        "nome": "CIBRA",
        "url": "https://www.gupy.io/company/cibra/jobs",
    },
    {
        "nome": "BYD",
        "url": "https://www.gupy.io/company/byd/jobs",
    },
    {
        "nome": "Motiva",
        "url": "https://www.gupy.io/company/motiva/jobs",
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

            # Espera aparecer qualquer card de vaga
            try:
                page.wait_for_selector("li[data-job-id], .job-card, a[href*='/jobs/']", timeout=10000)
            except TimeoutError:
                print(f"[{site['nome']}] nenhum card encontrado (timeout)")

            # Tenta 2 tipos de seletor
            cards = page.locator("li[data-job-id], .job-card")
            print(f"[{site['nome']}] Total de cards encontrados: {cards.count()}")

            for i in range(cards.count()):
                card = cards.nth(i)
                try:
                    # tenta pegar título
                    title = card.locator("h3, .job-card-title, .job-title").inner_text(timeout=2000).strip()
                except:
                    title = ""

                try:
                    # tenta pegar local
                    location = card.locator(".job-card-location, .location, .job-location").inner_text(timeout=2000).upper().strip()
                except:
                    location = ""

                try:
                    # tenta pegar link direto
                    link = card.locator("a[href*='/jobs/']").get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.gupy.io" + link
                except:
                    link = ""

                if not link:
                    continue

                if not any(f in location for f in BA_FILTER):
                    continue  # só pega Bahia

                if link not in links_encontrados:
                    vagas.append({
                        "titulo": title,
                        "empresa": site["nome"],
                        "link": link,
                        "ativa": "1",
                        "inativa": "0"
                    })
                    links_encontrados.add(link)

        browser.close()

    # Atualizar vagas antigas no CSV
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vaga["inativa"] = "1"
                    vagas.append(vaga)

    # Salvar CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["titulo", "empresa", "link", "ativa", "inativa"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vaga in vagas:
            writer.writerow(vaga)

    total_ativas = len([v for v in vagas if v["ativa"] == "1"])
    print(f"\n✅ Finalizado. Total de vagas BA ativas: {total_ativas}")

if __name__ == "__main__":
    scrape()










