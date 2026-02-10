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

# 🎯 Estado alvo para filtrar
ESTADO_ALVO = "Bahia (BA)"


# ✅ FUNÇÃO CERTA — FORÇA O REACT A CARREGAR TUDO
def carregar_todas_vagas(page):
    last_count = 0
    for _ in range(40):  # limite de segurança
        page.wait_for_timeout(2000)
        cards = page.locator('a[href*="/jobs/"]')
        count = cards.count()
        print(f"🔄 vagas renderizadas: {count}")
        if count == last_count:
            break  # não entrou vaga nova → acabou
        last_count = count
        page.mouse.wheel(0, 8000)


# ✅ FUNÇÃO NOVA — NAVEGAÇÃO POR PÁGINAS COM FILTRO DE ESTADO
def navegar_todas_paginas(page, site):
    pagina_atual = 1
    vagas = []

    while True:
        print(f"📄 Página {pagina_atual}")
        page.wait_for_timeout(3000)

        cards = page.locator(site["selector"])
        for i in range(cards.count()):
            el = cards.nth(i)
            try:
                titulo = el.inner_text(timeout=3000).strip()
                link = el.get_attribute("href")

                if not titulo or not link:
                    continue

                # ✅ pega o estado real do card (Motiva)
                estado_card = ""
                try:
                    estado_card = el.locator("div.common-select__single-value").inner_text(timeout=1000).strip()
                except Exception:
                    pass  # alguns cards podem não ter o estado no mesmo padrão

                # 🎯 filtra pelo estado correto
                if site["empresa"] == "MOTIVA" and ESTADO_ALVO != estado_card:
                    continue

                if not link.startswith("http"):
                    link = site["url"] + link

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link,
                    "ativa": "1"
                })

            except Exception:
                continue

        # tenta achar o botão da próxima página
        proxima_pagina = page.locator(
            f'button[data-testid="pagination-page-button"]:has-text("{pagina_atual + 1}")'
        )
        if proxima_pagina.count() == 0:
            break  # acabou as páginas
        proxima_pagina.first.click()
        pagina_atual += 1

    print(f"📌 Total de vagas coletadas nesta empresa: {len(vagas)}")
    return vagas


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
    todas_vagas = []
    links_encontrados = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['empresa']}")
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(4000)

            carregar_todas_vagas(page)
            vagas = navegar_todas_paginas(page, site)

            for vaga in vagas:
                links_encontrados.add(vaga["link"])
                todas_vagas.append(vaga)

        browser.close()

    # 🔄 desativa vagas que sumiram do site
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["link"] not in links_encontrados:
                    vaga["ativa"] = "0"
                    todas_vagas.append(vaga)

    salvar_vagas(todas_vagas)

    print("\n✅ Finalizado")
    print(f"📌 Vagas BA ativas encontradas: {len(links_encontrados)}")


if __name__ == "__main__":
    main()
