#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os

CSV_FILE = "vagas.csv"

EMPRESAS = [
    {
        "empresa": "BYD",
        "slug": "bydbrasil",
        "company_id": 11858
    },
    {
        "empresa": "MOTIVA",
        "slug": "motiva",
        "company_id": 17147
    }
]

FILTRO_BA = [
    "BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]


def eh_bahia(locations):
    texto = " ".join(locations).upper()
    return any(f in texto for f in FILTRO_BA)


def carregar_antigas():
    vagas = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                vagas[row["link"]] = row
    return vagas


def salvar(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "ativa"]
        )
        writer.writeheader()
        for v in vagas:
            writer.writerow(v)


def main():
    vagas_finais = []
    encontrados = set()
    antigas = carregar_antigas()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for emp in EMPRESAS:
            print(f"\n🔎 Buscando vagas da {emp['empresa']}")
            page_num = 0

            while True:
                api_url = "api_url = "https://api.gupy.io/api/v1/jobs/search"

                payload = {
                    "companyId": emp["company_id"],
                    "page": page_num,
                    "pageSize": 10,
                    "filters": {}
                }

                resp = page.request.post(
                    api_url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Referer": f"https://{emp['slug']}.gupy.io/"
                    },
                    data=payload
                )

                if not resp.ok:
                    print(f"❌ Erro HTTP {resp.status} na página {page_num}")
                    break

                data = resp.json()
                jobs = data.get("data", [])

                if not jobs:
                    print("⏹️ Fim da paginação")
                    break

                print(f"[{emp['empresa']}] página {page_num}: {len(jobs)} vagas")

                for job in jobs:
                    titulo = job.get("name", "")
                    link = job.get("careerPageUrl", "")
                    locations = job.get("locations", [])

                    if not eh_bahia(locations):
                        continue

                    encontrados.add(link)
                    antiga = antigas.get(link)

                    vagas_finais.append({
                        "id": antiga["id"] if antiga else str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": emp["empresa"],
                        "link": link,
                        "ativa": "1"
                    })

                page_num += 1

        browser.close()

    # marca antigas como inativas
    for link, vaga in antigas.items():
        if link not in encontrados:
            vaga["ativa"] = "0"
            vagas_finais.append(vaga)

    salvar(vagas_finais)
    print(f"\n✅ Finalizado. Vagas BA ativas: {len(encontrados)}")


if __name__ == "__main__":
    main()








