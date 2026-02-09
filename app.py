#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
from flask import Flask, redirect, render_template_string

app = Flask(__name__)

vagas = {
    "dados-jr": {
        "titulo": "Analista de Dados Júnior",
        "link": "https://www.linkedin.com/jobs/view/123"
    },
    "devops-pl": {
        "titulo": "DevOps Pleno",
        "link": "https://www.linkedin.com/jobs/view/456"
    }
}

@app.route("/")
def home():
    html = """
    <h1>Central de Vagas - Engenharia / Tech</h1>
    <p>Projeto voluntário para ajudar profissionais a se candidatarem.</p>
    <ul>
        {% for key, vaga in vagas.items() %}
            <li>
                <a href="/vaga/{{ key }}">{{ vaga.titulo }}</a>
            </li>
        {% endfor %}
    </ul>
    """
    return render_template_string(html, vagas=vagas)

@app.route("/vaga/<id>")
def vaga(id):
    if id in vagas:
        return redirect(vagas[id]["link"])
    return "Vaga não encontrada", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

