#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os
import time

CSV_FILE = "vagas.csv"

SITES = [
    {
        "empresa": "BYD",
        "url": "https://bydbrasil.gupy.io",
        "selector": 'a[href*="/jobs/"]'
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io",
        "selector": 'a[href*="/jobs/"]'
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

def vaga_eh_bahia(titulo):
    titulo = titulo.upper()
    return any(f in titulo for f in FILTRO_BA)

def salvar_vagas(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "titulo", "empresa", "link", "ativa"]
        )
        writer.writeheader()
        writer.writerows(vagas)

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

            scroll_sem_novidade = 0

            while scroll_sem_novidade < 2:
                cards = page.locator(site["selector"])
                count = cards.count()
                novos = 0

                print(f"[{site['empresa']}] cards visíveis: {count}")

                for i in range(count):
                    try:
                        el = cards.nth(i)
                        titulo = el.inner_text(timeout=2000).strip()
                        link = el.get_attribute("href")

                        if not titulo or not link:
                            continue
                        if not vaga_eh_bahia(titulo):
                            continue

                        if not link.startswith("http"):
                            link = site["url"] + link

                        if link in links_encontrados:
                            continue

                        links_encontrados.add(link)
                        novos += 1

                        vagas.append({
                            "id": str(uuid.uuid4())[:8],
                            "titulo": titulo,
                            "empresa": site["empresa"],
                            "link": link,
                            "ativa": "1"
                        })

                    except Exception:
                        continue

                if novos == 0:
                    scroll_sem_novidade += 1
                else:
                    scroll_sem_novidade = 0

                # 🔽 scroll real
                page.mouse.wheel(0, 5000)
                time.sleep(2)

        browser.close()

    # 🔄 desativar vagas antigas
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    vagas.append(vaga)

    salvar_vagas(vagas)
    print(f"\n✅ Finalizado. Vagas BA ativas: {len(links_encontrados)}")

if __name__ == "__main__":
    main()




