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

# 📍 Filtro Bahia
FILTRO_BA = [
    "BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]


def vaga_eh_bahia(locations):
    texto = " ".join(locations).upper()
    return any(f in texto for f in FILTRO_BA)


def carregar_links_antigos():
    links = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                links[row["link"]] = row
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
    vagas_finais = []
    links_encontrados = set()
    vagas_antigas = carregar_links_antigos()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for emp in EMPRESAS:
            print(f"\n🔎 Buscando vagas da {emp['empresa']}")

            page_num = 0
            per_page = 10

            while True:
                api_url = (
                    "https://portal.api.gupy.io/api/v1/jobs"
                    f"?careerPageSlug={emp['slug']}"
                    f"&page={page_num}"
                    f"&perPage={per_page}"
                )

                resp = page.request.get(
                    api_url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
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
                    print("⚠️ Resposta não-JSON, encerrando paginação")
                    break

                jobs = data.get("data", [])

                if not jobs:
                    print(f"⏹️ Fim das vagas da {emp['empresa']}")
                    break

                print(f"[{emp['empresa']}] página {page_num} → {len(jobs)} vagas")

                for job in jobs:
                    titulo = job.get("name", "").strip()
                    link = job.get("careerPageUrl", "")
                    locations = job.get("locations", [])

                    if not titulo or not link:
                        continue

                    if not vaga_eh_bahia(locations):
                        continue

                    links_encontrados.add(link)

                    vaga_antiga = vagas_antigas.get(link)

                    vagas_finais.append({
                        "id": vaga_antiga["id"] if vaga_antiga else str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": emp["empresa"],
                        "link": link,
                        "ativa": "1"
                    })

                page_num += 1

        browser.close()

    # 🔄 marcar vagas antigas como inativas
    for link, vaga in vagas_antigas.items():
        if link not in links_encontrados:
            vaga["ativa"] = "0"
            vagas_finais.append(vaga)

    salvar_vagas(vagas_finais)

    print(f"\n✅ Finalizado. Total vagas BA ativas: {len(links_encontrados)}")


if __name__ == "__main__":
    main()









