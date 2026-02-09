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
        "selector": 'a[href*="/jobs/"]',
        "local_selector": ".sc-dlfnbm"  # exemplo: onde aparece a cidade/estado no card
    }
]

# 🏖️ Lista de locais da BA
LOC_BA = ["BAHIA", "SALVADOR", "CAMAÇARI", "LAURO DE FREITAS", "FEIRA DE SANTANA", "DIAS D'ÁVILA"]


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
            page.wait_for_timeout(2000)

            # Opcional: aplicar filtro de Estado, se o site permitir
            if page.query_selector("#state-select"):
                page.fill("#state-select", "Bahia")
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)

            page_num = 0
            while True:
                # recarregar a página ou navegar na paginação
                url = f"{site['url']}?page={page_num}"
                page.goto(url, timeout=60000)
                page.wait_for_timeout(2000)

                cards = page.locator(site["selector"])
                count = cards.count()
                print(f"[{site['empresa']}] página {page_num} → {count} cards")

                if count == 0:
                    break

                for i in range(count):
                    try:
                        el = cards.nth(i)
                        titulo = el.inner_text(timeout=2000).strip()
                        link = el.get_attribute("href")

                        if not link.startswith("http"):
                            link = site["url"] + link

                        # pegar o local direto do card
                        local_text = el.locator(site["local_selector"]).inner_text(timeout=2000).upper()

                        # filtrar por Bahia
                        if not any(loc in local_text for loc in LOC_BA):
                            continue

                        if link in links_encontrados:
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






