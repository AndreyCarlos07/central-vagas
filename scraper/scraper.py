#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os

CSV_FILE = "vagas.csv"

# Empresas Gupy
EMPRESAS = [
    {
        "empresa": "BYD",
        "slug": "bydbrasil"
    },
    {
        "empresa": "MOTIVA",
        "slug": "motiva"
    }
]

# 📍 Palavras-chave para Bahia
FILTRO_BA = [
    " - BA",
    " BAHIA",
    " SALVADOR",
    " CAMAÇARI",
    " LAURO DE FREITAS",
    " FEIRA DE SANTANA",
    " DIAS D'ÁVILA"
]

def eh_bahia(texto):
    texto = texto.upper()
    return any(f in texto for f in FILTRO_BA)

def carregar_links_existentes():
    links = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                links.add(row["link"])
    return links

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
    links_antigos = carregar_links_existentes()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for emp in EMPRESAS:
            print(f"\n🔎 Buscando vagas da {emp['empresa']}")

            page_num = 0
            per_page = 10

            while True:
                api_url = (
                    f"https://{emp['slug']}.gupy.io/api/v1/jobs"
                    f"?page={page_num}&perPage={per_page}"
                )

                resp = page.request.get(
                    api_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
                        "Accept": "application/json",
                        "Referer": f"https://{emp['slug']}.gupy.io/"
                    }
                )

                if not resp.ok:
                    print(f"❌ Erro HTTP {resp.status} na página {page_num}")
                    break

                try:
                    data = resp.json()
                except Exception:
                    print(f"⚠️ Resposta não-JSON na página {page_num}, encerrando paginação")
                    break

                jobs = data.get("data", [])

                if not jobs:
                    print(f"ℹ️ Fim das vagas na página {page_num}")
                    break

                print(f"[{emp['empresa']}] página {page_num} → {len(jobs)} vagas")

                for job in jobs:
                    titulo = job.get("name", "").strip()
                    link = job.get("careerPageUrl", "").strip()

                    if not titulo or not link:
                        continue

                    if not eh_bahia(titulo):
                        continue

                    if link in links_encontrados:
                        continue

                    links_encontrados.add(link)

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": emp["empresa"],
                        "link": link,
                        "ativa": "1"
                    })

                page_num += 1

        browser.close()

    # 🔄 marcar vagas antigas como inativas
    for link_antigo in links_antigos:
        if link_antigo not in links_encontrados:
            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": "",
                "empresa": "",
                "link": link_antigo,
                "ativa": "0"
            })

    salvar_vagas(vagas)

    print(f"\n✅ Scraping finalizado")
    print(f"➡️ Vagas BA ativas: {len(links_encontrados)}")

if __name__ == "__main__":
    main()









