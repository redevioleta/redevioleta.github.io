# Deploy do backend no Azure (Container Apps + PostgreSQL)

O site estático continua no **GitHub Pages** (`https://redevioleta.github.io/`). Apenas a API FastAPI roda no
**Azure Container Apps**, com **Azure Database for PostgreSQL Flexible Server** como banco persistente.
Nada é provisionado automaticamente por este repositório.

## Pré-requisitos manuais

- Assinatura Azure com permissão de Owner/Contributor + User Access Administrator no resource group
  (o Bicep cria uma role assignment `AcrPull`).
- Provedores registrados: `Microsoft.App`, `Microsoft.OperationalInsights`, `Microsoft.ContainerRegistry`,
  `Microsoft.DBforPostgreSQL`, `Microsoft.ManagedIdentity`.
- Azure CLI (`az`) logado, com a extensão `containerapp` e Bicep.
- Senha forte para o admin do PostgreSQL e (opcional) a chave `GEMINI_API_KEY`.
- Permissão de admin no repositório GitHub para criar a variável de Actions `REDE_VIOLETA_API_BASE`.

## Recursos criados (`infra/main.bicep`)

Log Analytics, Container Registry (Basic, sem admin user), identidade gerenciada *user-assigned* (com `AcrPull`
para baixar a imagem sem senha), ambiente Container Apps, PostgreSQL Flexible Server (Burstable B1ms, v16,
backup de 7 dias) + banco `redevioleta`, e o Container App com ingress HTTPS externo, probes de
startup/liveness/readiness em `/health` e secrets `database-url` e `gemini-api-key`.

## Passo a passo

```bash
RG=rede-violeta-rg
az group create -n $RG -l brazilsouth

# 1) Infra base (sem o app). A senha vem de variável de ambiente/prompt, nunca de arquivo versionado.
read -rs PG_PASSWORD
az deployment group create -g $RG -f infra/main.bicep \
  -p postgresAdminPassword="$PG_PASSWORD" deployApp=false
ACR=$(az deployment group show -g $RG -n main --query properties.outputs.acrName.value -o tsv)

# 2) Build e push da imagem (a partir da raiz do repositório)
az acr build -r $ACR -t rede-violeta-api:latest backend/

# 3) Cria o Container App
read -rs GEMINI_API_KEY   # opcional; deixe vazio para só usar respostas locais
az deployment group create -g $RG -f infra/main.bicep \
  -p postgresAdminPassword="$PG_PASSWORD" geminiApiKey="$GEMINI_API_KEY" deployApp=true \
  --query properties.outputs.apiBaseUrl.value -o tsv
```

A saída do passo 3 é a **URL da API** (`https://<app>.<região>.azurecontainerapps.io/api/v1`).
Verifique: `curl https://<app>.<região>.azurecontainerapps.io/health`.

## Configurações do backend

| Variável | Descrição |
|---|---|
| `PORT` | Porta de escuta (padrão `8000`; o Container App usa `8000`). |
| `DATABASE_URL` | URL SQLAlchemy. `postgres://` e `postgresql://` são convertidas para o driver `psycopg` (v3). Use `?sslmode=require`. Secret `database-url` no Container App. Sem ela, usa SQLite local (somente desenvolvimento). |
| `CORS_ORIGINS` | Allowlist separada por vírgula. Deve conter `https://redevioleta.github.io` (padrão). Sem curingas. |
| `GEMINI_API_KEY` | Secret `gemini-api-key` (opcional). |
| `GEMINI_MODEL` | Padrão `gemini-2.5-flash`. |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | Provedor alternativo compatível com OpenAI (opcional). |

Schema/dados: ao iniciar, o contêiner executa `seed.py`, que cria as tabelas (`create_all`) e popula dados
iniciais de forma idempotente. Por isso `maxReplicas` é 1 por padrão. Para mudanças de schema futuras, adote
Alembic.

## Apontar o GitHub Pages para a API

No repositório: *Settings → Secrets and variables → Actions → Variables → New repository variable*:

- Nome: `REDE_VIOLETA_API_BASE`
- Valor: `https://<app>.<região>.azurecontainerapps.io/api/v1`

Não é um secret (a URL é pública). Faça push em `main` (ou reexecute o workflow "Deploy GitHub Pages"):
ele gera `config.js` com o valor, validando que é uma URL `https`. Se a variável não estiver definida, o
workflow emite um aviso e o site usa apenas as respostas locais (sem backend).
Localmente, abrir `index.html` via `file://` continua usando `http://127.0.0.1:8000/api/v1`.

## Rodar localmente

```bash
cd backend
pip install -r requirements.txt
python seed.py && uvicorn app.main:app --reload
# ou com contêiner (SQLite em /tmp apenas para teste):
docker build -t rede-violeta-api .
docker run --rm -p 8000:8000 -e DATABASE_URL=sqlite:////tmp/rv.db rede-violeta-api
```

## Segurança e próximos passos

- O firewall do PostgreSQL permite apenas serviços do Azure (`0.0.0.0`). Para isolamento maior, use VNet
  integration + Private Endpoint e, idealmente, autenticação Microsoft Entra no banco (hoje usa senha de admin,
  guardada como secret do Container App).
- Os secrets ficam nos parâmetros do deployment (marcados `@secure`); considere Key Vault referenciado pela
  identidade gerenciada.
