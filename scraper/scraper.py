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
        "location_selector": ".job-card-location"
    },
    {
        "empresa": "BYD",
        "url": "https://byd.gupy.io/",
        "job_selector": 'a[href*="/jobs/"]',
        "location_selector": ".job-card-location"
    },
    {
        "empresa": "Motiva",
        "url": "https://motiva.gupy.io/",
        "job_selector": 'a[href*="/jobs/"]',
        "location_selector": ".job-card-location"
    }
]

# Estados/locais da Bahia
BA_FILTER = [
    "BA", "BAHIA", "SALVADOR", "CAMAÇARI",
    "LAURO DE FREITAS", "FEIRA DE SANTANA", "DIAS D'ÁVILA"
]

def carregar_vagas_existentes():
    """Carrega vagas existentes no CSV e retorna um dict por link"""
    vagas_existentes = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                vagas_existentes[vaga["link"]] = vaga
    return vagas_existentes

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
    vagas_existentes = carregar_vagas_existentes()
    vagas_novas = []
    links_encontrados = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['empresa']}")
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(3000)

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

                    # filtrar Bahia
                    if not any(f in location for f in BA_FILTER):
                        continue

                    links_encontrados.add(link)

                    # Se já existe, só mantém ativa
                    if link in vagas_existentes:
                        vaga = vagas_existentes[link]
                        vaga["ativa"] = "1"
                        vagas_novas.append(vaga)
                    else:
                        # nova vaga
                        vaga = {
                            "id": str(uuid.uuid4())[:8],
                            "titulo": titulo,
                            "empresa": site["empresa"],
                            "link": link,
                            "ativa": "1"
                        }
                        vagas_novas.append(vaga)
                        print(f"   ↪ Encontrada: {titulo} ({location})")

                except Exception:
                    continue

        browser.close()

    # 🔄 marca vagas antigas como inativas
    for link, vaga in vagas_existentes.items():
        if link not in links_encontrados:
            vaga["ativa"] = "0"
            vagas_novas.append(vaga)

    salvar_vagas(vagas_novas)
    print(f"\n✅ Finalizado. Total de vagas BA ativas: {len(links_encontrados)}")

if __name__ == "__main__":
    main()






