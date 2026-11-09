# ✂️ Encurtador de URLs API

API REST que transforma links longos em links curtos, com alias personalizado e
contagem de cliques. Feita com Python, Flask e SQLite.

## O que demonstra
- Design de API REST (verbos HTTP e status codes corretos: 201, 400, 404, 409)
- Application factory do Flask (facilita testes e configuração)
- Validação de entrada (bloqueia esquemas perigosos como `javascript:`)
- SQL parametrizado (proteção contra SQL injection)
- Geração segura de códigos com `secrets`
- Testes de integração com o test client do Flask

## Instalação
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Endpoints
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/links` | Cria link `{"url": "...", "alias": "opcional"}` |
| GET | `/api/links` | Lista todos |
| GET | `/api/links/<codigo>` | Detalhes e cliques |
| DELETE | `/api/links/<codigo>` | Remove |
| GET | `/<codigo>` | Redireciona (302) e conta o clique |

## Exemplo
```bash
curl -X POST http://127.0.0.1:5000/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "alias": "gh"}'
# acesse http://127.0.0.1:5000/gh
```

## Testes
```bash
python -m unittest discover -v
```

## Ideias de evolução
Autenticação com token, expiração de links, rate limiting, Docker, deploy.
