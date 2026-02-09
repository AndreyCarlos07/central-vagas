#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
import csv
from datetime import datetime
from flask import Flask, redirect, render_template_string

app = Flask(__name__)

CSV_FILE = "vagas.csv"

def vagas_ativas():
    hoje = datetime.today().date()
    vagas = []

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                expira = datetime.strptime(vaga["expira_em"], "%Y-%m-%d").date()
                if expira >= hoje:
                    vagas.append(vaga)
    except FileNotFoundError:
        pass

    return vagas

@app.route("/")
def home():
    vagas = vagas_ativas()

    html = """
    <h1>Central de Vagas - Engenharia / Tech</h1>
    <p>Projeto voluntário para ajudar profissionais a se candidatarem.</p>

    {% if vagas %}
        <ul>
        {% for vaga in vagas %}
            <li>
                <a href="/vaga/{{ vaga.id }}">
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
    return render_template_string(html, vagas=vagas)

@app.route("/vaga/<id>")
def vaga(id):
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for vaga in reader:
            if vaga["id"] == id:
                return redirect(vaga["link"])
    return "Vaga não encontrada ou expirada", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



