# Execução com Docker

## Requisitos

- Docker com o plugin Compose.

## Iniciar o protótipo

A partir da raiz do repositório:

```bash
docker compose -f docker/compose.yaml up --build
```

Depois do healthcheck dos serviços:

- Frontend: <http://localhost:8080>
- Backend: <http://localhost:8000>

O frontend encaminha as requisições em `/api/` para o backend. As migrations são
aplicadas automaticamente antes do Gunicorn iniciar, e o banco SQLite fica no volume
nomeado `frete-fechado_backend_data`.

## Configuração opcional

As portas e a chave do Django podem ser configuradas por variáveis de ambiente:

```bash
FRONTEND_PORT=3000 \
BACKEND_PORT=8001 \
DJANGO_SECRET_KEY='substitua-esta-chave' \
docker compose -f docker/compose.yaml up --build
```

Os serviços escutam apenas na interface local (`127.0.0.1`) por padrão.

## Verificar e encerrar

```bash
docker compose -f docker/compose.yaml ps
docker compose -f docker/compose.yaml down
```

Para também remover os dados persistidos do SQLite:

```bash
docker compose -f docker/compose.yaml down --volumes
```
