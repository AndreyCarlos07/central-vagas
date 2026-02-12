#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
import csv
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)

CSV_FILE = "vagas.csv"


def vagas_ativas():
    vagas = []
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                vagas.append(vaga)
    except FileNotFoundError:
        pass
    return vagas


@app.route("/")
def home():
    vagas = vagas_ativas()

    # ==========================
    # CAPTURA FILTROS
    # ==========================
    busca_nome = request.args.get("q", "").lower()
    filtro_empresa = request.args.get("empresa", "")

    # ==========================
    # APLICA FILTROS
    # ==========================
    if busca_nome:
        vagas = [
            v for v in vagas
            if busca_nome in v["titulo"].lower()
        ]

    if filtro_empresa:
        vagas = [
            v for v in vagas
            if v["empresa"] == filtro_empresa
        ]

    total_vagas = len(vagas)
    empresas_unicas = sorted(set(v["empresa"] for v in vagas_ativas()))
    total_empresas = len(empresas_unicas)

    html = """
    <html>
    <head>
        <title>Central de Vagas</title>
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
                gap: 8px;
                background: #0a66c2;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }

            .linkedin-btn:hover { background: #084a8b; }

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
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #ccc;
                margin-right: 10px;
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

            a.vaga-link {
                text-decoration: none;
                color: #0066cc;
                font-size: 18px;
            }

            .empresa { color: #555; margin-top: 5px; }
        </style>
    </head>
    <body>

        <h1>Central de Vagas - Engenharia / Tech</h1>

        <div class="top-bar">

            <a href="https://www.linkedin.com/in/engandreycarlos/" target="_blank" class="linkedin-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 24 24">
                    <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.2 8.5h4.5v15h-4.5v-15zm7.5 0h4.3v2.1h.1c.6-1.1 2-2.1 4.2-2.1 4.5 0 5.3 3 5.3 6.9v7h-4.5v-6.2c0-1.5-.03-3.5-2.2-3.5-2.2 0-2.5 1.7-2.5 3.4v6.3h-4.5v-15z"/>
                </svg>
                Me siga no LinkedIn
            </a>

            <div class="info-box">
                📌 {{ total_vagas }} vagas encontradas
            </div>

            <div class="info-box">
                🏢 {{ total_empresas }} empresas monitoradas
            </div>

        </div>

        <!-- FILTRO -->
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

                <button type="submit">Filtrar</button>
            </form>
        </div>

        <p>Projeto voluntário desenvolvido por <strong>Andrey Carlos</strong> para ajudar profissionais a se candidatarem.</p>
        
        {% if vagas %}
            {% for vaga in vagas %}
                <div class="vaga">
                    <a href="/vaga/{{ vaga.id }}" target="_blank" class="vaga-link">
                        <strong>{{ vaga.titulo }}</strong>
                    </a>
                    <div class="empresa">
                        Empresa: {{ vaga.empresa }}
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p><em>Nenhuma vaga encontrada com esses filtros.</em></p>
        {% endif %}

    </body>
    </html>
    """

    return render_template_string(
        html,
        vagas=vagas,
        total_vagas=total_vagas,
        total_empresas=total_empresas,
        empresas_unicas=empresas_unicas,
        busca_nome=request.args.get("q", ""),
        filtro_empresa=filtro_empresa
    )


@app.route("/vaga/<id>")
def vaga(id):
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for vaga in reader:
                if vaga["id"] == id:
                    return redirect(vaga["link"])
    except FileNotFoundError:
        pass

    return "Vaga não encontrada ou encerrada", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)    
