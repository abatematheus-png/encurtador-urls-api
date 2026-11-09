import os
import tempfile
import unittest

from app import create_app, url_valida


class TestAPI(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app(self.path).test_client()

    def tearDown(self):
        os.remove(self.path)

    def criar(self, **kw):
        return self.client.post("/api/links", json=kw)

    def test_criar_link(self):
        r = self.criar(url="https://example.com/pagina")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.json["codigo"]), 6)
        self.assertEqual(r.json["cliques"], 0)

    def test_url_invalida(self):
        self.assertEqual(self.criar(url="javascript:alert(1)").status_code, 400)
        self.assertEqual(self.criar(url="nao-e-url").status_code, 400)
        self.assertEqual(self.client.post("/api/links", data="x").status_code, 400)

    def test_alias_personalizado_e_duplicado(self):
        self.assertEqual(self.criar(url="https://a.com", alias="meu-link").status_code, 201)
        self.assertEqual(self.criar(url="https://b.com", alias="meu-link").status_code, 409)

    def test_alias_invalido(self):
        self.assertEqual(self.criar(url="https://a.com", alias="a b").status_code, 400)

    def test_redirecionamento_conta_cliques(self):
        codigo = self.criar(url="https://example.com", alias="exe").json["codigo"]
        r = self.client.get(f"/{codigo}")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers["Location"], "https://example.com")
        self.client.get(f"/{codigo}")
        self.assertEqual(self.client.get(f"/api/links/{codigo}").json["cliques"], 2)

    def test_nao_encontrado(self):
        self.assertEqual(self.client.get("/naoexiste").status_code, 404)
        self.assertEqual(self.client.get("/api/links/naoexiste").status_code, 404)

    def test_listar_e_remover(self):
        self.criar(url="https://a.com", alias="aaa")
        self.assertEqual(len(self.client.get("/api/links").json), 1)
        self.assertEqual(self.client.delete("/api/links/aaa").status_code, 204)
        self.assertEqual(self.client.delete("/api/links/aaa").status_code, 404)

    def test_url_valida(self):
        self.assertTrue(url_valida("http://x.com"))
        self.assertFalse(url_valida("ftp://x.com"))


if __name__ == "__main__":
    unittest.main()
