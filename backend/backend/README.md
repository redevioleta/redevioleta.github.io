# Fala Segura — Backend (FastAPI)

Backend do site **Fala Segura**, campanha Agosto Lilás, com apoio e
conscientização sobre assédio e violência contra a mulher.

## Estrutura

```
app/
├── main.py              # entrypoint, cria o app e registra rotas
├── core/
│   └── config.py        # configurações (nome do app, URL do banco, etc)
├── db/
│   └── database.py      # engine, sessão e Base do SQLAlchemy
├── models/
│   └── models.py        # modelos de banco (RASCUNHO — seu amigo revisa)
├── schemas/
│   └── schemas.py        # schemas Pydantic (validação de entrada/saída)
├── api/
│   ├── api.py            # junta todas as rotas num só router
│   └── routes/
│       ├── desabafos.py
│       ├── assedio.py
│       ├── denuncias.py
│       ├── quiz.py
│       ├── recursos.py
│       ├── faq.py
│       ├── timeline.py
│       ├── delegacias.py
│       └── alertas.py
└── services/             # espaço para lógica de negócio mais complexa depois
```

Cada aba do site virou um módulo de rota próprio — fica fácil de mexer
em uma parte sem afetar as outras, e cada pessoa consegue trabalhar
num arquivo diferente sem conflito.

## Como rodar

```bash
python -m venv venv
source venv/bin/activate   # no Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

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

## Próximos passos sugeridos

- Autenticação (se for necessário login para alguma aba, tipo admin
  de denúncias)
- Popular `recursos`, `faq`, `linha_do_tempo` e `delegacias` com dados
  reais (são majoritariamente tabelas de leitura)
- Considerar Alembic para migrações assim que o banco definitivo
  estiver definido, em vez de `Base.metadata.create_all`
