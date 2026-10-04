# Fala Segura — Backend (FastAPI)

Backend do site Fala Segura, campanha Agosto Lilás, com apoio e
conscientização sobre assédio e violência contra a mulher.

## Estrutura

app/
main.py
core/
config.py
db/
database.py
models/
models.py
schemas/
schemas.py
api/
api.py
routes/
desabafos.py
assedio.py
denuncias.py
quiz.py
recursos.py
faq.py
timeline.py
delegacias.py
alertas.py
chat.py
services/

Cada aba do site virou um módulo de rota próprio — fica fácil de mexer
em uma parte sem afetar as outras, e cada pessoa consegue trabalhar
num arquivo diferente sem conflito.

## Como rodar

python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
uvicorn app.main:app --reload
A API sobe em `http://localhost:8000`. A documentação interativa
(Swagger) fica automaticamente em `http://localhost:8000/docs`.

## Sobre o banco de dados

Por padrão o projeto está configurado para usar **SQLite local**
(`fala_segura.db`), só para você já poder rodar e testar a API sem
depender de nada externo.

Os models em `app/models/models.py` são um **rascunho inicial** —
criei um para cada aba do site, com os campos que pareciam fazer
sentido pelo que você me contou do projeto. Quando seu amigo definir
o banco de verdade, os pontos de integração são:

1. `app/core/config.py` → trocar `database_url` pela string de conexão
   real (ex: Postgres, MySQL).
2. `app/models/models.py` → ajustar os models para bater com o schema
   que ele desenhar (nomes de tabela, colunas, relacionamentos, etc).
3. Se o banco já existir com nomes diferentes, é só editar essa
   classes — o resto da API (rotas, schemas) não precisa mudar muito,
   só os campos que os schemas expõem.

Nada na lógica das rotas depende de SQLite especificamente — trocar
o banco é basicamente trocar a `database_url` e ajustar os models.

## Violeta IA (chat com IA generativa)

A rota `POST /api/v1/chat/` conecta o chat "Violeta" a uma IA generativa
real, compatível com a API da OpenAI (funciona com OpenAI, Groq,
OpenRouter, etc.). Para ativar, crie um arquivo `.env` em `backend/`
com:

```env
OPENAI_API_KEY=sua-chave-aqui
# Opcionais (têm valor padrão):
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Se `OPENAI_API_KEY` não estiver definida (ou a chamada à IA falhar por
qualquer motivo — sem internet, chave inválida, timeout, etc.), o
backend cai automaticamente para respostas locais por palavra-chave,
então o chat continua funcionando mesmo sem IA configurada.

Em mensagens com sinais de perigo imediato (ex.: "socorro", "ele está
aqui", "ameaça"), a resposta de segurança (190/180) é sempre gerada
localmente, sem depender da IA externa — por segurança, essa parte
nunca é delegada ao modelo de linguagem.

Além do acolhimento geral, a Violeta IA foi instruída (e o fallback
local também cobre, nos três idiomas) a explicar:

- os tipos de violência previstos na Lei Maria da Penha (física,
  psicológica, sexual, patrimonial, moral);
- o passo a passo para denunciar (190, 180, DEAM/Boletim de Ocorrência,
  Defensoria Pública/medida protetiva, IML);
- como reunir e guardar provas (prints, fotos, áudios, testemunhas);
- como ajudar uma pessoa próxima que esteja sofrendo violência, sem
  julgamento e sem colocar ninguém em risco.

Nenhuma mensagem de chat é salva no banco de dados: o histórico de
conversa trafega apenas dentro da própria requisição (enviado pelo
frontend) e não é persistido no servidor.

## Próximos passos sugeridos

Autenticação (se for necessário login para alguma aba, tipo admin
  de denúncias)
Popular `recursos`, `faq`, `linha_do_tempo` e `delegacias` com dados
  reais (são majoritariamente tabelas de leitura)
Considerar Alembic para migrações assim que o banco definitivo
  estiver definido, em vez de `Base.metadata.create_all`
