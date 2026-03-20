#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from playwright.sync_api import sync_playwright
import csv
import uuid
import os
from datetime import datetime

# ===========================
# DEBUG CONFIG
# ===========================
MODO_DEBUG = True  # 🔥 Troque para False quando quiser rodar tudo
EMPRESAS_DEBUG = ["INDORAMA VENTURES", "GERDAU"]

CSV_HISTORICO = "vagas.csv"
CSV_NOVAS = "vagas_novas.csv"

# ===========================
# CARREGAR HISTÓRICO
# ===========================
def carregar_historico():
    vagas = []
    links_existentes = set()

    if os.path.exists(CSV_HISTORICO):
        with open(CSV_HISTORICO, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vagas.append(row)
                links_existentes.add(row["link"])

    return vagas, links_existentes


# ===========================
# SALVAR CSV
# ===========================
def salvar_csv(arquivo, vagas):
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "titulo", "empresa", "link", "data_coleta"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vaga in vagas:
            writer.writerow(vaga)


# ===========================
# SITES CONFIGURADOS
# ===========================
SITES = [
    {"empresa": "BYD", "url": "https://bydbrasil.gupy.io", "tipo": "gupy"},
    {"empresa": "MOTIVA", "url": "https://motiva.gupy.io", "tipo": "gupy"},
    {"empresa": "KORDSA", "url": "https://kordsa.gupy.io", "tipo": "gupy"},    
    {"empresa": "LM MOBILIDADE", "url": "https://lmvagas.gupy.io", "tipo": "gupy"},
    {"empresa": "VOTORANTIM CIMENTOS", "url": "https://votorantimcimentos.gupy.io", "tipo": "gupy"},
    {"empresa": "VOTORANTIM CIMENTOS", "url": "https://votorantimcimentostalentos.gupy.io", "tipo": "gupy"},
    {"empresa": "EUROCHEM", "url": "https://carreiras.gupy.io/", "tipo": "gupy"},
    {"empresa": "TIMAC AGRO", "url": "https://timacagro.gupy.io", "tipo": "gupy"},
    {"empresa": "CIBRA", "url": "https://cibra.gupy.io", "tipo": "gupy"},
    {"empresa": "TRONOX", "url": "https://tronoxbrasil.gupy.io", "tipo": "gupy"},
    {"empresa": "HERINGER", "url": "https://heringer.gupy.io", "tipo": "gupy"},
    {"empresa": "AXIA ENERGIA", "url": "https://axiaenergia.gupy.io", "tipo": "gupy"},
    {"empresa": "BRAVA ENERGIA", "url": "https://bravaenergia.gupy.io", "tipo": "gupy"},
    {"empresa": "ENGIE", "url": "https://engiebrasilenergia.gupy.io", "tipo": "gupy"},
    {"empresa": "ULTRAGAZ", "url": "https://vagasultragaz.gupy.io", "tipo": "gupy"},
    {"empresa": "COPA ENERGIA", "url": "https://carreirascopaenergia.gupy.io", "tipo": "gupy"},
    {"empresa": "PETRORECONCAVO", "url": "https://petroreconcavocarreiras.gupy.io", "tipo": "gupy"},
    {"empresa": "PERBRAS", "url": "https://perbras.gupy.io", "tipo": "gupy"},
    {"empresa": "ULTRACARGO", "url": "https://ultracargo.gupy.io", "tipo": "gupy"},
    {"empresa": "SOLAR COCA COLA", "url": "https://solarcocacola.gupy.io", "tipo": "gupy"},
    {"empresa": "M. DIAS BRANCO", "url": "https://mdiasbranco.gupy.io", "tipo": "gupy"},
    {"empresa": "ENGEPACK", "url": "https://engepack.gupy.io", "tipo": "gupy"},
    {"empresa": "AMBEV", "url": "https://ambev.gupy.io", "tipo": "gupy"},
    {"empresa": "FORTLEV", "url": "https://fortlev.gupy.io", "tipo": "gupy"},
    {"empresa": "GRUPO BOTICÁRIO", "url": "https://grupoboticario.gupy.io", "tipo": "gupy"},
    {"empresa": "VALGROUP", "url": "https://valgroup.gupy.io", "tipo": "gupy"},
    {"empresa": "ITAÚ UNIBANCO", "url": "https://vemproitau.gupy.io", "tipo": "gupy"},
    {"empresa": "KEMPETRO", "url": "https://vocenakempetro.gupy.io", "tipo": "gupy"},
    {"empresa": "WILSON SONS", "url": "https://wilsonsons.gupy.io", "tipo": "gupy"},
    {"empresa": "GLOBAL GROUP", "url": "https://globalgroup.gupy.io", "tipo": "gupy"},
    {"empresa": "CETREL", "url": "https://cetrel.gupy.io", "tipo": "gupy"},
    {"empresa": "MOHAWK", "url": "https://mohawk.gupy.io", "tipo": "gupy"},
    {"empresa": "MARTINS", "url": "https://logisticamartins.gupy.io", "tipo": "gupy"},
    {"empresa": "YPÊ", "url": "https://carreirasype.gupy.io", "tipo": "gupy"},
    {"empresa": "3CORAÇÕES", "url": "https://3coracoes.gupy.io", "tipo": "gupy"},
    {"empresa": "ALVOAR LÁCTEOS", "url": "https://alvoarlacteos.gupy.io", "tipo": "gupy"},
    {"empresa": "GRUPO MARATÁ", "url": "https://grupomarata.gupy.io", "tipo": "gupy"},
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
    },
    {
        "empresa": "MOSAIC",
        "url": "https://mosaic.wd5.myworkdayjobs.com/pt-BR/mosaic",
        "tipo": "workday",
        "base": "https://mosaic.wd5.myworkdayjobs.com",
        "pesquisas": ["Candeias"]
    },
    {
        "empresa": "NEOENERGIA",
        "url": "https://iberdrola.wd3.myworkdayjobs.com/pt-BR/Iberdrola",
        "tipo": "workday",
        "base": "https://iberdrola.wd3.myworkdayjobs.com",
        "pesquisas": ["Salvador"]
    },
    {
        "empresa": "NEXTPOWER",
        "url": "https://nextracker.wd5.myworkdayjobs.com/nextpower_careers",
        "tipo": "workday",
        "base": "https://nextracker.wd5.myworkdayjobs.com",
        "pesquisas": ["Simões Filho"]
    },
    {
        "empresa": "KIMBERLY-CLARK",
        "url": "https://kimberlyclark.wd1.myworkdayjobs.com/pt-BR/GLOBAL",
        "tipo": "workday",
        "base": "https://kimberlyclark.wd1.myworkdayjobs.com",
        "pesquisas": ["Camaçari"]
    },
    {
        "empresa": "BRACELL",
        "url": "https://averis.wd3.myworkdayjobs.com/pt-BR/RGE",
        "tipo": "workday",
        "base": "https://averis.wd3.myworkdayjobs.com",
        "pesquisas": ["Camaçari", "Alagoinhas"]
    },
    {
        "empresa": "INDORAMA VENTURES",
        "url": "https://ivlglobaliod.wd1.myworkdayjobs.com/pt-BR/Indovinya",
        "tipo": "workday",
        "base": "https://ivlglobaliod.wd1.myworkdayjobs.com",
        "pesquisas": ["Camaçari"]
    },
    {
        "empresa": "CONTINENTAL",
        "url": "https://jobs.continental.com/pt/#/?location=%7B%22title%22:%22Cama%C3%A7ari-Bahia,%20Brasil%22,%22type%22:%22location%22,%22coordinates%22:%7B%22latitude%22:-12.6998,%22longitude%22:-38.3261%7D%7D",
        "tipo": "continental"
    },
    {
        "empresa": "GERDAU",
        "url": "https://jobs.gerdau.com/search/?searchby=location&createNewAlert=false&q=&locationsearch=sim%C3%B5es+filho&geolocation=&optionsFacetsDD_country=&optionsFacetsDD_location=&optionsFacetsDD_title=&optionsFacetsDD_state=&optionsFacetsDD_city=&optionsFacetsDD_department=&optionsFacetsDD_customfield5=",
        "tipo": "gerdau"
    },
    {
        "empresa": "MERCADO LIVRE",
        "url": "https://mercadolibre.eightfold.ai/careers",
        "tipo": "eightfold"
    },
    {
    "empresa": "FORD",
    "url": "https://efds.fa.em5.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
    "tipo": "oracle",
    "filtros": [
    {
        "location": "Camacari%252C+BA%252C+Brazil",
        "locationId": "300000842085609"
    }
    ]
    },
    {
    "empresa": "BRASKEM",
    "url": "https://epiw.fa.la1.oraclecloud.com/hcmUI/CandidateExperience/pt-BR/sites/CX_1001/jobs",
    "tipo": "oracle",
    "filtros": [
    {
        "location": "CAMACARI%2C+BA%2C+Brasil",
        "locationId": "300000014753730"
    },
    {
        "location": "SALVADOR%252C+BA%252C+Brasil",
        "locationId": "300000014749824"
    }
    ]
    },
    {
        "empresa": "ACELEN",
        "url": "https://acelen.jobs.recrut.ai/#openings",
        "tipo": "recrutai",
        "cidade": "São Francisco do Conde / BA"
    },
    {
        "empresa": "MDC ENERGIA",
        "url": "https://mdcnossostalentos.jobs.recrut.ai/#openings",
        "tipo": "recrutai",
        "cidade": ["Camaçari / BA", "Salvador / BA"]
    },
    {
        "empresa": "SOTREQ",
        "url": "https://app.jobconvo.com/pt-br/careers/Sotreq/f6adee26-687e-4320-89a9-6ef13602f81d/?title=&state=&city=SIM%C3%95ES+FILHO",
        "tipo": "jobconvo"
    },
    {
        "empresa": "HEINEKEN",
        "url": "https://careers.theheinekencompany.com/Brazil/search", 
        "tipo": "heineken"
    }
]

# 📍 filtro Bahia (somente GUPY)
PALAVRAS_BA = ["BAHIA", "SALVADOR", "CAMAÇARI", "LAURO", "FEIRA", "DIAS D'ÁVILA", "CANDEIAS", "POJUCA - BA", "CATU", "SIMÕES FILHO", "ALAGOINHAS"]

# ===========================
# GUPY
# ===========================
def carregar_scroll_gupy(page):
    last_count = 0
    for _ in range(20):
        page.wait_for_timeout(1000)
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


def filtrar_gupy_bahia(vagas):
    filtradas = [
        vaga for vaga in vagas
        if any(p in vaga["titulo"].upper() for p in PALAVRAS_BA)
    ]
    print(f"📌 GUPY após filtro Bahia: {len(filtradas)}")
    return filtradas


# ===========================
# WORKDAY
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
# CONTINENTAL
# ===========================
def coletar_continental(page, site):
    vagas = []
    links_coletados = set()

    page.goto(site["url"], timeout=60000)
    page.wait_for_selector('a[href*="detail-page"]', timeout=15000)
    page.wait_for_load_state("networkidle")   

    # Scroll para garantir carregamento
    for _ in range(6):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1500)

    cards = page.locator('a[href*="detail-page/job-detail"]')

    for i in range(cards.count()):
        el = cards.nth(i)

        try:
            link = el.get_attribute("href")

            if not link.startswith("http"):
                link = "https://jobs.continental.com" + link

            link_limpo = link.split("?")[0]

            if link_limpo in links_coletados:
                continue

            links_coletados.add(link_limpo)

            titulo = el.inner_text().strip()

            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": site["empresa"],
                "link": link_limpo
            })

        except:
            continue

    print(f"📌 {site['empresa']} (PORTAL PROPRIO): {len(vagas)} vagas")
    return vagas

# ===========================
# GERDAU
# ===========================
def coletar_gerdau(page, site):
    vagas = []
    links_coletados = set()

    page.goto(site["url"], timeout=60000)

    # espera a página carregar minimamente
    page.wait_for_timeout(5000)

    # 🔥 tenta achar vagas por até 30s
    cards = None
    for _ in range(15):  # 15 tentativas (~30s)
        cards = page.locator('a.jobTitle-link')

        if cards.count() > 0:
            break

        print("⏳ aguardando vagas...")
        page.wait_for_timeout(2000)

    if not cards or cards.count() == 0:
        print("❌ nenhuma vaga encontrada")
        return vagas

    print("✅ vagas encontradas:", cards.count())

    for i in range(cards.count()):
        el = cards.nth(i)

        try:
            link = el.get_attribute("href")
            titulo = el.inner_text().strip()

            if not link or not titulo:
                continue

            if not link.startswith("http"):
                link = "https://jobs.gerdau.com" + link

            link_limpo = link.split("?")[0]

            if link_limpo in links_coletados:
                continue

            links_coletados.add(link_limpo)

            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": site["empresa"],
                "link": link_limpo
            })

        except:
            continue

    print(f"📌 {site['empresa']} (SCRAPING): {len(vagas)} vagas")
    return vagas
    

# ===========================
# EIGHTFOLD (MERCADO LIVRE)
# ===========================
def coletar_eightfold(page, site):
    vagas = []

    page.goto("https://mercadolibre.eightfold.ai/careers", timeout=60000)
    page.wait_for_load_state("networkidle")

    # Espera o campo aparecer
    page.wait_for_selector('input[data-testid="position-query-search-search"]', timeout=15000)

    # Digita Simões Filho
    page.fill('input[data-testid="position-query-search-search"]', "Simões Filho")
    page.keyboard.press("Enter")

    # Espera os resultados carregarem
    page.wait_for_selector('a[href*="/careers/job/"]', timeout=15000)
    page.wait_for_load_state("networkidle")

    # Coleta links
    links = page.locator('a[href*="/careers/job/"]')
    total = links.count()

    for i in range(total):
        titulo = links.nth(i).inner_text()
        link = links.nth(i).get_attribute("href")

        if link and not link.startswith("http"):
            link = "https://mercadolibre.eightfold.ai" + link

        vagas.append({
            "id": str(uuid.uuid4())[:8],
            "empresa": site["empresa"],
            "titulo": titulo.strip(),
            "link": link
        })

    print(f"📌 {site['empresa']} (EIGHTFOLD): {len(vagas)} vagas coletadas")
    return vagas


# ===========================
# ORACLE CLOUD
# ===========================
def coletar_oracle(page, site):
    vagas = []
    links_coletados = set()

    filtros = site.get("filtros", [])

    if not filtros:
        filtros = [None]  # caso não tenha filtro

    for filtro in filtros:

        if filtro:
            url_com_filtro = (
                site["url"]
                + f"?location={filtro['location']}"
                + f"&locationId={filtro['locationId']}"
                + "&locationLevel=city"
                + "&mode=location"
                + "&radius=25"
                + "&radiusUnit=KM"
            )
        else:
            url_com_filtro = site["url"]

        try:
            page.goto(url_com_filtro, timeout=60000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)

            print("URL carregada:", page.url)

            cards = page.locator("a.job-list-item__link")
            total = cards.count()

            print("Total de links encontrados:", total)

            for i in range(total):
                try:
                    card = cards.nth(i)
                    link = card.get_attribute("href")

                    if not link:
                        continue

                    link_limpo = link.split("?")[0]

                    if link_limpo in links_coletados:
                        continue

                    links_coletados.add(link_limpo)

                    page.goto(link_limpo, timeout=60000)
                    page.wait_for_load_state("networkidle")

                    titulo = page.locator("h1.job-details__title").inner_text().strip()

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link_limpo
                    })

                    page.go_back()
                    page.wait_for_load_state("networkidle")

                except Exception as e:
                    print("Erro ao processar vaga:", e)
                    continue

        except Exception as e:
            print(f"Erro ao acessar Oracle {site['empresa']}:", e)
            continue

    print(f"📌 {site['empresa']} (ORACLE): {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# RECRUT.AI
# ===========================
def coletar_recrutai(page, site):

    vagas = []
    links_coletados = set()

    page.goto(site["url"], timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)

    cidades = site.get("cidade")

    if isinstance(cidades, str):
        cidades = [cidades]

    for cidade in cidades:

        print(f"🔎 {site['empresa']} filtrando cidade: {cidade}")

        try:

            # abre dropdown
            page.locator("button.dropdown-toggle").nth(1).click()
            page.wait_for_timeout(800)

            # seleciona cidade
            page.locator(f"text={cidade}").first.click()
            page.wait_for_timeout(800)

            # clicar filtrar
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # coleta vagas da cidade
            cards = page.locator('a[href*="job/"]')
            total = cards.count()

            print(f"Total de vagas em {cidade}: {total}")

            for i in range(total):

                try:

                    link = cards.nth(i).get_attribute("href")

                    if not link:
                        continue

                    base_url = site["url"].split("#")[0]

                    if not base_url.endswith("/"):
                        base_url += "/"

                    link_completo = base_url + link

                    if link_completo in links_coletados:
                        continue

                    links_coletados.add(link_completo)

                    # abre vaga
                    page.goto(link_completo, timeout=60000)
                    page.wait_for_load_state("networkidle")

                    titulo = page.locator("h3").first.inner_text().strip()

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link_completo
                    })

                    # volta para lista
                    page.go_back()
                    page.wait_for_load_state("networkidle")

                except Exception as e:
                    print("Erro ao processar vaga:", e)
                    continue

        except Exception as e:
            print("Erro ao filtrar cidade:", e)
            continue

    print(f"📌 {site['empresa']} (RECRUT.AI): {len(vagas)} vagas coletadas")

    return vagas

# ===========================
# JOBCONVO (SOTREQ)
# ===========================
def coletar_jobconvo(page, site):
    vagas = []
    links_coletados = set()

    page.goto(site["url"], timeout=60000)
    page.wait_for_load_state("networkidle")

    print("URL carregada:", page.url)

    linhas = page.locator("tr.joblist")
    total = linhas.count()

    print("Total de vagas encontradas:", total)

    for i in range(total):
        try:
            linha = linhas.nth(i)

            link = linha.locator("a.text-primary").get_attribute("href")
            titulo = linha.locator("h2.jobname").inner_text().strip()

            if not link or link in links_coletados:
                continue

            links_coletados.add(link)

            vagas.append({
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "empresa": site["empresa"],
                "link": link.split("&")[0]  # limpa parâmetros extras
            })

        except Exception as e:
            print("Erro ao processar vaga:", e)
            continue

    print(f"📌 {site['empresa']} (JOBCONVO): {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# HEINEKEN
# ===========================
def coletar_heineken(page, site):
    vagas = []
    links_coletados = set()
    total_empresa = 0  # 👈 contador geral real

    page.goto(site["url"], timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    print("🔎 Verificando age gate...")

    # ===========================
    # 1️⃣ VERIFICA AGE GATE
    # ===========================
    if page.locator("#input-date-day").count() > 0:
        print("🔐 Age gate detectado. Preenchendo data...")

        page.fill("#input-date-day", "23")
        page.fill("#input-date-month", "09")
        page.fill("#input-date-year", "1993")

        page.click("#input-date-submit")
        page.wait_for_load_state("networkidle")
        page.goto("https://careers.theheinekencompany.com/Brazil/search")
        page.wait_for_selector("#location", timeout=30000)

    else:
        print("✅ Age gate não apareceu.")

    # ===========================
    # 2️⃣ CIDADES PARA FILTRAR
    # ===========================
    cidades = ["Alagoinhas", "Salvador"]

    for cidade in cidades:

        print(f"📍 Filtrando cidade: {cidade}")

        vagas_cidade = 0  # 👈 contador REAL dessa cidade

        try:
            page.fill("#location", cidade)
            page.click("#searchfilter-submit")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # ===========================
            # 3️⃣ COLETAR LINKS
            # ===========================
            links = page.locator("a[href*='/job/']")
            total = links.count()

            for i in range(total):
                try:
                    link = links.nth(i).get_attribute("href")

                    if not link:
                        continue

                    if link.startswith("/"):
                        link = "https://careers.theheinekencompany.com" + link

                    link_limpo = link.split("?")[0]

                    if link_limpo in links_coletados:
                        continue

                    links_coletados.add(link_limpo)

                    # título direto da listagem
                    titulo = links.nth(i).inner_text().strip()

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link_limpo
                    })

                    vagas_cidade += 1
                    total_empresa += 1

                except Exception as e:
                    print("Erro ao processar vaga:", e)
                    continue

            print(f"Total coletado em {cidade}: {vagas_cidade}")

        except Exception as e:
            print(f"Erro ao filtrar {cidade}:", e)
            continue

    print(f"📌 {site['empresa']}: {total_empresa} vagas coletadas")
    return vagas


# ===========================
# MAIN
# ===========================
def main():
    historico, links_existentes = carregar_historico()

    novas_vagas_execucao = []
    todas_vagas_coletadas = []
    empresas_sucesso = set()  # 🔥 controla quem rodou corretamente

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:

            # 🔥 FILTRO DEBUG
            if MODO_DEBUG and site["empresa"] not in EMPRESAS_DEBUG:
                continue

            print(f"\n🔎 Buscando vagas da {site['empresa']}")

            try:

                if site["tipo"] == "gupy":
                    vagas = coletar_gupy(page, site)
                    vagas = filtrar_gupy_bahia(vagas)

                elif site["tipo"] == "workday":
                    vagas = coletar_workday(page, site)

                elif site["tipo"] == "continental":
                    vagas = coletar_continental(page, site)

                elif site["tipo"] == "gerdau":
                    vagas = coletar_gerdau(page, site)

                elif site["tipo"] == "eightfold":
                    vagas = coletar_eightfold(page, site)

                elif site["tipo"] == "oracle":
                    vagas = coletar_oracle(page, site)

                elif site["tipo"] == "recrutai":
                    vagas = coletar_recrutai(page, site)

                elif site["tipo"] == "jobconvo":
                    vagas = coletar_jobconvo(page, site)

                elif site["tipo"] == "heineken":
                    vagas = coletar_heineken(page, site)
                
                else:
                    print("⚠️ Tipo não reconhecido")
                    vagas = []

                print(f"📌 {site['empresa']}: {len(vagas)} vagas coletadas")

                todas_vagas_coletadas.extend(vagas)
                empresas_sucesso.add(site["empresa"])  # ✅ marcou como sucesso

            except Exception as e:
                print(f"❌ ERRO ao coletar {site['empresa']}")
                print(f"Motivo: {e}")
                print("⏭️ Pulando para próxima empresa...")
                continue

        browser.close()

    print("\n✅ Coleta finalizada")
    print(f"📊 Total coletado: {len(todas_vagas_coletadas)} vagas")

    # ===========================
    # 🔥 SINCRONIZAÇÃO INTELIGENTE
    # ===========================

    agora = datetime.utcnow().isoformat()
    links_atuais = {vaga["link"] for vaga in todas_vagas_coletadas}

    historico_atualizado = []

    for vaga in historico:
        empresa = vaga["empresa"]

        if empresa in empresas_sucesso:
            # Empresa rodou corretamente
            # Mantém só se ainda existir na coleta
            if vaga["link"] in links_atuais:
                historico_atualizado.append(vaga)
        else:
            # Empresa deu erro → mantém tudo dela
            historico_atualizado.append(vaga)

    # Atualiza conjunto após limpeza
    links_existentes = {vaga["link"] for vaga in historico_atualizado}

    # ===========================
    # IDENTIFICAR NOVAS VAGAS
    # ===========================

    for vaga in todas_vagas_coletadas:
        if vaga["link"] not in links_existentes:
            vaga["data_coleta"] = agora
            novas_vagas_execucao.append(vaga)
            historico_atualizado.append(vaga)

    # ===========================
    # SALVAR ARQUIVOS
    # ===========================

    if MODO_DEBUG:
        print("\n🧪 MODO DEBUG ATIVO - Salvando apenas arquivo de teste")
        salvar_csv("vagas_debug.csv", todas_vagas_coletadas)
    else:
        salvar_csv(CSV_HISTORICO, historico_atualizado)
        salvar_csv(CSV_NOVAS, novas_vagas_execucao)

    print("\n✅ Finalizado")

    if MODO_DEBUG:
        print(f"📌 Total coletado no debug: {len(todas_vagas_coletadas)}")
    else:
        print(f"📌 Novas vagas encontradas: {len(novas_vagas_execucao)}")
        print(f"📌 Total no histórico: {len(historico_atualizado)}")


if __name__ == "__main__":
    main()    
