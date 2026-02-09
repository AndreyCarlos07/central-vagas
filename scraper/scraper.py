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
        "selector": 'a[href*="/jobs/"]'
    }
]

# 📍 FILTRO BAHIA (usado DENTRO da página da vaga)
FILTRO_BA = [
    " BA",
    "BAHIA",
    "SALVADOR",
    "CAMAÇARI",
    "LAURO DE FREITAS",
    "FEIRA DE SANTANA",
    "DIAS D'ÁVILA"
]


def vaga_eh_bahia(page, link):
    try:
        page.goto(link, timeout=60000)
        page.wait_for_timeout(2000)

        texto = page.inner_text("body").upper()
        return any(f in texto for f in FILTRO_BA)

    except Exception:
        return False


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

            page_num = 0

            while True:
                url = f"{site['url']}?page={page_num}"
                page.goto(url, timeout=60000)
                page.wait_for_timeout(3000)

                cards = page.locator(site["selector"])
                count = cards.count()

                print(f"[{site['empresa']}] página {page_num} → {count} cards")

                if count == 0:
                    break  # fim real da paginação

                for i in range(count):
                    try:
                        el = cards.nth(i)
                        titulo = el.inner_text(timeout=3000).strip()
                        link = el.get_attribute("href")

                        if not titulo or not link:
                            continue

                        if not link.startswith("http"):
                            link = site["url"] + link

                        if link in links_encontrados:
                            continue  # evita duplicação

                        print(f"   ↪ Verificando: {titulo}")

                        if not vaga_eh_bahia(page, link):
                            continue

                        links_encontrados.add(link)

                        vagas.append({
                            "id": str(uuid.uuid4())[:8],
                            "titulo": titulo,
                            "empresa": site["empresa"],
                            "link": link,
                            "ativa": "1"
                        })

                    except Exception:
                        continue

                page_num += 1

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





