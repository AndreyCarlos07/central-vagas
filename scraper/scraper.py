#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os

CSV_FILE = "vagas.csv"

EMPRESAS = [
    {"empresa": "BYD", "slug": "bydbrasil"},
    {"empresa": "MOTIVA", "slug": "motiva"},
]

FILTRO_BA = [
    " - BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]

def titulo_eh_ba(titulo: str) -> bool:
    t = titulo.upper()
    return any(f in t for f in FILTRO_BA)

def carregar_csv_existente():
    vagas = {}
    if not os.path.exists(CSV_FILE):
        return vagas

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vagas[row["link"]] = row
    return vagas

def salvar_csv(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "ativa"]
        )
        writer.writeheader()
        writer.writerows(vagas)

def main():
    vagas_antigas = carregar_csv_existente()
    vagas_novas = {}
    links_ativos = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for emp in EMPRESAS:
            print(f"\n🔎 Buscando vagas da {emp['empresa']}")
            page_num = 0

            while True:
                api_url = (
                    f"https://{emp['slug']}.gupy.io/api/v1/jobs"
                    f"?page={page_num}&perPage=10"
                )

                resp = page.request.get(api_url)
                data = resp.json()

                jobs = data.get("data", [])
                print(f"[{emp['empresa']}] página {page_num} → {len(jobs)} vagas")

                if not jobs:
                    break

                for job in jobs:
                    titulo = job["name"]
                    if not titulo_eh_ba(titulo):
                        continue

                    link = f"https://{emp['slug']}.gupy.io/jobs/{job['id']}"
                    links_ativos.add(link)

                    if link in vagas_antigas:
                        vaga = vagas_antigas[link]
                        vaga["ativa"] = "1"
                    else:
                        vaga = {
                            "id": str(uuid.uuid4())[:8],
                            "titulo": titulo,
                            "empresa": emp["empresa"],
                            "link": link,
                            "ativa": "1"
                        }

                    vagas_novas[link] = vaga

                page_num += 1

        browser.close()

    # 🔻 Desativar vagas que sumiram
    for link, vaga in vagas_antigas.items():
        if link not in links_ativos:
            vaga["ativa"] = "0"
            vagas_novas[link] = vaga

    salvar_csv(list(vagas_novas.values()))
    print(f"\n✅ Finalizado. Total de vagas BA ativas: {len(links_ativos)}")

if __name__ == "__main__":
    main()










