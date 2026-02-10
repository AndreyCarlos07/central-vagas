#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright, TimeoutError
import csv
import uuid

CSV_FILE = "vagas.csv"

SITES = [
    {"empresa": "BYD", "url": "https://bydbrasil.gupy.io", "selector": 'a[href*="/jobs/"]'},
    {"empresa": "MOTIVA", "url": "https://motiva.gupy.io", "selector": 'a[href*="/jobs/"]'}
]

# 📍 palavras-chave para filtrar vagas na BAHIA
FILTRO_BA = [
    " BAHIA",
    " SALVADOR",
    " CAMAÇARI",
    " LAURO DE FREITAS",
    " FEIRA DE SANTANA",
    " DIAS D'ÁVILA"
]

# ===========================
# FUNÇÃO: CARREGAR TODAS AS VAGAS (scroll)
# ===========================
def carregar_todas_vagas(page):
    last_count = 0
    for _ in range(40):  # limite de segurança
        page.wait_for_timeout(2000)
        cards = page.locator('a[href*="/jobs/"]')
        count = cards.count()
        print(f"🔄 vagas renderizadas: {count}")
        if count == last_count:
            break
        last_count = count
        page.mouse.wheel(0, 8000)

# ===========================
# FUNÇÃO: NAVEGAR PÁGINAS E COLETAR VAGAS
# ===========================
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
                if not link.startswith("http"):
                    link = site["url"] + link

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link
                })
            except Exception:
                continue

        proxima_pagina = page.locator(
            f'button[data-testid="pagination-page-button"]:has-text("{pagina_atual + 1}")'
        )
        if proxima_pagina.count() == 0:
            break
        proxima_pagina.first.click()
        pagina_atual += 1

    print(f"📌 Total de vagas coletadas nesta empresa: {len(vagas)}")
    return vagas

# ===========================
# FUNÇÃO: FILTRAR VAGAS POR PALAVRAS-CHAVE
# ===========================
def filtrar_vagas_bahia(vagas):
    vagas_ba = []
    for vaga in vagas:
        for termo in FILTRO_BA:
            if termo.upper() in vaga["titulo"].upper():
                vagas_ba.append(vaga)
                break
    print(f"📌 Total de vagas filtradas para Bahia: {len(vagas_ba)}")
    return vagas_ba

# ===========================
# FUNÇÃO: SALVAR CSV
# ===========================
def salvar_vagas(vagas, arquivo=CSV_FILE):
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "titulo", "empresa", "link"])
        writer.writeheader()
        for vaga in vagas:
            writer.writerow(vaga)

# ===========================
# FUNÇÃO PRINCIPAL
# ===========================
def main():
    todas_vagas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['empresa']}")
            page.goto(site["url"], timeout=60000)
            page.wait_for_timeout(4000)

            # força o carregamento de todas as vagas
            carregar_todas_vagas(page)

            # coleta todas as vagas
            vagas_empresa = navegar_todas_paginas(page, site)
            todas_vagas.extend(vagas_empresa)

        browser.close()

    # filtra apenas vagas da Bahia
    vagas_ba = filtrar_vagas_bahia(todas_vagas)

    # salva no CSV
    salvar_vagas(vagas_ba)
    print("\n✅ Finalizado")
    print(f"📌 Vagas BA encontradas: {len(vagas_ba)}")

if __name__ == "__main__":
    main()
