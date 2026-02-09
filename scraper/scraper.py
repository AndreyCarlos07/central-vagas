#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import csv
import uuid
import os

CSV_FILE = "vagas.csv"

SITES = [
    {
        "empresa": "BYD",
        "url": "https://bydbrasil.gupy.io/"
    }
]

def carregar_ids_existentes():
    ids = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ids.add(row["link"])
    return ids

def salvar_vagas(vagas):
    arquivo_existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "publicada_em", "expira_em"]
        )
        if not arquivo_existe:
            writer.writeheader()

        for vaga in vagas:
            writer.writerow(vaga)

def main():
    vagas_novas = []
    links_existentes = carregar_ids_existentes()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            page.goto(site["url"])

            # 🔴 AQUI você adapta pra cada site real
            elementos = page.query_selector_all("a")

            for el in elementos:
                titulo = el.inner_text().strip()
                link = el.get_attribute("href")

                if not titulo or not link:
                    continue

                if link in links_existentes:
                    continue

                hoje = datetime.today().date()
                expira = hoje + timedelta(days=20)

                vagas_novas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link,
                    "publicada_em": hoje.isoformat(),
                    "expira_em": expira.isoformat()
                })

        browser.close()

    salvar_vagas(vagas_novas)

if __name__ == "__main__":
    main()

