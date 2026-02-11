#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import re
import os

CSV_FILE = "vagas.csv"

# ===========================
# CREDENCIAIS VAGAS.COM
# ===========================

VAGAS_EMAIL = os.getenv("VAGAS_EMAIL")
VAGAS_SENHA = os.getenv("VAGAS_SENHA")

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
        "empresa": "BRIDGESTONE",
        "url": "https://bridgestone.wd5.myworkdayjobs.com/pt-BR/LATAMExternalCareers/",
        "tipo": "workday",
        "base": "https://bridgestone.wd5.myworkdayjobs.com",
        "pesquisas": ["Bahia"]
    },
    {
        "empresa": "DOW",
        "url": "https://dow.wd1.myworkdayjobs.com/pt-BR/ExternalCareers",
        "tipo": "workday",
        "base": "https://dow.wd1.myworkdayjobs.com",
        "pesquisas": ["Aratu", "Catu"]
    },
    {
        "tipo": "vagas",
        "url": "https://www.vagas.com.br/login-candidatos",
        "empresas_desejadas": ["ZEENTECH", "AZ CONSULT", "WHITE MARTINS"],
        "cidade": "Camaçari - BA"
    }
]

PALAVRAS_BA = ["BAHIA", "SALVADOR", "CAMAÇARI", "LAURO"]

# ===========================
# VAGAS.COM
# ===========================
def coletar_vagas_com(page, site):
    vagas = []

    print("🔐 Fazendo login no Vagas.com")

    page.goto(site["url"], timeout=60000)
    page.wait_for_timeout(4000)

    # login
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', VAGAS_EMAIL)
    page.fill('input[type="password"]', VAGAS_SENHA)
    page.click('button[type="submit"]')

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)

    # clicar em filtrar
    page.click("text=Filtrar")
    page.wait_for_timeout(3000)

    # desmarcar recomendadas
    switch = page.locator('[data-testid="switch-mostrar-vagas-recomendadas"]')
    if switch.is_checked():
        switch.click()
        page.wait_for_timeout(2000)

        page.click('[data-testid="button-vagas-nao-recomendadas"]')
        page.wait_for_timeout(3000)

    # digitar cidade
    page.fill('input[placeholder="Digite uma cidade"]', site["cidade"])
    page.wait_for_timeout(2000)

    # selecionar primeira opção do dropdown
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")

    page.wait_for_timeout(2000)

    page.click('[data-testid="button-mostrar-vagas"]')
    page.wait_for_timeout(5000)

    # scroll
    for _ in range(10):
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(2000)

    cards = page.locator("div[role='button']")

    for i in range(cards.count()):
        try:
            texto = cards.nth(i).inner_text()

            # verifica empresa desejada
            empresa_match = any(
                emp in texto.upper() for emp in site["empresas_desejadas"]
            )

            if not empresa_match:
                continue

            # extrai código da vaga (ex: 2777845)
            codigo = re.search(r"\((\d+)\)", texto)
            if not codigo:
                continue

            codigo_vaga = codigo.group(1)

            # extrai título
            linhas = texto.split("\n")
            titulo = linhas[1] if len(linhas) > 1 else "Sem título"

            link = f"https://www.vagas.com.br/vagas/v{codigo_vaga}"

            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": "VAGAS.COM",
                "link": link
            })

        except:
            continue

    print(f"📌 VAGAS.COM: {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# WORKDAY
# ===========================
def coletar_workday(page, site):
    vagas = []
    links = set()

    for termo in site.get("pesquisas", []):
        page.goto(site["url"])
        page.wait_for_timeout(4000)

        page.fill('input[data-automation-id="keywordSearchInput"]', termo)
        page.click('button[data-automation-id="keywordSearchButton"]')
        page.wait_for_timeout(5000)

        for _ in range(10):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)

        cards = page.locator('a[data-automation-id="jobTitle"]')

        for i in range(cards.count()):
            el = cards.nth(i)
            titulo = el.inner_text()
            link = el.get_attribute("href")

            if not link.startswith("http"):
                link = site["base"] + link

            if link in links:
                continue

            links.add(link)

            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": site["empresa"],
                "link": link
            })

    print(f"📌 {site['empresa']} WORKDAY: {len(vagas)} vagas")
    return vagas

# ===========================
# GUPY
# ===========================
def coletar_gupy(page, site):
    vagas = []

    page.goto(site["url"])
    page.wait_for_timeout(5000)

    for _ in range(20):
        page.mouse.wheel(0, 8000)
        page.wait_for_timeout(2000)

    cards = page.locator('a[href*="/jobs/"]')

    for i in range(cards.count()):
        el = cards.nth(i)
        titulo = el.inner_text()
        link = el.get_attribute("href")

        if not link.startswith("http"):
            link = site["url"] + link

        if any(p in titulo.upper() for p in PALAVRAS_BA):
            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": site["empresa"],
                "link": link
            })

    print(f"📌 {site['empresa']} GUPY: {len(vagas)} vagas")
    return vagas

# ===========================
# SALVAR CSV
# ===========================
def salvar_vagas(vagas):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "titulo", "empresa", "link"])
        writer.writeheader()
        writer.writerows(vagas)

# ===========================
# MAIN
# ===========================
def main():
    todas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:
            if site["tipo"] == "gupy":
                todas.extend(coletar_gupy(page, site))

            elif site["tipo"] == "workday":
                todas.extend(coletar_workday(page, site))

            elif site["tipo"] == "vagas":
                todas.extend(coletar_vagas_com(page, site))

        browser.close()

    salvar_vagas(todas)

    print("✅ Finalizado")
    print(f"📌 Total coletado: {len(todas)}")

if __name__ == "__main__":
    main()
