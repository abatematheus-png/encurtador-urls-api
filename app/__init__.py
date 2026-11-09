"""Encurtador de URLs - API REST com Flask e SQLite."""
import re
import secrets
import sqlite3
import string
from urllib.parse import urlparse

from flask import Flask, g, jsonify, redirect, request

ALFABETO = string.ascii_letters + string.digits
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")


def url_valida(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc) and len(url) <= 2048


def gerar_codigo(tamanho: int = 6) -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(tamanho))


def create_app(db_path: str = "links.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def fechar_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().execute(
            """CREATE TABLE IF NOT EXISTS links (
                codigo TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                cliques INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        get_db().commit()

    def serializar(row) -> dict:
        return {
            "codigo": row["codigo"],
            "url": row["url"],
            "url_curta": f"{request.host_url}{row['codigo']}",
            "cliques": row["cliques"],
            "criado_em": row["criado_em"],
        }

    @app.post("/api/links")
    def criar():
        dados = request.get_json(silent=True) or {}
        url = (dados.get("url") or "").strip()
        alias = dados.get("alias")
        if not url_valida(url):
            return jsonify(erro="URL inválida. Use http:// ou https://."), 400
        if alias is not None and not ALIAS_RE.match(alias):
            return jsonify(erro="Alias deve ter 3-32 caracteres (letras, números, _ ou -)."), 400
        db = get_db()
        for _ in range(5):  # tenta de novo em caso raro de colisão
            codigo = alias or gerar_codigo()
            try:
                db.execute("INSERT INTO links (codigo, url) VALUES (?, ?)", (codigo, url))
                db.commit()
                break
            except sqlite3.IntegrityError:
                if alias:
                    return jsonify(erro="Alias já está em uso."), 409
        else:
            return jsonify(erro="Não foi possível gerar um código."), 500
        row = db.execute("SELECT * FROM links WHERE codigo = ?", (codigo,)).fetchone()
        return jsonify(serializar(row)), 201

    @app.get("/api/links")
    def listar():
        rows = get_db().execute("SELECT * FROM links ORDER BY criado_em DESC, rowid DESC").fetchall()
        return jsonify([serializar(r) for r in rows])

    @app.get("/api/links/<codigo>")
    def detalhes(codigo):
        row = get_db().execute("SELECT * FROM links WHERE codigo = ?", (codigo,)).fetchone()
        if row is None:
            return jsonify(erro="Link não encontrado."), 404
        return jsonify(serializar(row))

    @app.delete("/api/links/<codigo>")
    def remover(codigo):
        db = get_db()
        cur = db.execute("DELETE FROM links WHERE codigo = ?", (codigo,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify(erro="Link não encontrado."), 404
        return "", 204

    @app.get("/<codigo>")
    def redirecionar(codigo):
        db = get_db()
        row = db.execute("SELECT url FROM links WHERE codigo = ?", (codigo,)).fetchone()
        if row is None:
            return jsonify(erro="Link não encontrado."), 404
        db.execute("UPDATE links SET cliques = cliques + 1 WHERE codigo = ?", (codigo,))
        db.commit()
        return redirect(row["url"], code=302)

    return app
