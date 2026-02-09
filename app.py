#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
from datetime import datetime
from flask import Flask, redirect, render_template_string

app = Flask(__name__)

# ===== BASE DE VAGAS =====
vagas = {
    "dados-jr": {
        "titulo": "Analista de Ativos Pleno - Divisão 14",
        "empresa": "BYD",
        "link": "https://bydbrasil.gupy.io/jobs/10534672?jobBoardSource=gupy_public_page",
        "publicada_em": "2025-12-17",
        "expira_em": "2026-02-14"
    },
    "devops-pl": {
        "titulo": "DevOps Pleno",
        "empresa": "Empresa Y",
        "link": "https://www.linkedin.com/jobs/view/456",
        "publicada_em": "2026-01-15",
        "expira_em": "2026-02-05"
    }
}

# ===== FILTRA VAGAS ATIVAS =====
def vagas_ativas():
    hoje = datetime.today().date()
    ativas = {}

    for key, vaga in vagas.items():
        expira = datetime.strptime(vaga["expira_em"], "%Y-%m-%d").date()
        if expira >= hoje:
            ativas[key] = vaga

    return ativas

# ===== PÁGINA PRINCIPAL =====
@app.route("/")
def home():
    vagas_validas = vagas_ativas()

    html = """
    <h1>Central de Vagas - Engenharia / Tech</h1>
    <p>Projeto voluntário para ajudar profissionais a se candidatarem.</p>

    {% if vagas %}
        <ul>
        {% for key, vaga in vagas.items() %}
            <li>
                <a href="/vaga/{{ key }}">
                    <strong>{{ vaga.titulo }}</strong>
                </a><br>
                Empresa: {{ vaga.empresa }}<br>
                Publicada em: {{ vaga.publicada_em }}<br>
                Expira em: {{ vaga.expira_em }}
            </li>
            <br>
        {% endfor %}
        </ul>
    {% else %}
        <p><em>Nenhuma vaga ativa no momento.</em></p>
    {% endif %}
    """

    return render_template_string(html, vagas=vagas_validas)

# ===== REDIRECIONAMENTO DA VAGA =====
@app.route("/vaga/<id>")
def vaga(id):
    vagas_validas = vagas_ativas()

    if id in vagas_validas:
        return redirect(vagas_validas[id]["link"])

    return "Vaga não encontrada ou expirada", 404

# ===== START APP =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


