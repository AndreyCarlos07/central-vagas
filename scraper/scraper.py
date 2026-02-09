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
    }
]

def carregar_vagas():
    vagas = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["ativa"] = "0"  # 🔴 tudo começa como inativo
                vagas[row["link"]] = row
    return vagas

def salvar_vagas(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "ativa"]
        )
        writer.writeheader()
        for vaga in vagas.values():
            writer.writerow(vaga)

def vaga_aceita_candidatura(page):
    # Heurística simples e eficiente
    botoes = page.query_selector_all("text=/candidatar|inscreva-se|apply/i")
    return len(botoes) > 0

def main():
    vagas = carregar_vagas()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(3000)

            links = page.query_selector_all('a[href*="/jobs/"]')

            for el in links:
                titulo = el.inner_text().strip()
                link = el.get_attribute("href")

                if not titulo or not link:
                    continue

                if not link.startswith("http"):
                    link = site["url"] + link

                page.goto(link, timeout=60000)
                page.wait_for_timeout(2000)

                if not vaga_aceita_candidatura(page):
                    continue  # 🚫 vaga encerrada

                if link in vagas:
                    vagas[link]["ativa"] = "1"
                else:
                    vagas[link] = {
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link,
                        "ativa": "1"
                    }

        browser.close()

    salvar_vagas(vagas)

if __name__ == "__main__":
    main()

