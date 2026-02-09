#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
import csv
from flask import Flask, redirect, render_template_string

app = Flask(__name__)

CSV_FILE = "vagas.csv"


def vagas_ativas():
    vagas = []

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                # só mostra vaga ativa
                if vaga.get("ativa") == "1":
                    vagas.append(vaga)
    except FileNotFoundError:
        pass

    return vagas


@app.route("/")
def home():
    vagas = vagas_ativas()

    html = """
    <html>
    <head>
        <title>Central de Vagas</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                padding: 30px;
            }
            h1 {
                color: #222;
            }
            .vaga {
                background: white;
                padding: 15px;
                margin-bottom: 12px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }
            a {
                text-decoration: none;
                color: #0066cc;
                font-size: 18px;
            }
            a:hover {
                text-decoration: underline;
            }
            .empresa {
                color: #555;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>

        <h1>Central de Vagas - Engenharia / Tech</h1>
        <p>Projeto voluntário para ajudar profissionais a se candidatarem.</p>

        {% if vagas %}
            {% for vaga in vagas %}
                <div class="vaga">
                    <a href="/vaga/{{ vaga.id }}" target="_blank">
                        <strong>{{ vaga.titulo }}</strong>
                    </a>
                    <div class="empresa">
                        Empresa: {{ vaga.empresa }}
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p><em>Nenhuma vaga ativa no momento.</em></p>
        {% endif %}

    </body>
    </html>
    """

    return render_template_string(html, vagas=vagas)


@app.route("/vaga/<id>")
def vaga(id):
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["id"] == id and vaga.get("ativa") == "1":
                    return redirect(vaga["link"])
    except FileNotFoundError:
        pass

    return "Vaga não encontrada ou encerrada", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



