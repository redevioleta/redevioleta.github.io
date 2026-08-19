# Requirements Document

## Introduction

O projeto **Fala Segura** é um MVP de plataforma de apoio a vítimas de violência e assédio. O backend já conta com FastAPI (Python), SQLAlchemy e SQLite (`fala_segura.db`). Este documento especifica os requisitos para estruturar e implementar adequadamente o banco de dados do projeto, garantindo que todos os modelos estejam corretamente definidos, que os dados iniciais (seed) possam ser carregados de forma idempotente e que a camada de acesso a dados seja consistente e íntegra.

Os módulos abrangidos são: **alertas comunitários**, **identificação de assédio**, **delegacias**, **denúncias**, **desabafos**, **FAQ**, **quiz**, **recursos** e **linha do tempo**.

---

## Glossary

- **Sistema**: A aplicação backend Fala Segura em FastAPI.
- **DB**: O banco de dados SQLite (`fala_segura.db`) gerenciado pelo SQLAlchemy.
- **Sessão**: Uma instância de `SessionLocal` do SQLAlchemy utilizada por um request HTTP.
- **Migration**: Processo de criação ou alteração de tabelas no DB a partir dos modelos SQLAlchemy.
- **Seed**: Processo de inserção de dados iniciais e estáticos no DB.
- **Modelo**: Classe SQLAlchemy que mapeia uma tabela do DB.
- **Schema**: Classe Pydantic que define a estrutura de entrada ou saída da API.
- **Rota**: Endpoint FastAPI que manipula requests HTTP para um módulo específico.
- **DEAM**: Delegacia Especializada no Atendimento à Mulher.
- **Quiz**: Conjunto de perguntas para ajudar o usuário a identificar situações de risco.
- **FAQ**: Perguntas frequentes com respostas sobre direitos e procedimentos.
- **Desabafo**: Registro de texto livre enviado pelo usuário, opcionalmente anônimo.
- **Denúncia**: Relato formal de violência ou assédio registrado pelo usuário.
- **Recurso**: Informação sobre serviço de apoio externo (telefone, link, categoria).
- **Alerta Comunitário**: Aviso geolocalizado criado por usuários sobre situações de risco.
- **Linha do Tempo**: Sequência cronológica de marcos legislativos sobre violência de gênero no Brasil.

---

## Requirements

### Requisito 1: Inicialização e Estrutura do Banco de Dados

**User Story:** Como desenvolvedor, quero que o banco de dados seja criado e inicializado automaticamente ao iniciar a aplicação, para que o ambiente esteja pronto sem intervenção manual.

#### Critérios de Aceitação

1. WHEN a aplicação Fala Segura é iniciada, THE Sistema SHALL criar todas as tabelas definidas nos Modelos no DB caso elas ainda não existam, sem remover ou alterar tabelas já existentes.
2. IF a criação das tabelas falhar durante a inicialização, THEN THE Sistema SHALL registrar a mensagem de erro no console e encerrar o processo com código de saída não-zero, impedindo que a aplicação suba em estado inconsistente.
3. WHEN um request HTTP é recebido, THE Sistema SHALL abrir uma nova sessão de DB dedicada a esse request e encerrá-la ao final do request, independentemente de sucesso ou erro, garantindo que nenhuma sessão seja reutilizada entre requests distintos.
4. WHEN um request HTTP encerra com erro não tratado, THE Sistema SHALL realizar rollback da sessão antes de encerrá-la, evitando persistência parcial de dados.
5. WHEN a variável de ambiente `DATABASE_URL` está definida, THE Sistema SHALL utilizar seu valor como URL de conexão com o DB.
6. IF a variável de ambiente `DATABASE_URL` não está definida, THEN THE Sistema SHALL utilizar o caminho padrão `sqlite:///./fala_segura.db` como URL de conexão.
7. IF a URL de conexão referenciar SQLite, THEN THE Sistema SHALL configurar o parâmetro `check_same_thread=False` para permitir uso multithreaded do FastAPI.

---

### Requisito 2: Modelo de Desabafos

**User Story:** Como usuária da plataforma, quero registrar um desabafo de forma anônima ou identificada, para que meu relato seja armazenado com segurança.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar desabafos com os campos: `id` (inteiro, chave primária, auto-incremento), `texto` (até 5.000 caracteres, obrigatório), `anonimo` (booleano, padrão `true`) e `criado_em` (data/hora UTC, gerado automaticamente no momento da inserção).
2. IF uma requisição de criação de desabafo omite o campo `texto` ou envia `texto` vazio, THEN THE Sistema SHALL rejeitar a operação e retornar HTTP 422.
3. WHEN uma requisição de criação de desabafo é recebida sem o campo `anonimo`, THE Sistema SHALL registrar o desabafo com `anonimo = true`.
4. WHEN um desabafo é criado com sucesso, THE Sistema SHALL retornar o `id` e o `criado_em` gerado no DB na resposta HTTP 201.

---

### Requisito 3: Modelo de Identificação de Assédio

**User Story:** Como usuária da plataforma, quero descrever uma situação e receber uma classificação, para que eu possa entender se a situação configura assédio.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar registros de identificação de assédio na tabela `identificacoes_assedio` com os campos: `id` (inteiro, chave primária), `descricao_situacao` (texto longo, obrigatório), `resultado` (texto curto, opcional) e `criado_em` (data/hora com fuso horário, gerado automaticamente pelo DB).
2. WHEN um registro de identificação de assédio é criado, THE Sistema SHALL aceitar o campo `resultado` como nulo, a ser preenchido por lógica de negócio posterior.

---

### Requisito 4: Modelo de Denúncias

**User Story:** Como usuária da plataforma, quero registrar uma denúncia com descrição, local e contato opcional, para que o relato seja preservado e rastreado por status.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar denúncias com os campos: `id` (inteiro, chave primária, auto-incremento), `descricao` (até 5.000 caracteres, obrigatório), `local` (até 255 caracteres, opcional), `anonimo` (booleano, padrão `true`), `contato` (até 255 caracteres, opcional), `status` (até 20 caracteres, padrão `"recebida"`) e `criado_em` (data/hora UTC, gerado automaticamente no momento da inserção).
2. IF uma requisição de criação ou atualização de denúncia define o campo `status` com um valor diferente de `"recebida"`, `"em_analise"` ou `"encaminhada"`, THEN THE Sistema SHALL rejeitar a operação e retornar HTTP 422.
3. WHEN uma denúncia é criada sem o campo `status`, THE Sistema SHALL registrá-la com `status = "recebida"`.
4. WHEN uma denúncia é criada com sucesso, THE Sistema SHALL retornar o `id` e o `criado_em` gerado no DB na resposta HTTP 201.
5. WHEN uma requisição de listagem de denúncias é recebida, THE Sistema SHALL retornar todas as denúncias ordenadas pelo campo `criado_em` em ordem decrescente.

---

### Requisito 5: Modelo de Quiz

**User Story:** Como usuária da plataforma, quero responder a um quiz com perguntas sobre minha situação, para que eu possa avaliar meu nível de risco de forma guiada.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar perguntas de quiz na tabela `quiz_perguntas` com os campos: `id` (inteiro, chave primária), `pergunta` (texto longo, obrigatório), `opcoes` (texto longo, obrigatório, armazena JSON serializado com opções e pesos) e `peso` (inteiro, padrão `1`).
2. WHEN todas as perguntas do quiz são solicitadas, THE Sistema SHALL retornar todas as entradas da tabela `quiz_perguntas` ordenadas por `id`.
3. WHEN uma lista de respostas é submetida ao quiz, THE Sistema SHALL calcular a pontuação somando os valores numéricos das opções selecionadas multiplicados pelo peso de cada pergunta e retornar a pontuação total e uma mensagem de resultado.

---

### Requisito 6: Modelo de Recursos

**User Story:** Como usuária da plataforma, quero consultar uma lista de recursos de apoio (linhas de ajuda, serviços jurídicos, psicológicos), para que eu saiba onde buscar suporte especializado.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar recursos com os campos: `id` (inteiro, chave primária, auto-incremento), `titulo` (até 255 caracteres, obrigatório), `descricao` (até 2.000 caracteres, opcional), `link` (até 500 caracteres, opcional) e `categoria` (até 100 caracteres, opcional).
2. WHEN uma requisição de listagem de recursos é recebida com o parâmetro `categoria`, THE Sistema SHALL retornar apenas os recursos cujo campo `categoria` corresponda ao valor informado de forma case-insensitive.
3. WHEN uma requisição de listagem de recursos é recebida sem o parâmetro `categoria`, THE Sistema SHALL retornar todos os recursos cadastrados ou uma lista vazia caso não existam registros.
4. IF o banco de dados estiver indisponível durante uma requisição de listagem de recursos, THEN THE Sistema SHALL retornar HTTP 503 com mensagem de erro descritiva.

---

### Requisito 7: Modelo de FAQ

**User Story:** Como usuária da plataforma, quero visualizar perguntas e respostas frequentes sobre direitos e procedimentos, para que eu possa me informar de forma rápida e acessível.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar itens de FAQ na tabela `faq_itens` com os campos: `id` (inteiro, chave primária), `pergunta` (texto curto, obrigatório), `resposta` (texto longo, obrigatório) e `ordem` (inteiro, padrão `0`).
2. WHEN uma requisição de listagem de FAQ é recebida, THE Sistema SHALL retornar os itens da tabela `faq_itens` ordenados pelo campo `ordem` em ordem crescente.

---

### Requisito 8: Modelo de Linha do Tempo

**User Story:** Como usuária da plataforma, quero visualizar marcos históricos da legislação brasileira sobre violência de gênero, para que eu compreenda a evolução dos meus direitos ao longo do tempo.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar eventos na tabela `linha_do_tempo` com os campos: `id` (inteiro, chave primária), `titulo` (texto curto, obrigatório), `descricao` (texto longo, opcional) e `data_evento` (data/hora, obrigatório).
2. WHEN uma requisição de listagem da linha do tempo é recebida, THE Sistema SHALL retornar os eventos ordenados pelo campo `data_evento` em ordem crescente.

---

### Requisito 9: Modelo de Delegacias

**User Story:** Como usuária da plataforma, quero localizar delegacias especializadas próximas a mim, para que eu possa registrar um boletim de ocorrência com segurança.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar delegacias na tabela `delegacias` com os campos: `id` (inteiro, chave primária), `nome` (texto curto, obrigatório), `endereco` (texto curto, obrigatório), `telefone` (texto curto, opcional), `latitude` (número de ponto flutuante, opcional), `longitude` (número de ponto flutuante, opcional) e `especializada` (booleano, padrão `false`).
2. WHEN uma requisição de listagem de delegacias é recebida com o parâmetro `especializada=true`, THE Sistema SHALL retornar apenas as delegacias com `especializada = true`.
3. WHEN os campos `latitude` e `longitude` estão presentes em uma delegacia, THE Sistema SHALL armazená-los com precisão de pelo menos 4 casas decimais.

---

### Requisito 10: Modelo de Alertas Comunitários

**User Story:** Como usuária da plataforma, quero criar e visualizar alertas sobre situações de risco em locais específicos, para que outras usuárias na mesma região sejam avisadas.

#### Critérios de Aceitação

1. THE Sistema SHALL armazenar alertas comunitários na tabela `alertas_comunitarios` com os campos: `id` (inteiro, chave primária), `titulo` (texto curto, obrigatório), `descricao` (texto longo, obrigatório), `localizacao` (texto curto, opcional), `latitude` (número de ponto flutuante, opcional), `longitude` (número de ponto flutuante, opcional) e `criado_em` (data/hora com fuso horário, gerado automaticamente pelo DB).
2. WHEN uma requisição de criação de alerta comunitário é recebida, THE Sistema SHALL persistir o alerta no DB e retorná-lo com o `id` e `criado_em` gerados.
3. WHEN uma requisição de listagem de alertas comunitários é recebida, THE Sistema SHALL retornar todos os alertas ordenados pelo campo `criado_em` em ordem decrescente.

---

### Requisito 11: Processo de Seed de Dados Iniciais

**User Story:** Como desenvolvedor, quero popular o banco de dados com dados iniciais de forma idempotente, para que o ambiente de desenvolvimento e produção tenha dados funcionais sem duplicação.

#### Critérios de Aceitação

1. THE Sistema SHALL disponibilizar um script `seed.py` que insira dados iniciais nas tabelas `faq_itens`, `recursos`, `quiz_perguntas`, `linha_do_tempo` e `delegacias`.
2. WHEN o script `seed.py` é executado e uma tabela já contém ao menos um registro, THE Sistema SHALL ignorar completamente a inserção nessa tabela e exibir no console a mensagem `"[SKIP] <tabela>: já possui dados, seed ignorado."`.
3. WHEN o script `seed.py` é executado e uma tabela está vazia, THE Sistema SHALL inserir todos os registros definidos para essa tabela e exibir no console a mensagem `"[OK] <tabela>: <N> registros inseridos."`.
4. WHEN o script `seed.py` é executado N vezes seguidas (N ≥ 2) em um DB já populado, THE Sistema SHALL deixar o número total de registros de cada tabela idêntico ao resultado da primeira execução bem-sucedida.
5. WHEN o script `seed.py` é iniciado, THE Sistema SHALL invocar `create_all` no DB antes de qualquer inserção, garantindo que todas as tabelas existam mesmo em um DB recém-criado.
6. IF a conexão com o DB falhar durante a execução do `seed.py`, THEN THE Sistema SHALL exibir a mensagem de erro no console e encerrar o processo com código de saída 1.
7. WHEN o script `seed.py` conclui todas as tabelas com sucesso, THE Sistema SHALL encerrar o processo com código de saída 0.
8. IF a inserção em uma tabela falhar por erro inesperado, THEN THE Sistema SHALL realizar rollback da transação apenas para essa tabela, exibir a mensagem de erro no console e prosseguir com as demais tabelas.

---

### Requisito 12: Integridade e Consistência dos Dados

**User Story:** Como desenvolvedor, quero que o banco de dados aplique restrições de integridade nos campos obrigatórios, para que dados inválidos nunca sejam persistidos.

#### Critérios de Aceitação

1. IF uma requisição de criação omite um campo marcado como `nullable=False` no Modelo, THEN THE Sistema SHALL rejeitar a operação e retornar um erro com código HTTP 422.
2. THE Sistema SHALL garantir que todos os campos `id` de todos os Modelos sejam chaves primárias com incremento automático.
3. WHEN uma operação de escrita é executada no DB, THE Sistema SHALL encerrar a Sessão corretamente após a operação, independentemente de sucesso ou falha, prevenindo vazamento de conexões.
4. THE Sistema SHALL indexar o campo `id` de todos os Modelos para garantir eficiência nas buscas por chave primária.
