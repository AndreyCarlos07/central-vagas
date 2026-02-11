#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid

CSV_FILE = "vagas.csv"

# ===========================
# SITES CONFIGURADOS
# ===========================
SITES = [
    {
        "empresa": "BYD",
        "url": "https://bydbrasil.gupy.io",
        "tipo": "gupy"
    },
    {
        "empresa": "MOTIVA",
        "url": "https://motiva.gupy.io",
        "tipo": "gupy"
    },
    {
        "empresa": "BRIDGESTONE",
        "url": "https://bridgestone.wd5.myworkdayjobs.com/pt-BR/LATAMExternalCareers",
        "tipo": "workday",
        "base": "https://bridgestone.wd5.myworkdayjobs.com",
        "pesquisas": ["Bahia"]
    },
    {
        "empresa": "DOW",
        "url": "https://dow.wd1.myworkdayjobs.com/pt-BR/ExternalCareers",
        "tipo": "workday",
        "base": "https://dow.wd1.myworkdayjobs.com",
        "pesquisas": ["Aratu"]
    }
]

# 📍 filtro Bahia (somente GUPY)
PALAVRAS_BA = ["BAHIA", "SALVADOR", "CAMAÇARI", "LAURO", "FEIRA", "DIAS D'ÁVILA"]

# ===========================
# GUPY
# ===========================
def carregar_scroll_gupy(page):
    last_count = 0
    for _ in range(40):
        page.wait_for_timeout(2000)
        cards = page.locator('a[href*="/jobs/"]')
        count = cards.count()
        if count == last_count:
            break
        last_count = count
        page.mouse.wheel(0, 8000)

def coletar_gupy(page, site):
    vagas = []

    page.goto(site["url"], timeout=60000)
    page.wait_for_timeout(4000)

    carregar_scroll_gupy(page)

    pagina_atual = 1

    while True:
        page.wait_for_timeout(3000)
        cards = page.locator('a[href*="/jobs/"]')

        for i in range(cards.count()):
            el = cards.nth(i)
            try:
                titulo = el.inner_text().strip()
                link = el.get_attribute("href")

                if not link.startswith("http"):
                    link = site["url"] + link

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link
                })
            except:
                continue

        proxima = page.locator(
            f'button[data-testid="pagination-page-button"]:has-text("{pagina_atual + 1}")'
        )

        if proxima.count() == 0:
            break

        proxima.first.click()
        pagina_atual += 1

    print(f"📌 {site['empresa']} (GUPY): {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# WORKDAY (pesquisa por empresa)
# ===========================
def coletar_workday(page, site):
    vagas = []
    links_coletados = set()

    for termo in site.get("pesquisas", []):
        print(f"🔎 {site['empresa']} pesquisando: {termo}")

        page.goto(site["url"], timeout=60000)
        page.wait_for_timeout(5000)

        page.fill('input[data-automation-id="keywordSearchInput"]', termo)
        page.click('button[data-automation-id="keywordSearchButton"]')

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # scroll para carregar todas as vagas
        for _ in range(20):
            page.mouse.wheel(0, 6000)
            page.wait_for_timeout(2000)

        cards = page.locator('a[data-automation-id="jobTitle"]')

        for i in range(cards.count()):
            el = cards.nth(i)
            try:
                titulo = el.inner_text().strip()
                link = el.get_attribute("href")

                if not link.startswith("http"):
                    link = site["base"] + link

                if link in links_coletados:
                    continue

                links_coletados.add(link)

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo,
                    "empresa": site["empresa"],
                    "link": link
                })
            except:
                continue

    print(f"📌 {site['empresa']} (WORKDAY): {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# FILTRO GUPY
# ===========================
def filtrar_gupy_bahia(vagas):
    filtradas = [
        vaga for vaga in vagas
        if any(palavra in vaga["titulo"].upper() for palavra in PALAVRAS_BA)
    ]
    print(f"📌 GUPY após filtro Bahia: {len(filtradas)}")
    return filtradas

# ===========================
# SALVAR CSV
# ===========================
def salvar_vagas(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "titulo", "empresa", "link"])
        writer.writeheader()
        for vaga in vagas:
            writer.writerow(vaga)

# ===========================
# MAIN
# ===========================
def main():
    todas_vagas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            print(f"\n🔎 Buscando vagas da {site['empresa']}")

            if site["tipo"] == "gupy":
                vagas = coletar_gupy(page, site)
                vagas = filtrar_gupy_bahia(vagas)

            elif site["tipo"] == "workday":
                vagas = coletar_workday(page, site)

            else:
                vagas = []

            todas_vagas.extend(vagas)

        browser.close()

    salvar_vagas(todas_vagas)

    print("\n✅ Finalizado")
    print(f"📌 Total salvo no CSV: {len(todas_vagas)}")


if __name__ == "__main__":
    main()
