#!/usr/bin/env python
# coding: utf-8

# In[ ]: 

    
from playwright.sync_api import sync_playwright
import csv
import uuid
import os
import time
import requests
import base64
import smtplib
import re
import unicodedata
import json
from email.mime.text import MIMEText
from datetime import datetime


# ===========================
# BACKUP E PRO CONFIG 
# ===========================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "AndreyCarlos07/central-vagas"
ARQUIVO_BACKUP = "vagas_backup.csv"
ARQUIVO_PRO = "pro.json"
ARQUIVO = "vagas_ocultas.json"

# ===========================
# DEBUG CONFIG
# ===========================
MODO_DEBUG = True  # 🔥 Troque para False quando quiser rodar tudo
EMPRESAS_DEBUG = ["ACELEN RENOVÁVEIS", "ACELEN", "MDC ENERGIA"]

# ===========================
# VAGAS CONFIG
# ===========================
CSV_HISTORICO = "vagas.csv"
CSV_NOVAS = "vagas_novas.csv"

# ===========================
# CARREGAR USUÁRIOS PRO
# ===========================
def carregar_usuarios_pro_github():
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_PRO}"

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("❌ erro ao buscar pro.json:", r.status_code, r.text)
            return []

        data = r.json()

        conteudo = base64.b64decode(data["content"]).decode("utf-8")
        dados = json.loads(conteudo)

        return dados.get("ativos", [])

    except Exception as e:
        print("❌ erro ao carregar usuarios PRO do GitHub:", e)
        return []

# ==========================
# MAPAS DE FILTRO PRO
# ==========================
MAPA_HIERARQUIA = {
    "diretor": ["diretor"],
    "gerente": ["gerente", "lider", "líder", "gestor", "head"],
    "coordenador": ["coordenador", "lider", "líder", "gestor"],
    "supervisor": ["supervisor", "lider", "líder", "chefe"],
    "especialista": ["especialista"],
    "engenheiro": ["engenheiro"],
    "analista": ["analista"],
    "tecnico": ["tecnico", "técnico", "manutenedor", "reparador", "planejador"],
    "inspetor": ["inspetor"],
    "operador": ["operador"],
    "auxiliar": ["auxiliar", "conferente", "abastecedor", "alimentador"],
    "assistente": ["assistente", "conferente", "abastecedor", "alimentador"],
    "jovem_aprendiz": ["jovem aprendiz", "aprendiz"],
    "estagio": ["estagio", "estágio", "estagiário", "estagiária"]
}

MAPA_AREA = {
    "manutencao": ["manutencao", "manutenção", "automacao", "automação", "robô", "robo", "roboticista", "instrumentação", "instrumentacao", "eletrica", "elétrica", "eletricista", "mecanica", "mecânica", "soldador", "solda", "corte", "ferramentaria", "soldagem", "refrigeracao"],
    "producao": ["producao", "produção"],
    "produto": ["produto"],
    "projeto": ["projeto"],
    "operacao": ["operacao", "operacional"],
    "administracao": ["administracao", "administrativo", "administrativa", "rh", "dp", "partner"],
    "marketing": ["marketing"],
    "qualidade": ["qualidade", "qa", "segurança", "meio ambiente", "químico", "trabalho"],
    "logistica": ["logística", "logistica", "estoque", "almoxarifado", "estoquista"],
    "civil": ["civil", "obras", "obra"]
}

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
# SELECIONAR VAGAS
# ===========================
def filtrar_vagas_usuario(vagas, user):
    resultado = []

    for v in vagas:
        titulo = v["titulo"].lower()

        tipo = user.get("tipo_filtro")
        valor = user.get("valor")

        # 🔹 HIERARQUIA
        if tipo == "hierarquia":
            palavras = MAPA_HIERARQUIA.get(valor, [])
            if not any(p in titulo for p in palavras):
                continue

        # 🔹 ÁREA
        elif tipo == "area":
            palavras = MAPA_AREA.get(valor, [])
            if not any(p in titulo for p in palavras):
                continue

        # 🔹 EMPRESA
        elif tipo == "empresa":
            if v["empresa"] not in valor:
                continue

        resultado.append(v)

    return resultado


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
# FAZER BACKUP
# ===========================
def backup_csv_github():

    if not os.path.exists(CSV_HISTORICO):
        print("⚠️ Nenhum histórico para backup")
        return

    print("☁️ Enviando backup para GitHub...")

    with open(CSV_HISTORICO, "r", encoding="utf-8") as f:
        conteudo = f.read()

    encoded = base64.b64encode(conteudo.encode()).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_BACKUP}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    # Verifica se já existe (pra pegar SHA)
    r = requests.get(url, headers=headers)
    sha = None

    if r.status_code == 200:
        sha = r.json()["sha"]

    payload = {
        "message": "Backup automático vagas.csv",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)

    print("✅ Backup realizado com sucesso!")


# ===========================
# GERAR SLUG
# ===========================
def gerar_slug(texto):
    # remove acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    
    # minúsculo
    texto = texto.lower()
    
    # substitui tudo que não é letra/número por hífen
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    
    # remove hífen do início/fim
    texto = texto.strip('-')
    
    return texto


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
    {"empresa": "GRUPO FERTIPAR", "url": "https://grupofertipar.gupy.io", "tipo": "gupy"},
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
        "url": "https://jobs.gerdau.com/search/?createNewAlert=false&q&locationsearch&locale=pt_BR",
        "tipo": "gerdau"
    },
    {
        "empresa": "GRUPO PETRÓPOLIS",
        "url": "https://carreiras.grupopetropolis.com.br",
        "tipo": "petropolis"
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
        "tipo": "recrutaifix",
        "cidade": "São Francisco do Conde / BA"
    },
    {
        "empresa": "MDC ENERGIA",
        "url": "https://mdcnossostalentos.jobs.recrut.ai/#openings",
        "tipo": "recrutaifix",
        "cidade": ["Camaçari / BA", "Salvador / BA"]
    },
    {
        "empresa": "ACELEN RENOVÁVEIS",
        "url": "https://acelen.jobs.recrut.ai/acelenrenewables#openings",
        "tipo": "recrutaifix",
        "cidade": "São Francisco do Conde / BA"
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
    },
    {
        "empresa": "GOLDWIND",
        "url": "https://careers.goldwind.com/Brazil/search", 
        "tipo": "goldwind"
    },
    {
        "empresa": "HALLIBURTON",
        "url": "https://jobs.halliburton.com/Brazil/search", 
        "tipo": "halliburton"
    },
    {
        "empresa": "JDE PEET'S",
        "url": "https://careers-br.jdepeets.com/pt-BR/job-search", 
        "tipo": "jde"
    },
    {
        "empresa": "BOMIX",
        "url": "https://bomix.pandape.infojobs.com.br", 
        "tipo": "pandape"
    },
    {
        "empresa": "ZEENTECH",
        "url": "https://zeentech.pandape.infojobs.com.br",
        "tipo": "pandape"
    },
    {
        "empresa": "WHITE MARTINS",
        "url": "https://trabalheconosco.vagas.com.br/white-martins/oportunidades",
        "tipo": "vagas"
    },
    {
        "empresa": "CSN",
        "url": "https://trabalheconosco.vagas.com.br/csn/oportunidades",
        "tipo": "vagas"
    },
    {
        "empresa": "ELEKEIROZ",
        "url": "https://trabalheconosco.vagas.com.br/elekeiroz/oportunidades",
        "tipo": "vagas"
    },
    {
        "empresa": "MFX",
        "url": "https://mfx.inhire.app/vagas",
        "tipo": "inhire",
        "tenant": "mfx",
        "cidades": ["Salvador, BA, BR"]
    },
    {
        "empresa": "TRESCAL",
        "url": "https://trescal.inhire.app/vagas",
        "tipo": "inhire",
        "tenant": "trescal",
        "cidades": ["Camaçari, BA, BR"]
    },
    {
        "empresa": "INFOTEC BRASIL",
        "url": "https://infotecbrasil.inhire.app/vagas",
        "tipo": "inhire",
        "tenant": "infotecbrasil",
        "cidades": ["São Francisco do Conde, BA, BR", "Catu, BA, BR", "Salvador, BA, BR"]
    }
]

# 📍 filtro Bahia (somente GUPY)
PALAVRAS_BA = ["BAHIA", "SALVADOR", "CAMAÇARI", "LAURO", "FEIRA", "DIAS D'ÁVILA", "CANDEIAS", "POJUCA - BA", "CATU", "SIMÕES FILHO", "ALAGOINHAS", "MATA DE SÃO JOÃO"]

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

    try:
        page.goto(site["url"], timeout=60000)

        # 🔥 espera campo aparecer
        page.wait_for_selector('input[name="locationsearch"]')

        # 🔥 digita como humano
        page.click('input[name="locationsearch"]')
        page.fill('input[name="locationsearch"]', "simões filho")

        # 🔥 ESSENCIAL: pressiona ENTER (isso dispara o search real do SAP)
        page.keyboard.press("Enter")

        # 🔥 fallback: botão também
        try:
            page.click('input.keywordsearchbutton')
        except:
            pass

        # 🔥 espera REAL: algum job aparecer
        page.wait_for_selector("#job-tile-list li", timeout=30000)

        print("✅ vagas apareceram")

        # 🔥 pequena pausa pra garantir render completo
        time.sleep(2)

        jobs = page.locator("#job-tile-list li")

        total = jobs.count()
        print("📦 total encontrado:", total)

        for i in range(total):
            try:
                job = jobs.nth(i)

                link_element = job.locator("a.jobTitle-link").first
                titulo = link_element.inner_text().strip()
                link = link_element.get_attribute("href")

                if not titulo or not link:
                    continue

                if not link.startswith("http"):
                    link = "https://jobs.gerdau.com" + link

                link_limpo = link.split("?")[0]

                if link_limpo in links_coletados:
                    continue

                links_coletados.add(link_limpo)

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo.strip(),
                    "empresa": site["empresa"],
                    "link": link_limpo
                })

            except Exception as e:
                print("erro job:", e)

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas

    print(f"📌 {site['empresa']}: {len(vagas)} vagas coletadas")
    return vagas
    

# ===========================
# GRUPO PETRÓPOLIS (API)
# ===========================
def coletar_petropolis(page, site):

    vagas = []
    links_coletados = set()

    try:
        # ===========================
        # 1️⃣ ABRE SITE (SESSÃO)
        # ===========================
        page.goto("https://carreiras.grupopetropolis.com.br", timeout=60000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        print("🌐 sessão iniciada")

        # interação fake (anti-bot)
        page.mouse.move(100, 200)
        page.mouse.wheel(0, 500)
        time.sleep(2)

        # ===========================
        # 2️⃣ COOKIES
        # ===========================
        cookies_list = page.context.cookies()
        cookies = {c['name']: c['value'] for c in cookies_list}

        # ===========================
        # 3️⃣ HEADERS
        # ===========================
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "Origin": "https://carreiras.grupopetropolis.com.br",
            "Referer": "https://carreiras.grupopetropolis.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/146 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        # ===========================
        # 4️⃣ API URL
        # ===========================
        url = "https://carreiras.grupopetropolis.com.br/services/jobs/search/"

        cidades = [
            "ALAGOINHAS, BA, BR",
            "CAMACARI, BA, BR",
            "SALVADOR, BA, BR"
        ]

        total_empresa = 0

        # ===========================
        # 5️⃣ LOOP
        # ===========================
        for cidade in cidades:

            print(f"📍 Buscando vagas em: {cidade}")

            payload = {
                "keywords": "",
                "locationsearch": "",
                "page": 0,
                "recordsperpage": 50,
                "sortby": "referencedate",
                "sortdir": "desc",

                # 🔥 necessário pro backend responder certo
                "facetquery": {
                    "facet": True,
                    "mincount": 1,
                    "limit": 5000,
                    "fields": ["location", "city", "state", "title"]
                },

                # 🔥 filtro correto
                "filterquery": {
                    "location": [cidade]
                }
            }

            time.sleep(1)  # evita bloqueio silencioso

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                cookies=cookies
            )

            if response.status_code != 200:
                print(f"❌ erro na API ({cidade}):", response.status_code)
                continue

            data = response.json()

            # ✅ CORREÇÃO FINAL
            jobs = data.get("jobList", [])

            print(f"📦 total encontrado em {cidade}: {len(jobs)}")

            for job in jobs:
                try:
                    titulo = job.get("title")
                    url_title = job.get("urltitle")
                    job_id = job.get("id")
                    
                    if not titulo or not url_title or not job_id:
                        continue

                    # 🔥 monta link corretamente
                    link = f"https://carreiras.grupopetropolis.com.br/job/{url_title}/{job_id}/"

                    link_limpo = link.split("?")[0]

                    if link_limpo in links_coletados:
                        continue

                    links_coletados.add(link_limpo)

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo.strip(),
                        "empresa": site["empresa"],
                        "link": link_limpo
                    })

                    total_empresa += 1

                except Exception as e:
                    print("erro job:", e)

        print(f"📌 {site['empresa']}: {total_empresa} vagas coletadas")
        return vagas

    except Exception as e:
        print("❌ erro geral:", e)
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
# RECRUT.AI (FINAL DEFINITIVA)
# ===========================
def coletar_recrutai_fix(page, site):

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
            # ===========================
            # FILTRO
            # ===========================
            page.locator("button.dropdown-toggle").nth(1).click()
            page.wait_for_timeout(800)

            page.locator(f"text={cidade}").first.click()
            page.wait_for_timeout(800)

            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # ===========================
            # AGUARDA RESULTADOS
            # ===========================
            try:
                page.wait_for_selector('a[href*="job/"]', timeout=10000)
            except:
                print(f"⚠️ Nenhuma vaga encontrada para {cidade}")
                continue

            cards = page.locator('a[href*="job/"]')
            total = cards.count()

            print(f"📦 Total de vagas em {cidade}: {total}")

            # ===========================
            # LOOP VAGAS
            # ===========================
            for i in range(total):
                try:
                    card = cards.nth(i)

                    link = card.get_attribute("href")

                    if not link:
                        continue

                    # ===========================
                    # 🔧 LINK CORRETO
                    # ===========================
                    if link.startswith("http"):
                        link_completo = link
                    else:
                        base = site["url"].split("#")[0]
                        link_completo = base.rstrip("/") + "/" + link.lstrip("/")

                    # 🔥 FIX ACELEN RENOVÁVEIS (COMPLETO)
                    link_completo = link_completo.replace(
                        "/acelenrenewables/acelenrenewables/",
                        "/acelenrenewables/"
                    ).replace(
                        "/acelenrenewables//acelenrenewables/",
                        "/acelenrenewables/"
                    )

                    # ===========================
                    # 🔁 DEDUPLICAÇÃO
                    # ===========================
                    if link_completo in links_coletados:
                        continue

                    links_coletados.add(link_completo)

                    # ===========================
                    # 🧠 TITULO REAL
                    # ===========================
                    try:
                        container = card.locator("xpath=ancestor::div[contains(@class, 'card')]")
                        h5 = container.locator("h5").first

                        titulo_raw = h5.inner_text(timeout=2000).strip()

                        # quebra por linhas e remove vazios
                        linhas = [l.strip() for l in titulo_raw.split("\n") if l.strip()]

                        if len(linhas) >= 2:
                            titulo = linhas[-1]  # última linha = título real
                        else:
                            titulo = linhas[0]

                    except:
                        titulo = "Vaga"

                    vagas.append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo,
                        "empresa": site["empresa"],
                        "link": link_completo
                    })

                except Exception as e:
                    print("Erro ao processar card:", e)

        except Exception as e:
            print("Erro ao filtrar cidade:", e)

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
# GOLDWIND
# ===========================
def coletar_goldwind(page, site):
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
        page.goto("https://careers.goldwind.com/Brazil/search")
        page.wait_for_selector("#location", timeout=30000)

    else:
        print("✅ Age gate não apareceu.")

    # ===========================
    # 2️⃣ CIDADES PARA FILTRAR
    # ===========================
    cidades = ["Camacari"]

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
                        link = "https://careers.goldwind.com" + link

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
# HALLIBURTON
# ===========================
def coletar_halliburton(page, site):

    vagas = []
    links_coletados = set()
    total_empresa = 0

    print("\n🔎 Buscando vagas da HALLIBURTON")

    try:
        # ===========================
        # 1️⃣ CIDADES (PADRÃO URL)
        # ===========================
        cidades = [
            ("catu", "CATU%2C+BA%2C+BR")
        ]

        for keyword, location in cidades:

            print(f"📍 Buscando: {keyword} / {location}")

            vagas_cidade = 0

            try:
                # ===========================
                # 2️⃣ MONTA URL DINÂMICA
                # ===========================
                url = f"https://jobs.halliburton.com/search/?q={keyword}&locationsearch={location}"

                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(3)

                # ===========================
                # 3️⃣ COLETA LINKS
                # ===========================
                links = page.locator("a[href*='/job/']")
                total = links.count()

                print(f"📦 total encontrado: {total}")

                for i in range(total):
                    try:
                        link = links.nth(i).get_attribute("href")

                        if not link:
                            continue

                        if link.startswith("/"):
                            link = "https://jobs.halliburton.com" + link

                        link_limpo = link.split("?")[0]

                        if link_limpo in links_coletados:
                            continue

                        links_coletados.add(link_limpo)

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
                        print("erro vaga:", e)

                print(f"Total coletado em {keyword}: {vagas_cidade}")

            except Exception as e:
                print(f"Erro ao buscar {keyword}:", e)

        print(f"📌 {site['empresa']}: {total_empresa} vagas coletadas")
        return vagas

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas
        

# ===========================
# JDE PEETS
# ===========================
def coletar_jde(page, site):

    vagas = []
    links_coletados = set()

    try:
        page.goto(site["url"], timeout=60000)

        # 🍪 cookies
        try:
            page.click("#onetrust-accept-btn-handler", timeout=5000)
        except:
            pass

        page.wait_for_selector('a.btn.btn-secondary', timeout=30000)
        print("✅ vagas carregadas")

        time.sleep(2)

        jobs = page.locator('a.btn.btn-secondary')
        cidades = page.locator('span.city-value')

        total = jobs.count()
        print("📦 total encontrado:", total)

        for i in range(total):
            try:
                cidade = cidades.nth(i).inner_text().strip()

                if "Salvador" not in cidade:
                    continue

                job = jobs.nth(i)
                link = job.get_attribute("href")

                if not link:
                    continue

                if not link.startswith("http"):
                    link = "https://careers-br.jdepeets.com" + link

                link_limpo = link.split("&")[0]

                if link_limpo in links_coletados:
                    continue

                links_coletados.add(link_limpo)

            except Exception as e:
                print(f"erro coleta {i}:", e)

        print("🔗 vagas filtradas Salvador:", len(links_coletados))

        # entra nas vagas
        for link in links_coletados:
            try:
                page.goto(link, timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                titulo = page.locator("h1").inner_text()

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo.strip(),
                    "empresa": site["empresa"],
                    "link": link
                })

            except Exception as e:
                print("erro job:", e)

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas

    print(f"📌 {site['empresa']}: {len(vagas)} vagas coletadas")
    return vagas

# ===========================
# PANDAPE
# ===========================
def coletar_pandape(page, site):

    vagas = []
    links_coletados = set()

    try:
        page.goto(site["url"], timeout=60000)

        # 🔥 espera página carregar
        page.wait_for_selector("body")

        time.sleep(2)

        # ✅ CLICAR NO FILTRO DE CIDADE (abre o dropdown)
        #try:
            #page.locator("#FilterLocation3").click()
            #time.sleep(1)
        #except:
            #print("⚠️ não encontrou filtro cidade")

        filtro_cidade = page.locator("#FilterLocation3")

        # 🔥 NOVO: clicar em "Ver mais" se existir
        try:
            botao_ver_mais = filtro_cidade.locator("text=Ver mais")
            if botao_ver_mais.count() > 0:
                botao_ver_mais.first.click()
                print("🔽 expandiu lista de cidades")
                time.sleep(1)
        except:
            print("ℹ️ não tinha botão 'Ver mais'")

        # ✅ MARCAR SALVADOR
        try:
            page.locator("span:has-text('Salvador - BA')").click()
            print("📍 Salvador selecionado")
        except:
            print("⚠️ Salvador não encontrado")

        # ✅ MARCAR SIMÕES FILHO
        try:
            page.locator("span:has-text('Simões Filho - BA')").click()
            print("📍 Simões Filho selecionado")
        except:
            print("⚠️ Simões Filho não encontrado")

       # ✅ MARCAR CAMAÇARI
        try:
            #page.wait_for_selector("span:has-text('Camaçari - BA')", timeout=5000)
            page.locator("span:has-text('Camaçari - BA')").click()
            print("📍 Camaçari selecionado")
        except:
            print("⚠️ Camaçari não encontrado")

        # 🔥 espera atualizar lista
        time.sleep(3)

        # 🔥 clicar em "carregar mais" até acabar
        while True:
            try:
                botao = page.locator("#btLoadMore")

                if botao.is_visible():
                    botao.click()
                    print("➕ carregando mais vagas...")
                    time.sleep(2)
                else:
                    break
            except:
                break

        print("✅ todas vagas carregadas")

        # 🔥 pegar todos os links
        jobs = page.locator("a[href*='/Detail/']")
        total = jobs.count()

        print("📦 total encontrado:", total)

        for i in range(total):
            try:
                job = jobs.nth(i)

                link = job.get_attribute("href")

                if not link:
                    continue

                if not link.startswith("http"):
                    link = site["url"].split(".infojobs")[0] + ".infojobs.com.br" + link

                link_limpo = link.split("?")[0]

                if link_limpo in links_coletados:
                    continue

                links_coletados.add(link_limpo)

            except Exception as e:
                print("erro coleta:", e)

        print("🔗 links únicos:", len(links_coletados))

        # 🔥 entra em cada vaga
        for link in links_coletados:
            try:
                page.goto(link, timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                titulo = page.locator("h1").inner_text()

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo.strip(),
                    "empresa": site["empresa"],
                    "link": link
                })

            except Exception as e:
                print("erro job:", e)

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas

    print(f"📌 {site['empresa']}: {len(vagas)} vagas coletadas")
    return vagas


# ===========================
# VAGAS 
# ===========================
def coletar_vagas(page, site): 

    vagas = []
    links_coletados = set()

    try:
        print(f"\n🔎 Buscando vagas da {site['empresa']}")

        # ===========================
        # 1️⃣ ABRE SITE
        # ===========================
        page.goto(site["url"], timeout=60000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        cidades = ["Camaçari", "Candeias", "Salvador"]

        total_geral = 0

        for cidade in cidades:

            print(f"\n🌆 Buscando por: {cidade}")

            try:
                # ===========================
                # INPUT DE BUSCA
                # ===========================
                search_input = page.locator("input.jobs-filter__input")

                if search_input.count() == 0:
                    print("🚨 Campo de busca não encontrado")
                    continue

                # limpa antes de buscar
                search_input.fill("")
                time.sleep(1)

                # digita cidade
                search_input.fill(cidade)
                search_input.press("Enter")
                time.sleep(4)

                # ===========================
                # AGUARDA RESULTADOS
                # ===========================
                try:
                    page.wait_for_selector("a[href*='/oportunidade/']", timeout=10000)
                except:
                    print(f"⚠️ Nenhuma vaga encontrada para {cidade}")
                    continue

                cards = page.locator("a[href*='/oportunidade/']")
                total = cards.count()

                print(f"📦 {cidade}: {total} vagas encontradas")

                total_geral += total

                # ===========================
                # LOOP VAGAS
                # ===========================
                for i in range(total):
                    try:
                        card = cards.nth(i)

                        link = card.get_attribute("href")

                        if not link:
                            continue

                        if not link.startswith("http"):
                            link = "https://trabalheconosco.vagas.com.br" + link

                        link_limpo = link.split("?")[0]

                        titulo = card.inner_text().strip()

                        # ===========================
                        # 🔥 DEDUPLICAÇÃO FORTE
                        # ===========================
                        chave_unica = (titulo.lower(), link_limpo)

                        if chave_unica in links_coletados:
                            continue

                        links_coletados.add(chave_unica)

                        vagas.append({
                            "id": str(uuid.uuid4())[:8],
                            "titulo": titulo,
                            "empresa": site["empresa"],
                            "link": link_limpo
                        })

                    except Exception as e:
                        print("erro vaga:", e)

            except Exception as e:
                print(f"❌ erro na cidade {cidade}:", e)

        print(f"\n📊 Total bruto (somado cidades): {total_geral}")
        print(f"📌 {site['empresa']}: {len(vagas)} vagas únicas coletadas")

        return vagas

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas
        

# ===========================
# INHIRE
# ===========================
def coletar_inhire(site):

    vagas = []
    links_coletados = set()

    print(f"\n🔎 Buscando vagas da {site['empresa']}")

    try:
        url = "https://api.inhire.app/job-posts/public/pages"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
            "Origin": f"https://{site['tenant']}.inhire.app",
            "Referer": f"https://{site['tenant']}.inhire.app/",
            "x-tenant": site["tenant"]  # 🔥 DINÂMICO
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("❌ erro na API:", response.status_code)
            return vagas

        data = response.json()
        jobs = data.get("jobsPage", [])

        print(f"📦 total encontrado: {len(jobs)}")

        # 🔥 cidades (opcional)
        cidades = site.get("cidades", [])

        total_empresa = 0

        for job in jobs:
            try:
                titulo = job.get("displayName")
                job_id = job.get("jobId")
                location = job.get("location", "").lower()

                if not titulo or not job_id:
                    continue

                # ===========================
                # 🔥 FILTRO POR CIDADE (OPCIONAL)
                # ===========================
                if cidades:
                    if not any(cidade.lower() in location for cidade in cidades):
                        continue

                # ===========================
                # 🔥 MONTA LINK
                # ===========================
                slug = gerar_slug(titulo)
                link = f"https://{site['tenant']}.inhire.app/vagas/{job_id}/{slug}"
                link_limpo = link.split("?")[0]

                if link_limpo in links_coletados:
                    continue

                links_coletados.add(link_limpo)

                vagas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo.strip(),
                    "empresa": site["empresa"],
                    "link": link_limpo
                })

                total_empresa += 1

            except Exception as e:
                print("erro vaga:", e)

        print(f"📌 {site['empresa']}: {total_empresa} vagas coletadas")
        return vagas

    except Exception as e:
        print("❌ erro geral:", e)
        return vagas

# ===========================
# CARREGAR OCULTAS EMAIL INDIVIDUAL
# ===========================
def carregar_ocultas():

    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    try:
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("⚠️ erro ao carregar vagas ocultas")
            return set()

        data = r.json()
        conteudo = base64.b64decode(data["content"]).decode("utf-8")

        json_data = json.loads(conteudo)

        # 🔥 AGORA PEGANDO DO FORMATO CORRETO
        return set(json_data.get("ocultas", []))

    except Exception as e:
        print("❌ erro ao processar vagas ocultas:", e)
        return set()
        

# ===========================
# REMOVER OCULTAS EMAIL INDIVIDUAL
# ===========================

def remover_ocultas(vagas, ocultas):
    return [v for v in vagas if v["id"] not in ocultas]

# ===========================
# LOGOS EMAIL INDIVIDUAL
# ===========================

def get_logo_url(empresa):
    nome = empresa.lower().replace(" ", "").replace("-", "")
    return f"https://raw.githubusercontent.com/AndreyCarlos07/central-vagas/main/logos/{nome}.png"


# ===========================
# GERAR RELATÓRIO INDIVIDUAL
# ===========================
def montar_relatorio_usuario(user, vagas_filtradas, vagas_novas):

    nome = user.get("nome")
    tipo = user.get("tipo_filtro")
    valor = user.get("valor")

    def criar_card(v):
        logo_url = get_logo_url(v["empresa"])

        return (
            '<div style="border:1px solid #e1e1e1;padding:10px;margin-bottom:8px;border-radius:8px;">'

            '<div style="display:flex;align-items:flex-start;gap:18px;">'

            # LOGO
            f'<img src="{logo_url}" width="50" height="50" '
            'style="border-radius:6px;object-fit:contain;">'

            # BLOCO DIREITA (texto + botão)
            '<div style="flex:1;padding-left:4px;">'

            f'<a href="{v["link"]}" target="_blank" '
            'style="text-decoration:none;color:#0a66c2;">'
            f'<p style="margin:0 0 6px 0;font-weight:bold;font-size:14px;line-height:1.2;">{v["titulo"].upper()}</p>'
            '</a>'
            f'<p style="margin:0 0 8px 0;font-size:13px;">Empresa: <b>{v["empresa"]}</b></p>'

            '</div>'
            '</div>'

            '</div>'
        )
    
    partes = []
 
    # HTML início    
    partes.append('<html>')
    partes.append('<body style="font-family:Arial;background:#f4f6f8;padding:20px;">')
    partes.append('<div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:10px;">')

    partes.append(
        '<div style="text-align:center;background:#0a66c2;color:white;'
        'padding:12px;border-radius:8px;margin-bottom:20px;font-weight:bold;">'
        'Central de Vagas PRO'
        '</div>'
        )
    partes.append(f'<p>Olá, <b>{nome}</b> 👋</p>')
    partes.append(f'<p>Filtro escolhido: {tipo.upper()} → {valor}</p>')
    partes.append(f'<p>Total de vagas: {len(vagas_filtradas)}</p>')
    
    # NOVAS VAGAS
    partes.append('<h3 style="font-size:16px;margin-bottom:10px;">Novas vagas no seu perfil:</h3>')
    
    if vagas_novas:
        for v in vagas_novas[:10]:
            partes.append(criar_card(v))

    else:
        partes.append(
            '<p style="background:#fff3cd;padding:10px;border-radius:5px;">'
            '📭 Após busca, não houve vagas novas hoje para o seu perfil.'
            '</p>'
        )

    # RESUMO VAGAS
    tem_mais_vagas = len(vagas_filtradas) > 10

    botao_extra = ""

    # ===========================
    # MONTAR QUERY INTELIGENTE
    # ===========================
        
    empresa_query = ""

    if tipo == "hierarquia":
        palavras = MAPA_HIERARQUIA.get(valor, [valor])
        query = "+".join(set(palavras))

    elif tipo == "area":
        palavras = MAPA_AREA.get(valor, [valor])
        query = "+".join(set(palavras))

    elif tipo == "empresa":
        # empresa normalmente é lista
        empresas = valor if isinstance(valor, list) else [valor]
        query = ""  # não usa q
        empresa_query = "&empresa=" + ",".join(empresas)

    else:
        query = valor
    
    if tem_mais_vagas:

        if tipo == "empresa":
            url = f"https://central-vagas.onrender.com/?ordem=recentes{empresa_query}"
        else:
            url = f"https://central-vagas.onrender.com/?q={query}&ordem=recentes"

        botao_extra = (
            f'<div style="margin-top:15px;">'
            f'<a href="{url}" '
            'style="padding:8px 14px;background:#0a66c2;color:white;'
            'text-decoration:none;border-radius:4px;font-size:12px;">'
            'Ver todas as vagas do seu perfil'
            '</a>'
            '</div>'
        )

    partes.append('<h3 style="font-size:16px;margin-bottom:10px;">Resumo de vagas no seu perfil:</h3>')
    
    for v in vagas_filtradas[:10]:
        partes.append(criar_card(v))
        
    partes.append(botao_extra)
    
    # FINAL
    partes.append('<hr>')

    partes.append('</div>')
    partes.append('</body>')
    partes.append('</html>')

    return "".join(partes)

    
# ===========================
# ENVIAR EMAIL INDIVIDUAL
# ===========================
def enviar_email_usuario(destinatario, mensagem):
    remetente = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")

    # 🔥 MODO DEBUG → FORÇA ENVIO SÓ PRA VOCÊ
    if MODO_DEBUG:
        print("🧪 DEBUG ATIVO → redirecionando email para você")
        destinatario = "andrey.engenhariamecatronica@gmail.com"

    msg = MIMEText(mensagem, "html")
    msg["Subject"] = "📊 Suas vagas personalizadas - Central de Vagas PRO"
    msg["From"] = remetente
    msg["To"] = destinatario

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print(f"📧 Email enviado para {destinatario}")


# ===========================
# GERAR RELATÓRIO GMAIL
# ===========================
def gerar_relatorio(total, sucesso, erro, zero, empresas_erro, empresas_zero, total_vagas):
    status = "🟢 OK" if erro == 0 else "🔴 ERROS DETECTADOS"

    return f"""
📊 RELATÓRIO DIÁRIO - SCRAPER

⏰ Data: {time.strftime('%d/%m/%Y %H:%M')}

🏢 Total de empresas: {total}
📊 Total de vagas coletadas: {total_vagas}

✅ Sucesso: {sucesso}
❌ Erro: {erro}
⚠️ Sem vagas: {zero}

-----------------------------------

❌ EMPRESAS COM ERRO:
{', '.join(sorted(empresas_erro)) if empresas_erro else 'Nenhuma'}

-----------------------------------

⚠️ EMPRESAS COM 0 VAGAS:
{', '.join(sorted(empresas_zero)) if empresas_zero else 'Nenhuma'}

-----------------------------------

📊 STATUS: {status}
"""


# ===========================
# ENVIAR ALERTA
# ===========================
def enviar_email_alerta(mensagem):
    remetente = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")
    destinatario = "andrey.engenhariamecatronica@gmail.com"

    msg = MIMEText(mensagem)
    msg["Subject"] = "Relatório Diário - Scraper"
    msg["From"] = remetente
    msg["To"] = destinatario

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)

    print("📧 Email enviado com sucesso!")

    
# ===========================
# MAIN
# ===========================
def main():
    historico, links_existentes = carregar_historico()

    novas_vagas_execucao = []
    todas_vagas_coletadas = []
    empresas_sucesso = set()  # 🔥 controla quem rodou corretamente
    empresas_erro = set()       # 👈 adicionar
    empresas_zero = set()       # 👈 adicionar

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in SITES:

            # 🔥 FILTRO DEBUG
            if MODO_DEBUG and site["empresa"] not in EMPRESAS_DEBUG:
                continue

            print(f"\n🔎 Buscando vagas da {site['empresa']}")

            inicio = time.time()

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

                elif site["tipo"] == "petropolis":
                    vagas = coletar_petropolis(page, site)
                
                elif site["tipo"] == "eightfold":
                    vagas = coletar_eightfold(page, site)

                elif site["tipo"] == "oracle":
                    vagas = coletar_oracle(page, site)

                elif site["tipo"] == "recrutai":
                    vagas = coletar_recrutai(page, site)

                elif site["tipo"] == "recrutaifix":
                    vagas = coletar_recrutai_fix(page, site)

                elif site["tipo"] == "jobconvo":
                    vagas = coletar_jobconvo(page, site)

                elif site["tipo"] == "heineken":
                    vagas = coletar_heineken(page, site)

                elif site["tipo"] == "goldwind":
                    vagas = coletar_goldwind(page, site)

                elif site["tipo"] == "halliburton":
                    vagas = coletar_halliburton(page, site)

                elif site["tipo"] == "jde":
                    vagas = coletar_jde(page, site)

                elif site["tipo"] == "pandape":
                    vagas = coletar_pandape(page, site)

                elif site["tipo"] == "vagas":
                    vagas = coletar_vagas(page, site)

                elif site["tipo"] == "inhire":
                    vagas = coletar_inhire(site)
                
                else:
                    print("⚠️ Tipo não reconhecido")
                    vagas = []

                print(f"📌 {site['empresa']}: {len(vagas)} vagas coletadas")

                fim = time.time()
                tempo_execucao = fim - inicio
                minutos = tempo_execucao / 60

                print(f"⏱️ {site['empresa']}: {tempo_execucao:.2f}s ({minutos:.2f} min)")

                if len(vagas) == 0:
                    empresas_zero.add(site["empresa"])

                todas_vagas_coletadas.extend(vagas)
                empresas_sucesso.add(site["empresa"])  # ✅ marcou como sucesso

            except Exception as e:
                print(f"❌ ERRO ao coletar {site['empresa']}")
                print(f"Motivo: {e}")
                print("⏭️ Pulando para próxima empresa...")

                empresas_erro.add(site["empresa"])  # 👈 adicionar
                
                continue

        browser.close()

    print("\n✅ Coleta finalizada")
    print(f"📊 Total coletado: {len(todas_vagas_coletadas)} vagas")

    total = len(SITES)
    sucesso = len(empresas_sucesso)
    erro = len(empresas_erro)
    zero = len(empresas_zero)

    total_vagas = len(todas_vagas_coletadas)

    try:
        mensagem = gerar_relatorio(total, sucesso, erro, zero, empresas_erro, empresas_zero, total_vagas)
        enviar_email_alerta(mensagem)
    except Exception as e:
        print("⚠️ Erro ao enviar email:", e)

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

    if not MODO_DEBUG:
        backup_csv_github()  # 🔥 BACKUP ANTES DE SOBRESCREVER
    
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

    # ===========================
    # VAGAS FILTRADAS
    # ===========================

    try:
        usuarios = carregar_usuarios_pro_github()

        ocultas = carregar_ocultas()

        print(f"\n👑 Enviando vagas para {len(usuarios)} usuários PRO...")

        for user in usuarios:
            try:
                email = user.get("email")

                vagas_filtradas = filtrar_vagas_usuario(historico_atualizado, user)
                vagas_novas_user = filtrar_vagas_usuario(novas_vagas_execucao, user)
                vagas_filtradas = remover_ocultas(vagas_filtradas, ocultas)
                vagas_novas_user = remover_ocultas(vagas_novas_user, ocultas)

                if not vagas_filtradas:
                    print(f"⚠️ Nenhuma vaga para {email}")
                    continue

                relatorio = montar_relatorio_usuario(
                    user,
                    vagas_filtradas,
                    vagas_novas_user
                )

                enviar_email_usuario(email, relatorio)

            except Exception as e:
                print(f"❌ erro ao processar usuário {user.get('email')}: {e}")

    except Exception as e:
        print("❌ erro geral no envio PRO:", e)


if __name__ == "__main__":
    main()    
