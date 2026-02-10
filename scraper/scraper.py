#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os
import time
import requests

CSV_FILE = "vagas.csv"

EMPRESAS = [
    {
        "empresa": "BYD",
        "slug": "bydbrasil",
        "company_id": 1181
    },
    {
        "empresa": "MOTIVA",
        "slug": "motiva",
        "company_id": 3202
    }
]

FILTRO_BA = [
    " BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]

API_URL = "https://api.gupy.io/api/v1/jobs/search"


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
        context = browser.new_context()
        page = context.new_page()

        for emp in EMPRESAS:
            print(f"\n🔎 Buscando vagas da {emp['empresa']}")

            # 1️⃣ abre a página da empresa (gera sessão + cookies válidos)
            page.goto(f"https://{emp['slug']}.gupy.io/", timeout=60000)
            page.wait_for_timeout(5000)

            # 🔑 cookies reais da sessão
            cookies = {
                c["name"]: c["value"]
                for c in context.cookies()
            }

            page_num = 0

            while True:
                body = {
                    "page": page_num,
                    "pageSize": 10,
                    "companyId": emp["company_id"]
                }

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Origin": f"https://{emp['slug']}.gupy.io",
                    "Referer": f"https://{emp['slug']}.gupy.io/"
                }

                resp = requests.post(
                    API_URL,
                    json=body,
                    headers=headers,
                    cookies=cookies,
                    timeout=30
                )

                if not resp.ok:
                    print(f"❌ Erro HTTP {resp.status_code} na página {page_num}")
                    break

                data = resp.json()
                jobs = data.get("data", [])

                if not jobs:
                    print("⏹️ Fim da paginação")
                    break

                print(f"[{emp['empresa']}] página {page_num}: {len(jobs)} vagas")

                for job in jobs:
                    titulo = job.get("name", "")
                    link = job.get("jobUrl", "")

                    if not titulo or not link:
                        continue

                    titulo_upper = titulo.upper()
                    if not any(f in titulo_upper for f in FILTRO_BA):
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
                time.sleep(1)  # evita rate-limit

        browser.close()

    # 🔄 Marca vagas antigas como inativas
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    salvar_vagas(vagas)

    print(f"\n✅ Finalizado")
    print(f"📌 Vagas BA ativas encontradas: {len(links_encontrados)}")


if __name__ == "__main__":
    main()




