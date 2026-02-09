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
        "empresa": "CIBRA",
        "url": "https://cibra.gupy.io/",
        "job_selector": 'a[href*="/jobs/"]',
        "location_selector": ".job-card-location"  # classe que aparece na listagem das vagas
    }
]

# Estados/locais da Bahia
BA_FILTER = [
    "BA", "BAHIA", "SALVADOR", "CAMAÇARI", 
    "LAURO DE FREITAS", "FEIRA DE SANTANA", "DIAS D'ÁVILA"
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
            print(f"\n🔎 Buscando vagas da {site['empresa']}")
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(3000)

            # pegar todas as vagas da listagem
            cards = page.locator(site["job_selector"])
            count = cards.count()
            print(f"[{site['empresa']}] Total de cards encontrados: {count}")

            for i in range(count):
                try:
                    el = cards.nth(i)
                    titulo = el.inner_text(timeout=2000).strip()
                    link = el.get_attribute("href")
                    location = el.locator(site["location_selector"]).inner_text(timeout=2000).upper()

                    if not link.startswith("http"):
                        link = site["url"] + link

                    if link in links_encontrados:
                        continue

                    # filtrar Bahia direto na listagem
                    if not any(f in location for f in BA_FILTER):
                        continue

                    links_encontrados.add(link)

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link,
                        "ativa": "1"
                    })
                    print(f"   ↪ Encontrada: {titulo} ({location})")

                except Exception:
                    continue

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
    print(f"\n✅ Finalizado. Total de vagas BA ativas: {len(links_encontrados)}")

if __name__ == "__main__":
    main()






