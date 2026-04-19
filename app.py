#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
import csv
import time
from flask import Flask, redirect, render_template_string, request
import smtplib
from email.mime.text import MIMEText
import json
import base64
import requests
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

CSV_FILE = "vagas.csv"
VAGAS_POR_PAGINA = 10  # ✅ ADICIONADO

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

EMAIL_USER = os.environ.get("EMAIL_USER")

EMAIL_PASS = os.environ.get("EMAIL_PASS")

EMAIL_USER_CENTRAL = os.environ.get("EMAIL_USER_CENTRAL")

EMAIL_PASS_CENTRAL = os.environ.get("EMAIL_PASS_CENTRAL")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

RESEND_API_KEY_CENTRAL = os.environ.get("RESEND_API_KEY_CENTRAL")

REPO = "AndreyCarlos07/central-vagas"
ARQUIVO_OCULTAS = "vagas_ocultas.json"
ARQUIVO_AVALIACOES = "avaliacoes.json"
ARQUIVO_CONTATOS = "contatos.json"
ARQUIVO_PRO = "pro.json"


# ==========================
# PALAVRAS BLOQUEADAS
# ==========================
PALAVRAS_BLOQUEADAS = {
    "enfermagem",
    "enfermeiro",
    "vendedor",
    "vendas",
    "advogado",
    "jurídico",
    "cozinha",
    "serviços gerais",
    "cozinheiro",
    "representante",
    "eusébio",
    "motorista",
    "jaboatão",
    "mg",
    "ufrj",
    "beleza",
    "sudeste",
    "loja"
}

# ==========================
# MAPAS DE FILTRO PRO
# ==========================

MAPA_HIERARQUIA = {
    "diretor": ["diretor", "head"],
    "gerente": ["gerente", "lider", "líder", "gestor", "head"],
    "coordenador": ["coordenador", "lider", "líder", "gestor"],
    "supervisor": ["supervisor", "lider", "líder", "chefe"],
    "especialista": ["especialista"],
    "engenheiro": ["engenheiro"],
    "analista": ["analista"],
    "tecnico": ["tecnico", "técnico", "manutenedor", "reparador", "planejador", "inspetor", "operador"],
    "auxiliar": ["auxiliar", "conferente", "abastecedor", "alimentador", "assistente"],
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

def filtrar_vagas_usuario(vagas, user):
    resultado = []

    for v in vagas:
        titulo = v.get("titulo", "").lower()

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
            empresas = valor if isinstance(valor, list) else [valor]
            if v.get("empresa") not in empresas:
                continue

        resultado.append(v)

    return resultado
    

def carregar_ocultas():

    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_OCULTAS}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return set()

    data = r.json()

    conteudo = base64.b64decode(data["content"]).decode()

    json_data = json.loads(conteudo)

    return set(json_data.get("ocultas", []))


def salvar_ocultas(lista_ids):

    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_OCULTAS}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    conteudo = json.dumps({"ocultas": list(lista_ids)}, indent=2)

    encoded = base64.b64encode(conteudo.encode()).decode()

    payload = {
        "message": "Atualizando vagas ocultas",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)


def vagas_ocultas():
    return carregar_ocultas()


def ocultar_vaga(id):

    ocultas = carregar_ocultas()

    ocultas.add(id)

    salvar_ocultas(ocultas)


def restaurar_vaga(id):

    ocultas = carregar_ocultas()

    ocultas.discard(id)

    salvar_ocultas(ocultas)
    

def carregar_avaliacoes():
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_AVALIACOES}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return {"pendentes": [], "aprovadas": [], "excluidas": []}

    data = r.json()
    conteudo = base64.b64decode(data["content"]).decode()

    dados = json.loads(conteudo)

    # 🔥 garante estrutura
    if "excluidas" not in dados:
        dados["excluidas"] = []

    return dados
    

def salvar_avaliacoes(dados):
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_AVALIACOES}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    sha = r.json()["sha"] if r.status_code == 200 else None

    conteudo = json.dumps(dados, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(conteudo.encode()).decode()

    payload = {
        "message": "Atualizando avaliações",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)
    

def enviar_email_avaliacao(nome, comentario, estrelas):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY_CENTRAL}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Central de Vagas <onboarding@resend.dev>",
                "to": [EMAIL_USER_CENTRAL],
                "subject": "⭐ Nova avaliação recebida",
                "text": f"""
Nome: {nome}
Estrelas: {estrelas}
Comentário:
{comentario}
"""
            }
        )

        print("AVALIACAO EMAIL:", response.status_code)

    except Exception as e:
        print("Erro email avaliação:", e)
    

def carregar_contatos():
    url = f"https://api.github.com/repos/{REPO}/contents/contatos.json"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return {
            "contatos": [],
            "andamento": [],
            "resolvidos": [],
            "excluidos": []
        }

    data = r.json()
    conteudo = base64.b64decode(data["content"]).decode()

    dados = json.loads(conteudo)

    # garante estrutura
    for key in ["contatos", "andamento", "resolvidos", "excluidos"]:
        if key not in dados:
            dados[key] = []

    return dados
    

def salvar_contatos(dados):
    url = f"https://api.github.com/repos/{REPO}/contents/contatos.json"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    sha = r.json()["sha"] if r.status_code == 200 else None

    conteudo = json.dumps(dados, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(conteudo.encode()).decode()

    payload = {
        "message": "Atualizando contatos",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)


def enviar_email_contato(nome, tipo, mensagem):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY_CENTRAL}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Central de Vagas <onboarding@resend.dev>",  # depois pode trocar
                "to": [EMAIL_USER_CENTRAL],
                "subject": "Novo contato recebido - Central de Vagas",
                "text": f"Nome: {nome}\nTipo: {tipo}\nMensagem:\n{mensagem}"
            }
        )

        print("STATUS:", response.status_code)
        print("RESPOSTA:", response.text)

    except Exception as e:
        print("Erro ao enviar email:", e)
        

def carregar_vagas_pro():
    with open("vagas_pro.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def carregar_pro():
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_PRO}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return {"pendentes": [], "ativos": [], "expirados": []}

    data = r.json()
    conteudo = base64.b64decode(data["content"]).decode()

    return json.loads(conteudo)
    

def salvar_pro(dados):
    url = f"https://api.github.com/repos/{REPO}/contents/{ARQUIVO_PRO}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    sha = r.json()["sha"] if r.status_code == 200 else None

    conteudo = json.dumps(dados, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(conteudo.encode()).decode()

    payload = {
        "message": "Atualizando PRO",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)
    

def enviar_email_solicitacao_pro(nome, email, tipo, valor):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY_CENTRAL}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Central de Vagas <onboarding@resend.dev>",
                "to": [EMAIL_USER_CENTRAL],
                "subject": "💸 Nova compra realizada PRO",
                "text": f"""
Nome: {nome}
Email: {email}
Filtro: {tipo}
Valor: {valor}
"""
            }
        )

        print("PRO EMAIL:", response.status_code)

    except Exception as e:
        print("Erro email PRO:", e)


def enviar_email_confirmacao_pro(destinatario, nome):

    EMAIL = os.getenv("EMAIL_USER_CENTRAL")
    SENHA = os.getenv("EMAIL_PASS_CENTRAL")

    html = f"""
    <h2>💎 Pagamento confirmado!</h2>
    <p>Olá, <b>{nome}</b></p>
    <p>Seu acesso PRO está ativo 🚀</p>

    <hr>

    <p style="font-size:12px;color:#777;">
    📩 Este é um email automático, por favor não responda.<br>
    Para suporte, utilize a página de contato da plataforma.
    </p>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = "💎 Pagamento confirmado - Acesso PRO liberado"
    msg["From"] = f"Central de Vagas <{EMAIL}>"
    msg["To"] = f"{destinatario}, suporte.central.vagas@gmail.com"

    destinatarios = [destinatario, "suporte.central.vagas@gmail.com"]

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, SENHA)
        server.sendmail(EMAIL, destinatarios, msg.as_string())

    print("📧 enviado via Gmail")
    

def verificar_expiracao():
    dados = carregar_pro()
    agora = datetime.now()

    ativos = []
    expirados = dados["expirados"]

    mudou = False  # 🔥 CONTROLE

    for user in dados["ativos"]:
        if user["expira_em"]:
            data_exp = datetime.fromisoformat(user["expira_em"])

            if agora > data_exp:
                user["status"] = "expirado"
                expirados.append(user)
                mudou = True  # 🔥 marcou mudança
                continue

        ativos.append(user)

    if mudou:  # 🔥 SÓ SALVA SE PRECISAR
        dados["ativos"] = ativos
        dados["expirados"] = expirados
        salvar_pro(dados)


def verificar_aviso_expiracao():
    dados = carregar_pro()
    agora = datetime.now().date()

    mudou = False

    for user in dados["ativos"]:
        try:
            expira = datetime.fromisoformat(user["expira_em"]).date()
            dias_restantes = (expira - agora).days

            # 🔔 3 dias antes
            if dias_restantes == 3 and not user.get("aviso_3d"):
                enviar_email_aviso(user, "3dias")
                user["aviso_3d"] = True
                mudou = True

            # ⚠️ no dia
            if dias_restantes == 0 and not user.get("aviso_hoje"):
                enviar_email_aviso(user, "hoje")
                user["aviso_hoje"] = True
                mudou = True

        except Exception as e:
            print("Erro aviso:", e)

    if mudou:
        salvar_pro(dados)
        

def enviar_email_aviso(user, tipo):

    EMAIL = os.getenv("EMAIL_USER_CENTRAL")
    SENHA = os.getenv("EMAIL_PASS_CENTRAL")

    nome = user.get("nome", "")
    email = user.get("email")

    if tipo == "3dias":
        assunto = "⏳ Sua assinatura PRO expira em 3 dias"
        mensagem = f"""
        <p>Olá, <b>{nome}</b> 👋</p>
        <p>Sua assinatura PRO irá expirar em <b>3 dias</b>.</p>
        <p>Para continuar recebendo vagas exclusivas, recomendamos renovar agora.</p>
        """
    else:
        assunto = "⚠️ Sua assinatura PRO expira hoje"
        mensagem = f"""
        <p>Olá, <b>{nome}</b> 👋</p>
        <p>Seu acesso PRO expira <b>hoje</b>.</p>
        <p>Renove agora para não perder suas vagas personalizadas.</p>
        """

    html = f"""
    <div style="font-family:Arial;padding:20px;background:#f4f6f8;">
        <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:10px;">

            <h2 style="color:#0a66c2;">Central de Vagas PRO</h2>

            {mensagem}

            <div style="margin-top:20px;text-align:center;">
                <a href="https://central-vagas.onrender.com/pro"
                   style="
                       background:#0a66c2;
                       color:white;
                       padding:12px 18px;
                       text-decoration:none;
                       border-radius:6px;
                       font-size:14px;
                       display:inline-block;
                       font-weight:bold;
                   ">
                   💳 Renovar assinatura PRO
                </a>
            </div>

            <hr>

            <p style="font-size:12px;color:#777;">
                📩 Este é um email automático, por favor não responda.<br>
                Para suporte, utilize a plataforma.
            </p>

        </div>
    </div>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = assunto
    msg["From"] = f"Central de Vagas <{EMAIL}>"
    msg["To"] = f"{email}, suporte.central.vagas@gmail.com"

    destinatarios = [email, "suporte.central.vagas@gmail.com"]

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, SENHA)
            server.sendmail(EMAIL, destinatarios, msg.as_string())

        print("📧 aviso expiracao enviado via Gmail")

    except Exception as e:
        print("❌ erro envio aviso:", e)
    

def vagas_ativas():
    vagas = []
    ocultas = vagas_ocultas()

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:

                if vaga["id"] in ocultas:
                    continue

                titulo_lower = vaga["titulo"].lower()

                # 🔎 verifica se contém palavra bloqueada
                if any(p in titulo_lower for p in PALAVRAS_BLOQUEADAS):
                    continue  # ignora essa vaga

                vagas.append(vaga)

    except FileNotFoundError:
        pass
    return vagas


@app.route("/sobre")
def sobre():

    html = """
    <html>
    <head>
        <title>Sobre</title>

        <style>
            body {
                font-family: Arial;
                background: #f4f6f8;
                padding: 30px;
            }

            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            .top-buttons {
                margin-bottom: 20px;
            }

            .top-buttons a {
                background: #0066cc;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                text-decoration: none;
                margin-right: 10px;
                font-weight: bold;
            }

            .top-buttons a:hover {
                background: #004999;
            }
        </style>
    </head>

    <body>

        <div class="container">

            <div class="top-buttons">
                <a href="/">🏠 Vagas</a>
            </div>

            <h1>Sobre a Central de Vagas</h1>

            <p>
            A Central de Vagas foi criada para ajudar profissionais
            a encontrar oportunidades de forma rápida e centralizada.
            </p>

            <p>
            Nosso objetivo é facilitar o acesso às vagas e melhorar as chances
            de contratação dos candidatos, reunindo oportunidades em um só lugar.
            </p>

            <p>
            O projeto é independente e tem como missão simplificar o processo
            de busca por emprego, oferecendo uma experiência prática e eficiente.
            </p>

        </div>

    </body>
    </html>
    """

    return render_template_string(html)
    

@app.route("/contato")
def contato():

    html = """
    <html>
    <head>
        <title>Contato</title>
        <style>
            body { font-family: Arial; background:#f4f6f8; padding:30px; }

            .box {
                max-width:600px;
                margin:auto;
                background:white;
                padding:20px;
                border-radius:8px;
            }

            input, select, textarea {
                width:100%;
                padding:10px;
                margin-bottom:10px;
            }

            button {
                background:#0066cc;
                color:white;
                padding:10px;
                border:none;
                border-radius:5px;
            }

            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            .top-buttons {
                margin-bottom: 20px;
            }

            .top-buttons a {
                background: #0066cc;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                text-decoration: none;
                margin-right: 10px;
                font-weight: bold;
            }

            .top-buttons a:hover {
                background: #004999;
            }
        </style>
    </head>
    <body>

        <div class="container">

            <!-- ✅ MENSAGEM DE SUCESSO -->
            {% if request.args.get("msg") == "ok" %}
            <div id="msg-sucesso" style="
                background:#d4edda;
                color:#155724;
                padding:15px;
                border-radius:6px;
                margin-bottom:20px;
                font-weight:bold;
            ">
                ✅ Contato enviado com sucesso!
            </div>

            <script>
            setTimeout(() => {
                const msg = document.getElementById("msg-sucesso");
                if (msg) msg.style.display = "none";
            }, 4000);
            </script>
            {% endif %}

            <div class="top-buttons">
                <a href="/">🏠 Vagas</a>
            </div>

            <div class="box">

                <h2>📩 Entre em contato:</h2>

                <form method="POST" action="/enviar_contato">

                    <input name="nome" placeholder="Seu nome" required>
                    <input type="email" name="email" placeholder="Seu e-mail" required>

                    <select name="tipo">
                        <option value="sugestao">Sugestão</option>
                        <option value="problema">Problemas no Site</option>
                        <option value="problema_pro">Problemas na Assinatura PRO</option>
                    </select>

                    <textarea name="mensagem" placeholder="Escreva sua mensagem..." required></textarea>

                    <button type="submit">Enviar</button>

                </form>

            </div>

        </div>

    </body>
    </html>
    """

    return render_template_string(html)


@app.route("/privacidade")
def privacidade():

    html = """
    <html>
    <head>
        <title>Política de Privacidade</title>

        <style>
            body {
                font-family: Arial;
                background: #f4f6f8;
                padding: 30px;
            }

            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            .top-buttons a {
                background: #0066cc;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                text-decoration: none;
                margin-right: 10px;
            }
        </style>
    </head>

    <body>

        <div class="container">

            <div class="top-buttons">
                <a href="/">🏠 Vagas</a>
            </div>

            <h1>Política de Privacidade</h1>

            <p>
            A Central de Vagas respeita a sua privacidade e busca oferecer uma experiência
            segura e transparente para todos os usuários.
            </p>

            <h3>Coleta de informações</h3>
            <p>
            Podemos coletar informações como páginas acessadas, tempo de navegação
            e interações no site, com o objetivo de melhorar a experiência do usuário.
            </p>

            <h3>Uso de cookies</h3>
            <p>
            Este site utiliza cookies para melhorar a navegação do usuário
            e para exibir anúncios mais relevantes.
            </p>

            <h3>Google AdSense</h3>
            <p>
            Utilizamos serviços de terceiros, como o Google AdSense, que podem usar
            cookies para exibir anúncios com base nas visitas anteriores dos usuários.
            </p>

            <h3>Google Analytics</h3>
            <p>
            Utilizamos o Google Analytics para entender como os usuários interagem
            com o site e melhorar continuamente nossos serviços.
            </p>

            <h3>Compartilhamento de informações</h3>
            <p>
            As informações coletadas podem ser processadas por serviços de terceiros,
            como ferramentas de análise e publicidade, respeitando suas próprias
            políticas de privacidade.
            </p>

            <h3>Formulários</h3>
            <p>
            As informações enviadas pelos usuários através de formulários, como nome
            e mensagem, são utilizadas apenas para contato e melhoria do serviço,
            não sendo utilizadas para fins comerciais.
            </p>

            <h3>Contato</h3>
            <p>
            Caso tenha dúvidas, utilize a página de contato disponível no site.
            </p>

        </div>

    </body>
    </html>
    """

    return render_template_string(html)


@app.route("/pro_vagas")
def painel_pro():
    try:
        user_id = request.args.get("id")

        dados = carregar_pro()
        usuarios = dados.get("ativos", [])

        user = next((u for u in usuarios if u["id"] == user_id), None)

        if not user:
            return "Acesso inválido", 403

        vagas = carregar_vagas_pro()
        vagas = filtrar_vagas_usuario(vagas, user)

        html = get_html_home_pro()

        return render_template_string(
            html,
            vagas=vagas,
            total_vagas=len(vagas),
            total_empresas=0,
            empresas_unicas=[],
            busca_nome="",
            filtro_empresa="",
            ordem="recentes",
            page=1,
            total_paginas=1,
            admin=False,
            token="",
            avaliacoes=[],
            page_av=1,
            total_paginas_av=1,
            total_pendentes_av=0,
            total_contatos=0,
            total_pro_pendentes=0,
            total_ocultas=0
        )

    except Exception as e:
        return f"ERRO: {str(e)}"
    

@app.route("/pro")
def pro():

    html = """
    <html>
    <head>
        <title>Versão PRO</title>
        <style>
            body { font-family: Arial; background:#f4f6f8; padding:30px; }

            .box {
                max-width:600px;
                margin:auto;
                background:white;
                padding:25px;
                border-radius:8px;
            }

            input, select {
                width:100%;
                padding:10px;
                margin-bottom:10px;
            }

            button {
                background:#28a745;
                color:white;
                padding:10px;
                border:none;
                border-radius:5px;
            }
            
        </style>
    </head>
    <body>

    <div class="box">
        
        <h2>💎 Versão PRO</h2>

        <p>
        Receba vagas filtradas direto no seu email com base no seu perfil.
        </p>

        <form method="POST" action="/assinar_pro">

            <input name="nome" placeholder="Seu nome" required>
            <input type="email" name="email" placeholder="Seu email" required>

            <h3>🎯 Escolha como deseja receber suas vagas:</h3>

            <select name="tipo_filtro" id="tipo_filtro" onchange="mostrarCampos()" required>
                <option value="">Selecione</option>
                <option value="hierarquia">Por hierarquia</option>
                <option value="empresa">Por empresa</option>
            <option value="area">Por área</option>
            </select>

            <br><br>

            <!-- HIERARQUIA -->
            <div id="campo_hierarquia" style="display:none;">
                <p>📌 Você receberá vagas conforme a hierarquia escolhida</p>
                <select name="hierarquia">
                    <option value="">Selecione</option>
                    <option value="diretor">Diretor</option>
                    <option value="gerente">Gerente</option>
                    <option value="coordenador">Coordenador</option>
                    <option value="supervisor">Supervisor</option>
                    <option value="especialista">Especialista</option>
                    <option value="engenheiro">Engenheiro</option>
                    <option value="analista">Analista</option>
                    <option value="tecnico/inspetor/operador">Técnico/Inspetor/Operador</option>
                    <option value="auxiliar">Auxiliar/Assistente</option>
                    <option value="estagio">Estágio</option>
                    <option value="jovem_aprendiz">Jovem Aprendiz</option>                    
                </select>
            </div>

            <!-- EMPRESA -->
            <div id="campo_empresa" style="display:none;">
                <p style="margin-bottom:10px;">
                    📌 Você receberá vagas das empresas selecionadas
                </p>

                <button type="button" onclick="toggleEmpresas()" style="
                    margin-bottom:10px;
                    padding:6px 10px;
                    border:none;
                    background:#0a66c2;
                    color:white;
                    border-radius:6px;
                    cursor:pointer;
                    font-size:12px;
                ">
                    Selecionar todas
                </button>

                <div style="
                    max-height:200px;
                    overflow-y:auto;
                    border:1px solid #ddd;
                    border-radius:10px;
                    background:#fafafa;
                ">

                    {% for empresa in empresas %}
                        <label style="
                            display:flex;
                            align-items:center;
                            justify-content:space-between;
                            padding:10px 12px;
                            border-bottom:1px solid #eee;
                            cursor:pointer;
                            transition:background 0.2s;
                            gap:10px;
                        "
                        onmouseover="this.style.background='#f0f4ff'"
                        onmouseout="this.style.background=this.querySelector('input').checked ? '#e6f0ff' : 'transparent'">

                            <div style="
                                display:flex;
                                align-items:center;
                                gap:10px;
                            ">

                                <input 
                                    type="checkbox" 
                                    name="empresa" 
                                    value="{{ empresa }}"
                                    onchange="
                                        if(this.checked){
                                            this.closest('label').style.background='#e6f0ff';
                                            this.closest('label').style.fontWeight='bold';
                                            this.closest('label').querySelector('.check-icon').style.opacity='1';
                                        } else {
                                            this.closest('label').style.background='transparent';
                                            this.closest('label').style.fontWeight='normal';
                                            this.closest('label').querySelector('.check-icon').style.opacity='0';
                                        }
                                    "
                                >

                                <span style="
                                    font-size:14px;
                                    white-space: nowrap;
                                ">
                                    {{ empresa }}
                                </span>
                             </div>

                            <!-- check visual -->
                            <span class="check-icon" style="
                                font-size:12px;
                                color:#0a66c2;
                                opacity:0;
                                transition:0.2s;
                            ">
                                ✔
                            </span>

                        </label>
                    {% endfor %}

                </div>
            </div>

            <!-- ÁREA -->
            <div id="campo_area" style="display:none;">
                <p>📌 Você receberá vagas da área escolhida</p>
                <select name="area">
                    <option value="">Selecione</option>
                    <option value="manutencao">Manutenção</option>
                    <option value="producao">Produção</option>
                    <option value="produto">Produto</option>
                    <option value="projeto">Projetos</option>
                    <option value="operacao">Operação</option>
                    <option value="administracao">Administração</option>
                    <option value="marketing">Marketing</option>
                    <option value="qualidade">Qualidade/SMS/Químico</option>
                    <option value="logistica">Logística</option>
                    <option value="civil">Civil</option>
                </select>
            </div>

            <br>

            <button type="submit">Solicitar acesso PRO</button>

        </form>

        <script>
        function mostrarCampos() {
            let tipo = document.getElementById("tipo_filtro").value;

            document.getElementById("campo_hierarquia").style.display = "none";
            document.getElementById("campo_empresa").style.display = "none";
            document.getElementById("campo_area").style.display = "none";

            if (tipo === "hierarquia") {
                document.getElementById("campo_hierarquia").style.display = "block";
            }
            else if (tipo === "empresa") {
                document.getElementById("campo_empresa").style.display = "block";
            }
            else if (tipo === "area") {
                document.getElementById("campo_area").style.display = "block";
            }
        }
        </script>

        <script id="btz3lp">
        function toggleEmpresas() {
            const checkboxes = document.querySelectorAll('input[name="empresa"]');
            const botao = event.target;

            const todasSelecionadas = Array.from(checkboxes).every(cb => cb.checked);

            checkboxes.forEach(cb => {
                cb.checked = !todasSelecionadas;

                const label = cb.closest('label');

                if (!todasSelecionadas) {
                    label.style.background = '#e6f0ff';
                    label.style.fontWeight = 'bold';
                    label.querySelector('.check-icon').style.opacity = '1';
                } else {
                    label.style.background = 'transparent';
                    label.style.fontWeight = 'normal';
                    label.querySelector('.check-icon').style.opacity = '0';
                }
            });

            botao.innerText = todasSelecionadas ? "Selecionar todas" : "Desmarcar todas";
        }
        </script>

        <p style="margin-top:15px;font-size:12px;color:#555;">
        ⚠️ Pode haver dias sem envio de vagas, caso não existam novas oportunidades no perfil selecionado.
        </p>

        <p style="font-size:12px;color:#555;">
        Este serviço não garante contratação e não possui vínculo com empresas.
        </p>

        <a href="/">← Voltar para central</a>

    </div>

    </body>
    </html>
    """

    empresas = sorted(set(v["empresa"] for v in vagas_ativas()))

    return render_template_string(html, empresas=empresas)
    

def get_html_home_pro():
    return """
    <html>
    <head>
        <title>Central de Vagas Pro</title>

        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-LLTE9JPMLL"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-LLTE9JPMLL');
        </script>

        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2211390415336582"
            crossorigin="anonymous"></script>

        <style>
            body { font-family: Arial; background: #f4f6f8; padding: 30px; }
            h1 { color: #222; }

            .top-bar {
                display: flex;
                gap: 15px;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }

            .linkedin-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #0a66c2;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .linkedin-btn:hover { background: #084a8b; }

            .whatsapp-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #25D366;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .whatsapp-btn:hover { background: #1ebe5d; }

            .avaliar-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #28a745;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .avaliar-btn:hover { background: #218838; }

            .info-box {
                background: white;
                padding: 8px 15px;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                font-weight: bold;
                color: #333;
            }

            .filtro-box {
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            input, select {
                padding: 12px;
                border-radius: 5px;
                border: 1px solid #ccc;
                margin-right: 10px;
                min-width: 180px;
            }

            button {
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
                background: #0066cc;
                color: white;
                cursor: pointer;
            }

            button:hover { background: #004999; }

            .vaga {
                background: white;
                padding: 15px;
                margin-bottom: 12px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            .paginacao {
                margin-top: 20px;
            }

            .paginacao a {
                padding: 8px 12px;
                background: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-right: 5px;
            }

            .paginacao a:hover {
                background: #004999;
            }

            a.vaga-link {
                text-decoration: none;
                color: #0066cc;
                font-size: 18px;
            }

            .empresa { color: #555; margin-top: 5px; }

            textarea {
                width: 100%;
                height: 120px;
                resize: none; /* impede redimensionar */
            }
        </style>
    </head>
    <body>

        {% if request.args.get("msg") == "ok" %}
        <div id="msg-sucesso" style="
            background:#d4edda;
            color:#155724;
            padding:15px;
            border-radius:6px;
            margin-bottom:20px;
            font-weight:bold;
        ">
            ✅ Avaliação enviada com sucesso! Aguarde aprovação.
        </div>

        <script>
        setTimeout(() => {
            const msg = document.getElementById("msg-sucesso");
            if (msg) msg.style.display = "none";
        }, 4000);
        </script>
        {% endif %}

        <div style="margin-bottom:15px;">
            <a href="/"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;
                    border:1px solid #ddd;
                ">Vagas</a>

            <a href="/sobre"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Sobre</a>

            <a href="/contato"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Contato</a>

            <a href="/privacidade"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;                    
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Privacidade</a>

            <a href="/pro"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'" 
                style="
                    background:#fff3e0;
                    color:#ff9800;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    font-weight:normal;                
                    border:1px solid #ff9800;
                ">💎 Versão PRO</a>
                
        </div>

        <h1>Central de Vagas PRO - Engenharia / BA</h1>

        {% if admin %}
        <p>
        <a href="/admin/pro?admin={{token}}">
        💰 Gerenciar PRO  ({{ total_pro_pendentes }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/ocultas?admin={{token}}">
        ⚙️ Ver vagas ocultas  ({{ total_ocultas }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/avaliacoes?admin={{token}}">
        📝 Ver avaliações pendentes ({{ total_pendentes_av }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/contatos?admin={{token}}">
        📩 Ver solicitações de contato  ({{ total_contatos }})
        </a>
        </p>
        {% endif %}

        <div class="top-bar">

            <a href="https://www.linkedin.com/in/engandreycarlos/" target="_blank" class="linkedin-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8.5h4.5v15h-4.5v-15zm7.5 0h4.3v2.1h.1c.6-1.1 2-2.1 4.2-2.1 4.5 0 5.3 3 5.3 6.9v7h-4.5v-6.2c0-1.5-.03-3.5-2.2-3.5-2.2 0-2.5 1.7-2.5 3.4v6.3h-4.5v-15z"/>
                </svg>
                LinkedIn
            </a>

            <a href="https://chat.whatsapp.com/LedWVo8O6TSES0kG6smJcT?mode=gi_t" target="_blank" class="whatsapp-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M20.52 3.48A11.86 11.86 0 0012.01 0C5.38 0 .01 5.37.01 12c0 2.12.56 4.19 1.62 6.01L0 24l6.17-1.61A11.96 11.96 0 0012.01 24c6.63 0 12-5.37 12-12 0-3.2-1.25-6.2-3.49-8.52zM12 21.8c-1.8 0-3.55-.48-5.08-1.39l-.36-.21-3.66.96.98-3.57-.23-.37A9.8 9.8 0 012.2 12c0-5.4 4.4-9.8 9.8-9.8 2.62 0 5.08 1.02 6.93 2.87A9.74 9.74 0 0121.8 12c0 5.4-4.4 9.8-9.8 9.8zm5.39-7.35c-.3-.15-1.78-.88-2.06-.98-.28-.1-.48-.15-.68.15-.2.3-.78.98-.96 1.18-.18.2-.36.23-.66.08-.3-.15-1.26-.46-2.4-1.46-.89-.79-1.5-1.76-1.68-2.06-.18-.3-.02-.46.13-.6.14-.14.3-.36.46-.54.15-.18.2-.3.3-.5.1-.2.05-.38-.02-.53-.08-.15-.68-1.64-.93-2.24-.24-.58-.49-.5-.68-.51h-.58c-.2 0-.53.08-.8.38-.27.3-1.04 1.02-1.04 2.5s1.07 2.9 1.22 3.1c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.35.2 1.86.12.57-.08 1.78-.73 2.03-1.43.25-.7.25-1.3.18-1.43-.07-.13-.27-.2-.57-.35z"/>
                </svg>
                WhatsApp
            </a>

            <a href="#"
               onclick="document.getElementById('form-avaliacao').style.display='block'; return false;"
               class="avaliar-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M12 .587l3.668 7.431L24 9.748l-6 5.847 1.416 8.255L12 19.771l-7.416 4.079L6 15.595 0 9.748l8.332-1.73z"/>
                </svg>
                Avaliar página
            </a>

            <div class="info-box">
                📌 {{ total_vagas }} vagas encontradas
            </div>

            <div class="info-box">
                🏢 {{ total_empresas }} empresas monitoradas
            </div>

            <div class="vaga">
                <h3>💡 Dicas para conseguir emprego mais rápido</h3>

                <p>
                Muitas empresas utilizam plataformas automatizadas para recrutamento,
                como sistemas de triagem de currículos. 
                Para aumentar suas chances de aprovação nos processos seletivos:
                </p>

                <ul>
                    <li>Preencha seu currículo de forma completa e atualizada</li>
                    <li>Utilize palavras-chave relacionadas à vaga desejada</li>
                    <li>Evite erros de português e revise suas informações</li>
                    <li>Mantenha seu perfil sempre atualizado nas plataformas</li>
                    <li>Candidate-se rapidamente após a publicação da vaga</li>
                </ul>

                <p>
                Pequenos ajustes podem aumentar significativamente suas chances
                de ser chamado para entrevistas e avançar nas etapas do processo seletivo.
                </p>
                </div>

        </div>   
               
        <script>
            (adsbygoogle = window.adsbygoogle || []).push({});
        </script>

        <p>Projeto voluntário desenvolvido por <strong>Andrey Carlos</strong> para ajudar profissionais a se candidatarem.</p>

        <div id="form-avaliacao" style="display:none;background:white;padding:15px;border-radius:8px;margin-bottom:20px;">

        <form method="POST" action="/avaliar">

        <input name="nome" placeholder="Seu nome" required>

        <select name="status" onchange="toggleCampos(this.value)">
            <option value="recolocacao">Recolocação</option>
            <option value="empregado">Empregado</option>
        </select>

        <script>
        function toggleCampos(status) {
            const cargo = document.querySelector('input[name="cargo"]');
            const empresa = document.querySelector('input[name="empresa"]');

            if (status === "recolocacao") {
                cargo.disabled = true;
                empresa.disabled = true;
                cargo.value = "";
                empresa.value = "";
            } else {
                cargo.disabled = false;
                empresa.disabled = false;
            }
        }
        </script>

        <input name="cargo" placeholder="Cargo" disabled>
        <input name="empresa" placeholder="Empresa" disabled>

        <select name="estrelas" required>
            <option value="">Avaliação</option>
            <option value="5">⭐⭐⭐⭐⭐</option>
            <option value="4">⭐⭐⭐⭐</option>
            <option value="3">⭐⭐⭐</option>
            <option value="2">⭐⭐</option>
            <option value="1">⭐</option>
        </select>

        <textarea name="comentario" maxlength="300" placeholder="Comentário..." required></textarea>

        <button type="submit">Enviar avaliação</button>

        </form>
        </div>
        
        {% if vagas %}
            {% for vaga in vagas %}
                <div class="vaga">
                    <a href="/vaga/{{ vaga.id }}?redirect=1" target="_blank" class="vaga-link"
                       onclick="event.preventDefault();
                                gtag('event', 'click_vaga', {
                                    'vaga': '{{ vaga.titulo }}',
                                    'empresa': '{{ vaga.empresa }}',
                                    'origem': 'home'
                                });
                                setTimeout(() => {
                                    window.open(this.href, '_blank');
                                }, 150);">
                        <strong>{{ vaga.titulo }}</strong>
                    </a>  
                    <div class="empresa">
                        Empresa: {{ vaga.empresa }}
                    </div>

                    {% if admin %}
                    <a href="/ocultar/{{ vaga.id }}?admin={{token}}&page={{page}}&q={{busca_nome}}&empresa={{filtro_empresa}}&ordem={{ordem}}" style="color:red;font-size:12px;">
                    ocultar
                    </a>
                    {% endif %}

                </div>
            {% endfor %}
        {% else %}
            <p><em>Nenhuma vaga encontrada com esses filtros.</em></p>
        {% endif %}

        <div class="paginacao">
            {% if page > 1 %}
                <a href="?{% if admin %}admin={{token}}&{% endif %}page={{ page-1 }}&q={{ busca_nome }}&empresa={{ filtro_empresa }}&ordem={{ ordem }}">
                    ← Anterior
                </a>
            {% endif %}

            {% if page < total_paginas %}
                <a href="?{% if admin %}admin={{token}}&{% endif %}page={{ page+1 }}&q={{ busca_nome }}&empresa={{ filtro_empresa }}&ordem={{ ordem }}">
                    Próxima →
                </a>
            {% endif %}
            
        </div>

        <!-- banner_home_topo -->
        <ins class="adsbygoogle"
            style="display:block; width:300px;height:50px"
            data-ad-client="ca-pub-2211390415336582"
            data-ad-slot="8168087096"></ins>

        <h2>⭐ Avaliações</h2>

        {% for a in avaliacoes %}
        <div class="vaga">

        <strong>{{ a.nome }}</strong>

        <br>

        {{ "⭐" * (a.estrelas | int) }}

        <p>{{ a.comentario }}</p>

        {% if a.status == "empregado" %}
        <small>{{ a.cargo }} - {{ a.empresa }}</small>
        {% else %}
        <small>Em recolocação</small>
        {% endif %}

        </div>
        {% endfor %}

        <div class="paginacao">
        {% if page_av > 1 %}
        <a href="?page={{page}}&page_av={{ page_av-1 }}">← Anterior</a>
        {% endif %}

        {% if page_av < total_paginas_av %}
        <a href="?page={{page}}&page_av={{ page_av+1 }}">Próxima →</a>
        {% endif %}
        </div>

    </body>
    </html>
    """
    

def get_html_home():
    return """
    <html>
    <head>
        <title>Central de Vagas</title>

        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-LLTE9JPMLL"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-LLTE9JPMLL');
        </script>

        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2211390415336582"
            crossorigin="anonymous"></script>

        <style>
            body { font-family: Arial; background: #f4f6f8; padding: 30px; }
            h1 { color: #222; }

            .top-bar {
                display: flex;
                gap: 15px;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }

            .linkedin-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #0a66c2;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .linkedin-btn:hover { background: #084a8b; }

            .whatsapp-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #25D366;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .whatsapp-btn:hover { background: #1ebe5d; }

            .avaliar-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 180px;
                background: #28a745;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .avaliar-btn:hover { background: #218838; }

            .info-box {
                background: white;
                padding: 8px 15px;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                font-weight: bold;
                color: #333;
            }

            .filtro-box {
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            input, select {
                padding: 12px;
                border-radius: 5px;
                border: 1px solid #ccc;
                margin-right: 10px;
                min-width: 180px;
            }

            button {
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
                background: #0066cc;
                color: white;
                cursor: pointer;
            }

            button:hover { background: #004999; }

            .vaga {
                background: white;
                padding: 15px;
                margin-bottom: 12px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }

            .paginacao {
                margin-top: 20px;
            }

            .paginacao a {
                padding: 8px 12px;
                background: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-right: 5px;
            }

            .paginacao a:hover {
                background: #004999;
            }

            a.vaga-link {
                text-decoration: none;
                color: #0066cc;
                font-size: 18px;
            }

            .empresa { color: #555; margin-top: 5px; }

            textarea {
                width: 100%;
                height: 120px;
                resize: none; /* impede redimensionar */
            }
        </style>
    </head>
    <body>

        {% if request.args.get("msg") == "ok" %}
        <div id="msg-sucesso" style="
            background:#d4edda;
            color:#155724;
            padding:15px;
            border-radius:6px;
            margin-bottom:20px;
            font-weight:bold;
        ">
            ✅ Avaliação enviada com sucesso! Aguarde aprovação.
        </div>

        <script>
        setTimeout(() => {
            const msg = document.getElementById("msg-sucesso");
            if (msg) msg.style.display = "none";
        }, 4000);
        </script>
        {% endif %}

        <div style="margin-bottom:15px;">
            <a href="/"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;
                    border:1px solid #ddd;
                ">Vagas</a>

            <a href="/sobre"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Sobre</a>

            <a href="/contato"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Contato</a>

            <a href="/privacidade"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'"  
                style="
                    background:#f4f6f8;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    margin-right:8px;                    
                    font-weight:normal;                
                    border:1px solid #ddd;
                ">Privacidade</a>

            <a href="/pro"
                onmouseover="this.style.background='#0066cc'"
                onmouseout="this.style.background='#f4f6f8'" 
                style="
                    background:#fff3e0;
                    color:#ff9800;
                    padding:8px 12px;
                    border-radius:6px;
                    text-decoration:none;
                    font-weight:normal;                
                    border:1px solid #ff9800;
                ">💎 Versão PRO</a>
                
        </div>

        <h1>Central de Vagas - Engenharia / BA</h1>

        {% if admin %}
        <p>
        <a href="/admin/pro?admin={{token}}">
        💰 Gerenciar PRO  ({{ total_pro_pendentes }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/ocultas?admin={{token}}">
        ⚙️ Ver vagas ocultas  ({{ total_ocultas }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/avaliacoes?admin={{token}}">
        📝 Ver avaliações pendentes ({{ total_pendentes_av }})
        </a>
        </p>
        {% endif %}

        {% if admin %}
        <p>
        <a href="/admin/contatos?admin={{token}}">
        📩 Ver solicitações de contato  ({{ total_contatos }})
        </a>
        </p>
        {% endif %}

        <div class="top-bar">

            <a href="https://www.linkedin.com/in/engandreycarlos/" target="_blank" class="linkedin-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8.5h4.5v15h-4.5v-15zm7.5 0h4.3v2.1h.1c.6-1.1 2-2.1 4.2-2.1 4.5 0 5.3 3 5.3 6.9v7h-4.5v-6.2c0-1.5-.03-3.5-2.2-3.5-2.2 0-2.5 1.7-2.5 3.4v6.3h-4.5v-15z"/>
                </svg>
                LinkedIn
            </a>

            <a href="https://chat.whatsapp.com/LedWVo8O6TSES0kG6smJcT?mode=gi_t" target="_blank" class="whatsapp-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M20.52 3.48A11.86 11.86 0 0012.01 0C5.38 0 .01 5.37.01 12c0 2.12.56 4.19 1.62 6.01L0 24l6.17-1.61A11.96 11.96 0 0012.01 24c6.63 0 12-5.37 12-12 0-3.2-1.25-6.2-3.49-8.52zM12 21.8c-1.8 0-3.55-.48-5.08-1.39l-.36-.21-3.66.96.98-3.57-.23-.37A9.8 9.8 0 012.2 12c0-5.4 4.4-9.8 9.8-9.8 2.62 0 5.08 1.02 6.93 2.87A9.74 9.74 0 0121.8 12c0 5.4-4.4 9.8-9.8 9.8zm5.39-7.35c-.3-.15-1.78-.88-2.06-.98-.28-.1-.48-.15-.68.15-.2.3-.78.98-.96 1.18-.18.2-.36.23-.66.08-.3-.15-1.26-.46-2.4-1.46-.89-.79-1.5-1.76-1.68-2.06-.18-.3-.02-.46.13-.6.14-.14.3-.36.46-.54.15-.18.2-.3.3-.5.1-.2.05-.38-.02-.53-.08-.15-.68-1.64-.93-2.24-.24-.58-.49-.5-.68-.51h-.58c-.2 0-.53.08-.8.38-.27.3-1.04 1.02-1.04 2.5s1.07 2.9 1.22 3.1c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.35.2 1.86.12.57-.08 1.78-.73 2.03-1.43.25-.7.25-1.3.18-1.43-.07-.13-.27-.2-.57-.35z"/>
                </svg>
                WhatsApp
            </a>

            <a href="#"
               onclick="document.getElementById('form-avaliacao').style.display='block'; return false;"
               class="avaliar-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M12 .587l3.668 7.431L24 9.748l-6 5.847 1.416 8.255L12 19.771l-7.416 4.079L6 15.595 0 9.748l8.332-1.73z"/>
                </svg>
                Avaliar página
            </a>

            <div class="info-box">
                📌 {{ total_vagas }} vagas encontradas
            </div>

            <div class="info-box">
                🏢 {{ total_empresas }} empresas monitoradas
            </div>

            <div class="vaga">
                <h3>💡 Dicas para conseguir emprego mais rápido</h3>

                <p>
                Muitas empresas utilizam plataformas automatizadas para recrutamento,
                como sistemas de triagem de currículos. 
                Para aumentar suas chances de aprovação nos processos seletivos:
                </p>

                <ul>
                    <li>Preencha seu currículo de forma completa e atualizada</li>
                    <li>Utilize palavras-chave relacionadas à vaga desejada</li>
                    <li>Evite erros de português e revise suas informações</li>
                    <li>Mantenha seu perfil sempre atualizado nas plataformas</li>
                    <li>Candidate-se rapidamente após a publicação da vaga</li>
                </ul>

                <p>
                Pequenos ajustes podem aumentar significativamente suas chances
                de ser chamado para entrevistas e avançar nas etapas do processo seletivo.
                </p>
                </div>

        </div>   
               
        <script>
            (adsbygoogle = window.adsbygoogle || []).push({});
        </script>

        <div class="filtro-box">
            <form method="GET">
                <input type="text" name="q" placeholder="Pesquisar vaga..."
                       value="{{ busca_nome }}">

                <select name="empresa">
                    <option value="">Todas empresas</option>
                    {% for emp in empresas_unicas %}
                        <option value="{{ emp }}"
                        {% if emp == filtro_empresa %}selected{% endif %}>
                            {{ emp }}
                        </option>
                    {% endfor %}
                </select>


                <select name="ordem">
                    <option value="padrao" {% if ordem == "padrao" %}selected{% endif %}>
                        Padrão
                    </option>
                    <option value="recentes" {% if ordem == "recentes" %}selected{% endif %}>
                        Mais recentes
                    </option>
                    <option value="antigas" {% if ordem == "antigas" %}selected{% endif %}>
                        Mais antigas
                    </option>
                </select>


                <button type="submit">Filtrar</button>
            </form>
        </div>

        <p>Projeto voluntário desenvolvido por <strong>Andrey Carlos</strong> para ajudar profissionais a se candidatarem.</p>

        <div id="form-avaliacao" style="display:none;background:white;padding:15px;border-radius:8px;margin-bottom:20px;">

        <form method="POST" action="/avaliar">

        <input name="nome" placeholder="Seu nome" required>

        <select name="status" onchange="toggleCampos(this.value)">
            <option value="recolocacao">Recolocação</option>
            <option value="empregado">Empregado</option>
        </select>

        <script>
        function toggleCampos(status) {
            const cargo = document.querySelector('input[name="cargo"]');
            const empresa = document.querySelector('input[name="empresa"]');

            if (status === "recolocacao") {
                cargo.disabled = true;
                empresa.disabled = true;
                cargo.value = "";
                empresa.value = "";
            } else {
                cargo.disabled = false;
                empresa.disabled = false;
            }
        }
        </script>

        <input name="cargo" placeholder="Cargo" disabled>
        <input name="empresa" placeholder="Empresa" disabled>

        <select name="estrelas" required>
            <option value="">Avaliação</option>
            <option value="5">⭐⭐⭐⭐⭐</option>
            <option value="4">⭐⭐⭐⭐</option>
            <option value="3">⭐⭐⭐</option>
            <option value="2">⭐⭐</option>
            <option value="1">⭐</option>
        </select>

        <textarea name="comentario" maxlength="300" placeholder="Comentário..." required></textarea>

        <button type="submit">Enviar avaliação</button>

        </form>
        </div>
        
        {% if vagas %}
            {% for vaga in vagas %}
                <div class="vaga">
                    <a href="/vaga/{{ vaga.id }}?redirect=1" target="_blank" class="vaga-link"
                       onclick="event.preventDefault();
                                gtag('event', 'click_vaga', {
                                    'vaga': '{{ vaga.titulo }}',
                                    'empresa': '{{ vaga.empresa }}',
                                    'origem': 'home'
                                });
                                setTimeout(() => {
                                    window.open(this.href, '_blank');
                                }, 150);">
                        <strong>{{ vaga.titulo }}</strong>
                    </a>  
                    <div class="empresa">
                        Empresa: {{ vaga.empresa }}
                    </div>

                    {% if admin %}
                    <a href="/ocultar/{{ vaga.id }}?admin={{token}}&page={{page}}&q={{busca_nome}}&empresa={{filtro_empresa}}&ordem={{ordem}}" style="color:red;font-size:12px;">
                    ocultar
                    </a>
                    {% endif %}

                </div>
            {% endfor %}
        {% else %}
            <p><em>Nenhuma vaga encontrada com esses filtros.</em></p>
        {% endif %}

        <div class="paginacao">
            {% if page > 1 %}
                <a href="?{% if admin %}admin={{token}}&{% endif %}page={{ page-1 }}&q={{ busca_nome }}&empresa={{ filtro_empresa }}&ordem={{ ordem }}">
                    ← Anterior
                </a>
            {% endif %}

            {% if page < total_paginas %}
                <a href="?{% if admin %}admin={{token}}&{% endif %}page={{ page+1 }}&q={{ busca_nome }}&empresa={{ filtro_empresa }}&ordem={{ ordem }}">
                    Próxima →
                </a>
            {% endif %}
            
        </div>

        <!-- banner_home_topo -->
        <ins class="adsbygoogle"
            style="display:block; width:300px;height:50px"
            data-ad-client="ca-pub-2211390415336582"
            data-ad-slot="8168087096"></ins>

        <h2>⭐ Avaliações</h2>

        {% for a in avaliacoes %}
        <div class="vaga">

        <strong>{{ a.nome }}</strong>

        <br>

        {{ "⭐" * (a.estrelas | int) }}

        <p>{{ a.comentario }}</p>

        {% if a.status == "empregado" %}
        <small>{{ a.cargo }} - {{ a.empresa }}</small>
        {% else %}
        <small>Em recolocação</small>
        {% endif %}

        </div>
        {% endfor %}

        <div class="paginacao">
        {% if page_av > 1 %}
        <a href="?page={{page}}&page_av={{ page_av-1 }}">← Anterior</a>
        {% endif %}

        {% if page_av < total_paginas_av %}
        <a href="?page={{page}}&page_av={{ page_av+1 }}">Próxima →</a>
        {% endif %}
        </div>

    </body>
    </html>
    """
    

@app.route("/")
def home():    
    vagas = vagas_ativas()

    admin = request.args.get("admin") == ADMIN_TOKEN


    # ==========================
    # CAPTURA FILTROS
    # ==========================
    busca_nome = request.args.get("q", "").lower()
    filtro_empresa = request.args.get("empresa", "")
    ordem = request.args.get("ordem", "recentes") #padrao
    page = int(request.args.get("page", 1))  # ✅ ADICIONADO

    # ==========================
    # APLICA FILTROS
    # ==========================
    if busca_nome:
        palavras_busca = busca_nome.split()

        vagas = [
            v for v in vagas
            if any(p in v["titulo"].lower() for p in palavras_busca)
        ]

    if filtro_empresa:
        empresas = filtro_empresa.split(",")

        vagas = [
            v for v in vagas
            if v["empresa"] in empresas
        ]

    # ==========================
    # ORDENAÇÃO
    # ==========================
    try:
        # ✅ ORDEM ALFABÉTICA SOMENTE SE NÃO HOUVER FILTRO NEM ORDEM NA URL
        if ordem == "padrao":
            vagas.sort(key=lambda v: v["titulo"].lower())
        else:
            vagas.sort(
                key=lambda v: datetime.fromisoformat(v["data_coleta"]) if v.get("data_coleta") else datetime.min,
                reverse=(ordem == "recentes")
            )
    except:
        pass


    total_vagas = len(vagas)

    # ==========================
    # PAGINAÇÃO
    # ==========================
    inicio = (page - 1) * VAGAS_POR_PAGINA
    fim = inicio + VAGAS_POR_PAGINA
    vagas = vagas[inicio:fim]

    total_paginas = (total_vagas + VAGAS_POR_PAGINA - 1) // VAGAS_POR_PAGINA

    empresas_unicas = sorted(set(v["empresa"] for v in vagas_ativas()))
    total_empresas = len(empresas_unicas)

    avaliacoes = carregar_avaliacoes()["aprovadas"]

    # ordena mais recentes primeiro
    avaliacoes.sort(key=lambda a: a["data"], reverse=True)

    # pega só as 5

    AVALIACOES_POR_PAGINA = 3
    page_av = int(request.args.get("page_av", 1))

    inicio = (page_av - 1) * AVALIACOES_POR_PAGINA
    fim = inicio + AVALIACOES_POR_PAGINA

    avaliacoes_paginadas = avaliacoes[inicio:fim]

    total_paginas_av = (len(avaliacoes) + AVALIACOES_POR_PAGINA - 1) // AVALIACOES_POR_PAGINA

    dados_av = carregar_avaliacoes()
    total_pendentes_av = len(dados_av["pendentes"])

    dados_cont = carregar_contatos()
    total_contatos = len(dados_cont["contatos"])

    dados_pro = carregar_pro()
    total_pro_pendentes = len(dados_pro["pendentes"])

    ocultas = vagas_ocultas()
    total_ocultas = len(ocultas)

    html = get_html_home()  # 🔥 AGORA VEM DA FUNÇÃO

    return render_template_string(
        html,
        vagas=vagas,
        total_vagas=total_vagas,
        total_empresas=total_empresas,
        empresas_unicas=empresas_unicas,
        busca_nome=request.args.get("q", ""),
        filtro_empresa=filtro_empresa,
        ordem=ordem,
        page=page,
        total_paginas=total_paginas,
        admin=admin,
        token=ADMIN_TOKEN,
        avaliacoes=avaliacoes_paginadas,
        page_av=page_av,
        total_paginas_av=total_paginas_av,
        total_pendentes_av=total_pendentes_av,
        total_contatos=total_contatos,
        total_pro_pendentes=total_pro_pendentes,
        total_ocultas=total_ocultas
    )


@app.route("/ocultar/<id>")
def ocultar(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    ocultar_vaga(id)

    page = request.args.get("page", 1)
    q = request.args.get("q", "")
    empresa = request.args.get("empresa", "")
    ordem = request.args.get("ordem", "recentes")

    return redirect(f"/?admin={ADMIN_TOKEN}&page={page}&q={q}&empresa={empresa}&ordem={ordem}")


@app.route("/restaurar/<id>")
def restaurar(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    restaurar_vaga(id)

    return redirect("/?admin=" + ADMIN_TOKEN)
    

@app.route("/admin/ocultas")
def admin_ocultas():

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    ocultas = vagas_ocultas()
    vagas = []

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for vaga in reader:
                if vaga["id"] in ocultas:
                    vagas.append(vaga)

    except:
        pass

    html = """
    <html>
    <head>
        <title>Vagas Ocultas</title>
    </head>
    <body>

    <h2>Vagas ocultadas</h2>

    <a href="/?admin={{token}}">← voltar</a>

    <hr>

    {% for vaga in vagas %}

        <p>

        <strong>{{ vaga.titulo }}</strong><br>
        Empresa: {{ vaga.empresa }}<br>

        <a href="/restaurar/{{vaga.id}}?admin={{token}}" style="color:green;">
        restaurar
        </a>

        </p>

        <hr>

    {% endfor %}

    {% if not vagas %}
    <p>Nenhuma vaga ocultada.</p>
    {% endif %}

    </body>
    </html>
    """

    return render_template_string(
        html,
        vagas=vagas,
        token=ADMIN_TOKEN
    )
    

@app.route("/avaliar", methods=["POST"])
def avaliar():
    nome = request.form.get("nome")
    comentario = request.form.get("comentario")
    estrelas = int(request.form.get("estrelas", 0))
    status = request.form.get("status")
    cargo = request.form.get("cargo")
    empresa = request.form.get("empresa")

    if not nome or not comentario or estrelas == 0:
        return "Preencha os campos obrigatórios"

    if len(comentario) > 300:
        return "Comentário muito grande (máx 300 caracteres)"

    nova = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "comentario": comentario,
        "estrelas": estrelas,
        "status": status,
        "cargo": cargo,
        "empresa": empresa,
        "data": datetime.now().isoformat()
    }

    dados = carregar_avaliacoes()
    dados["pendentes"].append(nova)

    salvar_avaliacoes(dados)

    enviar_email_avaliacao(nome, comentario, estrelas)

    return redirect("/?msg=ok")


@app.route("/admin/avaliacoes")
def admin_avaliacoes():
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_avaliacoes()

    html = """
    <a href="/?admin={{token}}">← voltar</a>

    <h2>Pendentes</h2>

    {% for a in pendentes %}
        <p>
        {{ a.nome }} - {{ a.comentario }}
        <br>
        <a href="/aprovar/{{a.id}}?admin={{token}}">Aprovar</a>
        </p>
    {% endfor %}

    <hr>

    <h2>Aprovadas</h2>

    {% for a in aprovadas %}
        <p>
        {{ a.nome }} - {{ a.comentario }}
        <br>
        <a href="/excluir_avaliacao/{{a.id}}?admin={{token}}" style="color:red;">
        Excluir
        </a>
        </p>
        {% endfor %}

    <hr>

    <h2>Excluídas</h2>

    {% for a in excluidas %}
        <p>
        {{ a.nome }} - {{ a.comentario }}
        <br>
        <a href="/restaurar_avaliacao/{{a.id}}?admin={{token}}" style="color:green;">
        Restaurar
        </a>
        </p>
        {% endfor %}
    """

    return render_template_string(html,
    pendentes=dados["pendentes"],
    aprovadas=dados["aprovadas"],
    excluidas=dados["excluidas"],
    token=ADMIN_TOKEN
)

@app.route("/excluir_avaliacao/<id>")
def excluir_avaliacao(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_avaliacoes()

    for a in dados["aprovadas"]:
        if a["id"] == id:
            dados["aprovadas"].remove(a)
            dados["excluidas"].append(a)
            break

    salvar_avaliacoes(dados)

    return redirect("/admin/avaliacoes?admin=" + ADMIN_TOKEN)

@app.route("/aprovar/<id>")
def aprovar(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_avaliacoes()

    for a in dados["pendentes"]:
        if a["id"] == id:
            dados["pendentes"].remove(a)
            dados["aprovadas"].append(a)
            break

    salvar_avaliacoes(dados)

    return redirect("/admin/avaliacoes?admin=" + ADMIN_TOKEN)
    
    
@app.route("/enviar_contato", methods=["POST"])
def enviar_contato():

    nome = request.form.get("nome")
    tipo = request.form.get("tipo")
    mensagem = request.form.get("mensagem")

    novo = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "tipo": tipo,
        "mensagem": mensagem,
        "data": datetime.now().isoformat()
    }

    dados = carregar_contatos()
    dados["contatos"].append(novo)

    salvar_contatos(dados)

    # 🔥 NÃO BLOQUEIA O SITE
    #threading.Thread(target=enviar_email_contato,args=(nome, tipo, mensagem)).start()
    enviar_email_contato(nome, tipo, mensagem)
    #print("SIMULANDO ENVIO DE EMAIL")
    #print(nome, tipo, mensagem)

    return redirect("/contato?msg=ok")
    

@app.route("/admin/contatos")
def admin_contatos():

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_contatos()

    html = """
    <a href="/?admin={{token}}">← voltar</a>

    <h2>📥 Contatos recebidos</h2>
    {% for c in contatos %}
        <p>
        <strong>{{ c.nome }}</strong><br>
        {{ c.mensagem }}<br>
        <a href="/andamento/{{c.id}}?admin={{token}}">Mover p/ andamento</a>
        </p><hr>
    {% endfor %}

    <h2>🔄 Em andamento</h2>
    {% for c in andamento %}
        <p>
        <strong>{{ c.nome }}</strong><br>
        <a href="/resolver/{{c.id}}?admin={{token}}">Resolver</a>
        </p><hr>
    {% endfor %}

    <h2>✅ Resolvidos</h2>
    {% for c in resolvidos %}
        <p>
        <strong>{{ c.nome }}</strong><br>
        <a href="/excluir_contato/{{c.id}}?admin={{token}}">Excluir</a>
        </p><hr>
    {% endfor %}

    <h2>🗑️ Excluídos</h2>
    {% for c in excluidos %}
        <p>
        <strong>{{ c.nome }}</strong><br>
        <a href="/restaurar_contato/{{c.id}}?admin={{token}}">Restaurar</a>
        </p><hr>
    {% endfor %}
    """

    return render_template_string(
        html,
        contatos=dados["contatos"],
        andamento=dados["andamento"],
        resolvidos=dados["resolvidos"],
        excluidos=dados["excluidos"],
        token=ADMIN_TOKEN
    )
    

@app.route("/andamento/<id>")
def mover_andamento(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_contatos()

    for c in dados["contatos"]:
        if c["id"] == id:
            dados["contatos"].remove(c)
            dados["andamento"].append(c)
            break

    salvar_contatos(dados)
    return redirect("/admin/contatos?admin=" + ADMIN_TOKEN)
    

@app.route("/resolver/<id>")
def resolver(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_contatos()

    for c in dados["andamento"]:
        if c["id"] == id:
            dados["andamento"].remove(c)
            dados["resolvidos"].append(c)
            break

    salvar_contatos(dados)
    return redirect("/admin/contatos?admin=" + ADMIN_TOKEN)
    

@app.route("/excluir_contato/<id>")
def excluir_contato(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_contatos()

    for c in dados["resolvidos"]:
        if c["id"] == id:
            dados["resolvidos"].remove(c)
            dados["excluidos"].append(c)
            break

    salvar_contatos(dados)
    return redirect("/admin/contatos?admin=" + ADMIN_TOKEN)
    

@app.route("/restaurar_contato/<id>")
def restaurar_contato(id):
    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_contatos()

    for c in dados["excluidos"]:
        if c["id"] == id:
            dados["excluidos"].remove(c)
            dados["contatos"].append(c)
            break

    salvar_contatos(dados)
    return redirect("/admin/contatos?admin=" + ADMIN_TOKEN)
    

@app.route("/assinar_pro", methods=["POST"])
def assinar_pro():

    nome = request.form.get("nome")
    email = request.form.get("email")
    tipo = request.form.get("tipo_filtro")

    valor = None

    if tipo == "hierarquia":
        valor = request.form.get("hierarquia")

    elif tipo == "empresa":
        valor = request.form.getlist("empresa")

    elif tipo == "area":
        valor = request.form.get("area")

    # ✅ VALIDAÇÃO
    if not nome or not email or not tipo or not valor:
        return "Selecione corretamente o filtro"

    novo = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "email": email,
        "tipo_filtro": tipo,
        "valor": valor,
        "status": "pendente",
        "data_inicio": None,
        "expira_em": None,
        "data_criacao": datetime.now().isoformat()
    }

    dados = carregar_pro()
    dados["pendentes"].append(novo)

    salvar_pro(dados)

    enviar_email_solicitacao_pro(nome, email, tipo, valor)

    return """
    <h2>✅ Solicitação recebida!</h2>

    <p>Para ativar seu acesso PRO:</p>

    <p><strong>PIX:</strong> seuemail@gmail.com FASE DE TESTE</p>
    <p><strong>Valor:</strong> R$ 9,90</p>

    <p>Após o pagamento, você começará a receber as vagas filtradas.</p>

    <a href="/">← Voltar</a>
    """


@app.route("/admin/pro")
def admin_pro():

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_pro()

    html = """
    <a href="/?admin={{token}}">← voltar</a>

    <h2>💰 Pendentes</h2>
    {% for u in pendentes %}
        <p>
        {{ u.nome }} - {{ u.email }}
        <br>
        <a href="/ativar_pro/{{u.id}}?admin={{token}}">✅ Ativar</a><br>
        <a href="/excluir_pro/{{u.id}}?admin={{token}} "onclick="return confirm('Tem certeza que deseja excluir este usuário?')" style="color:red;">🗑️ Excluir</a>
        </p>
        <hr>
    {% endfor %}

    <h2>🚀 Ativos</h2>
    {% for u in ativos %}
        <p>
        {{ u.nome }} - expira em {{ u.expira_em }}
        <br>
        <a href="/expirar_pro/{{u.id}}?admin={{token}}" style="color:red;">Expirar</a><br>
        <a href="/excluir_pro/{{u.id}}?admin={{token}}" onclick="return confirm('Tem certeza que deseja excluir este usuário?')" style="color:red;">🗑️ Excluir</a>
        </p>
        <hr>
    {% endfor %}

    <h2>⛔ Expirados</h2>
    {% for u in expirados %}
        <p>
        {{ u.nome }}
        <br>
        <a href="/reativar_pro/{{u.id}}?admin={{token}}" style="color:green;">Reativar</a><br>
        <a href="/excluir_pro/{{u.id}}?admin={{token}}" onclick="return confirm('Tem certeza que deseja excluir este usuário?')" style="color:red;">🗑️ Excluir</a>
        </p>
        <hr>
    {% endfor %}
    """

    return render_template_string(
        html,
        pendentes=dados["pendentes"],
        ativos=dados["ativos"],
        expirados=dados["expirados"],
        token=ADMIN_TOKEN
    )
    
    
@app.route("/ativar_pro/<id>")
def ativar_pro(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_pro()

    for u in dados["pendentes"]:
        if str(u["id"]) == str(id):

            print("ATIVANDO USUARIO:", u["email"])

            dados["pendentes"].remove(u)

            u["status"] = "ativo"
            u["data_inicio"] = datetime.now().isoformat()
            u["expira_em"] = (datetime.now() + timedelta(days=30)).isoformat()

            dados["ativos"].append(u)

            # 🔥 ENVIA EMAIL AQUI
            try:
                enviar_email_confirmacao_pro(
                    u["email"],
                    u.get("nome", "")
                )
            except Exception as e:
                print("Erro ao enviar confirmação:", e)

            break

    salvar_pro(dados)

    return redirect("/admin/pro?admin=" + ADMIN_TOKEN)
    

@app.route("/expirar_pro/<id>")
def expirar_pro(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_pro()

    for u in dados["ativos"]:
        if u["id"] == id:
            dados["ativos"].remove(u)

            u["status"] = "expirado"
            dados["expirados"].append(u)
            break

    salvar_pro(dados)

    return redirect("/admin/pro?admin=" + ADMIN_TOKEN)
    

@app.route("/reativar_pro/<id>")
def reativar_pro(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_pro()

    for u in dados["expirados"]:
        if u["id"] == id:
            dados["expirados"].remove(u)

            u["status"] = "ativo"
            u["data_inicio"] = datetime.now().isoformat()
            u["expira_em"] = (datetime.now() + timedelta(days=30)).isoformat()

            dados["ativos"].append(u)
            break

    salvar_pro(dados)

    return redirect("/admin/pro?admin=" + ADMIN_TOKEN)
    

@app.route("/excluir_pro/<id>")
def excluir_pro(id):

    if request.args.get("admin") != ADMIN_TOKEN:
        return "Acesso negado"

    dados = carregar_pro()

    # 🔥 percorre todas as listas
    for chave in ["pendentes", "ativos", "expirados"]:
        for u in dados[chave]:
            if str(u["id"]) == str(id):
                print(f"🗑️ Excluindo usuário {u['email']} de {chave}")
                dados[chave].remove(u)
                salvar_pro(dados)
                return redirect("/admin/pro?admin=" + ADMIN_TOKEN)

    return "Usuário não encontrado"


@app.route("/ads.txt")
def ads_txt():
    return "google.com, pub-2211390415336582, DIRECT, f08c47fec0942fa0", 200, {
        'Content-Type': 'text/plain'
    }
    

@app.route("/vaga/<id>")
def vaga(id):

    redirect_mode = request.args.get("redirect") == "1"

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["id"] == id:

                    # 🔥 Se for clique interno → redireciona direto
                    if redirect_mode:
                        return redirect(vaga["link"])

                    # 🔥 Se for link compartilhado → mostra página
                    html = """
                    <html>
                    <head>
                        <title>{{ vaga.titulo }}</title>
                        <!-- Google tag (gtag.js) -->
                        <script async src="https://www.googletagmanager.com/gtag/js?id=G-LLTE9JPMLL"></script>
                        <script>
                          window.dataLayer = window.dataLayer || [];
                          function gtag(){dataLayer.push(arguments);}
                          gtag('js', new Date());
                          gtag('config', 'G-LLTE9JPMLL');
                        </script>
                        <meta property="og:title" content="{{ vaga.titulo }}">
                        <meta property="og:description" content="Veja essa vaga na Central de Vagas">
                        <meta property="og:type" content="website">
                    </head>
                    <body style="font-family: Arial; padding: 30px; background:#f4f6f8;">

                        <div style="background:white;padding:20px;border-radius:8px;max-width:600px;margin:auto;">
                            
                            <h2>{{ vaga.titulo }}</h2>

                            <p><strong>Empresa:</strong> {{ vaga.empresa }}</p>

                            <h3>📌 Sobre esta vaga</h3>

                            <p>
                            Esta vaga foi coletada automaticamente pela Central de Vagas para facilitar sua busca por oportunidades.
                            </p>

                            <p>
                            Recomendamos que o candidato leia atentamente os requisitos da vaga
                            e mantenha seu currículo atualizado antes de se candidatar.
                            </p>

                            <h3>💡 Dica</h3>

                            <p>
                            Para aumentar suas chances, adapte seu currículo com palavras-chave
                            da descrição da vaga e destaque experiências relevantes.
                            </p>

                            <br>

                            <a href="{{ vaga.link }}" target="_blank"
                               onclick="event.preventDefault();
                                        gtag('event', 'click_vaga', {
                                            'vaga': '{{ vaga.titulo }}',
                                            'empresa': '{{ vaga.empresa }}',
                                            'origem': 'pagina_vaga'
                                        });
                                        setTimeout(() => {
                                            window.open(this.href, '_blank');
                                        }, 150);"
                               style="background:#0066cc;color:white;padding:12px 20px;
                                      text-decoration:none;border-radius:6px;display:inline-flex;align-items:center;gap:8px;min-width:180px;">
                                🚀 Ir para candidatura
                            </a>

                            <br><br>

                            <a href="https://www.linkedin.com/in/engandreycarlos/" target="_blank"
                                style="background:#0a66c2;color:white;padding:12px 20px;
                                    text-decoration:none;border-radius:6px;display:inline-flex;align-items:center;gap:8px;min-width:180px;">
                                    
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                                    <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8.5h4.5v15h-4.5v-15zm7.5 0h4.3v2.1h.1c.6-1.1 2-2.1 4.2-2.1 4.5 0 5.3 3 5.3 6.9v7h-4.5v-6.2c0-1.5-.03-3.5-2.2-3.5-2.2 0-2.5 1.7-2.5 3.4v6.3h-4.5v-15z"/>
                                </svg>
                            LinkedIn
                            </a>

                            <br><br>

                            <a href="https://chat.whatsapp.com/LedWVo8O6TSES0kG6smJcT?mode=gi_t" target="_blank" 
                                style="background:#25D366;color:white;padding:12px 20px;
                                    text-decoration:none;border-radius:6px;display:inline-flex;align-items:center;gap:8px;min-width:180px;">

                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                                    <path d="M20.52 3.48A11.86 11.86 0 0012.01 0C5.38 0 .01 5.37.01 12c0 2.12.56 4.19 1.62 6.01L0 24l6.17-1.61A11.96 11.96 0 0012.01 24c6.63 0 12-5.37 12-12 0-3.2-1.25-6.2-3.49-8.52zM12 21.8c-1.8 0-3.55-.48-5.08-1.39l-.36-.21-3.66.96.98-3.57-.23-.37A9.8 9.8 0 012.2 12c0-5.4 4.4-9.8 9.8-9.8 2.62 0 5.08 1.02 6.93 2.87A9.74 9.74 0 0121.8 12c0 5.4-4.4 9.8-9.8 9.8zm5.39-7.35c-.3-.15-1.78-.88-2.06-.98-.28-.1-.48-.15-.68.15-.2.3-.78.98-.96 1.18-.18.2-.36.23-.66.08-.3-.15-1.26-.46-2.4-1.46-.89-.79-1.5-1.76-1.68-2.06-.18-.3-.02-.46.13-.6.14-.14.3-.36.46-.54.15-.18.2-.3.3-.5.1-.2.05-.38-.02-.53-.08-.15-.68-1.64-.93-2.24-.24-.58-.49-.5-.68-.51h-.58c-.2 0-.53.08-.8.38-.27.3-1.04 1.02-1.04 2.5s1.07 2.9 1.22 3.1c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.35.2 1.86.12.57-.08 1.78-.73 2.03-1.43.25-.7.25-1.3.18-1.43-.07-.13-.27-.2-.57-.35z"/>
                                </svg>
                            Entrar no grupo
                            </a>

                            <br><br>

                            <p>Projeto voluntário desenvolvido por <strong>Andrey Carlos</strong></p>

                            <a href="/">← Voltar para central</a>

                        </div>

                    </body>
                    </html>
                    """

                    return render_template_string(html, vaga=vaga)

    except FileNotFoundError:
        pass

    return "Vaga não encontrada ou encerrada", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
