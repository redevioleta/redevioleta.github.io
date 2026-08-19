"""Popula o banco com dados iniciais para todos os módulos."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, Base, engine
from app.models.models import (
    FaqItem, Recurso, Quiz, EventoLinhaDoTempo, Delegacia
)
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── FAQ ─────────────────────────────────────────────────────────────────────
faq_items = [
    (1,  "O que diferencia assédio de violência?",
          "Assédio é um comportamento repetido e indesejado de natureza sexual, moral ou psicológica. Violência pode ser um único ato físico, sexual, psicológico, patrimonial ou moral. Ambos são crimes — a diferença está na forma e frequência, mas os dois merecem denúncia."),
    (2,  "Posso denunciar de forma anônima?",
          "Sim. O Disque 100 e o Disque 180 aceitam denúncias anônimas. A identidade não é necessária para que a denúncia seja investigada."),
    (3,  "Preciso de advogado para denunciar?",
          "Não para o Boletim de Ocorrência. Você pode registrar sozinha/o na delegacia ou online. Para processos judiciais é recomendado, mas a Defensoria Pública oferece assistência jurídica gratuita para quem não tem condições de contratar advogado particular."),
    (4,  "A Lei Maria da Penha protege apenas mulheres cisgênero?",
          "Não. O STJ e o STF entendem que a Lei Maria da Penha protege mulheres trans e travestis, pois o critério é gênero feminino, não biológico. Homens cisgêneros podem recorrer ao Código Penal e à Lei nº 13.772/2018 em casos de violência doméstica."),
    (5,  "O que acontece depois que eu denuncio?",
          "1. A delegacia abre um Inquérito Policial. 2. O Ministério Público recebe o inquérito e pode oferecer denúncia criminal. 3. Você pode solicitar Medidas Protetivas de Urgência. 4. O juiz decide sobre as medidas em até 48h. 5. O processo segue para julgamento."),
    (6,  "Posso retirar uma denúncia depois?",
          "Em crimes de ação penal pública (como os previstos na Lei Maria da Penha), a denúncia não pode ser retirada pela vítima após o processo iniciado — cabe ao Estado prosseguir. Isso protege a vítima de pressões do agressor."),
    (7,  "Como provar assédio no trabalho?",
          "Guarde prints de mensagens, e-mails, registros de chamadas. Anote datas, horários e o que foi dito. Identifique testemunhas. Registre ocorrência no RH com protocolo. Em seguida, procure a Delegacia do Trabalho (MTE) ou ajuíze ação na Justiça do Trabalho."),
    (8,  "O que é uma Medida Protetiva de Urgência?",
          "É uma determinação judicial que pode: proibir o agressor de se aproximar da vítima; proibi-lo de contato por qualquer meio; retirá-lo do lar; suspender porte de arma. É solicitada ao registrar o B.O. e decidida pelo juiz em até 48 horas."),
    (9,  "Assédio virtual / online é crime?",
          "Sim. A Lei nº 13.772/2018 criminaliza o registro não autorizado de conteúdo íntimo. A Lei nº 13.718/2018 criou o crime de importunação sexual online. Compartilhamento de fotos íntimas sem consentimento (revenge porn) é crime com pena de 1 a 5 anos."),
    (10, "O que é stalking e é crime no Brasil?",
          "Stalking é a perseguição obsessiva e repetida por qualquer meio — redes sociais, mensagens, aparição nos mesmos locais. A Lei nº 14.132/2021 tornou o stalking crime com pena de 1 a 2 anos de prisão, aumentada em até metade se praticado contra mulher."),
    (11, "Quais são os tipos de violência doméstica?",
          "A Lei Maria da Penha reconhece cinco tipos: 1) Física — agressões corporais; 2) Psicológica — ameaças, humilhações, isolamento; 3) Sexual — atos sem consentimento; 4) Patrimonial — destruição de bens ou documentos; 5) Moral — calúnia, difamação, injúria."),
]
if not db.query(FaqItem).first():
    for ordem, pergunta, resposta in faq_items:
        db.add(FaqItem(pergunta=pergunta, resposta=resposta, ordem=ordem))
    print(f"  FAQ: {len(faq_items)} itens inseridos")
else:
    print("  FAQ: já possui dados, ignorado")

# ── RECURSOS ─────────────────────────────────────────────────────────────────
recursos = [
    ("Ligue 180 — Central da Mulher",      "Atendimento gratuito 24h. Orientação, denúncia e encaminhamento para a rede de proteção.",                          "https://www.gov.br/mdh/pt-br/navegue-por-temas/politicas-para-mulheres/ligue-180",      "emergência"),
    ("Disque 100 — Direitos Humanos",      "Canal de denúncia de violações de direitos humanos, inclusive crianças e adolescentes.",                             "https://www.gov.br/mdh/pt-br/disque100",                                               "emergência"),
    ("CVV — Centro de Valorização da Vida","Apoio emocional e prevenção ao suicídio. Ligue 188 (gratuito, 24h) ou acesse o chat online.",                       "https://www.cvv.org.br",                                                               "psicológico"),
    ("SaferNet Brasil",                    "Denúncia e apoio para crimes e violências na internet. Registro de cyberbullying, revenge porn e stalking digital.", "https://www.safernet.org.br",                                                          "digital"),
    ("Defensoria Pública",                 "Assistência jurídica gratuita para quem não pode pagar advogado. Presente em todos os estados.",                    "https://www.anadep.org.br",                                                            "jurídico"),
    ("CAPS — Centro de Atenção Psicossocial","Serviço público gratuito de saúde mental pelo SUS. Presente em municípios de todo o Brasil.",                      None,                                                                                   "psicológico"),
    ("CRAS / CREAS",                       "Centro de Referência em Assistência Social. Atendimento social e psicológico gratuito.",                             None,                                                                                   "social"),
    ("Portal da Mulher — Gov.br",          "Informações oficiais sobre direitos, serviços e políticas públicas para mulheres.",                                  "https://www.gov.br/mulheres",                                                          "jurídico"),
    ("Delegacia Eletrônica SP",            "Registro de Boletim de Ocorrência online para crimes como ameaça, injúria e importunação.",                          "https://www.delegaciaeletronica.policiacivil.sp.gov.br",                               "digital"),
    ("Jusbrasil",                          "Consulta gratuita de processos, jurisprudência e orientações jurídicas.",                                            "https://www.jusbrasil.com.br",                                                         "jurídico"),
    ("UBS — Unidade Básica de Saúde",      "Solicite encaminhamento para psicólogo pelo SUS na UBS mais próxima de você.",                                      None,                                                                                   "saúde"),
    ("Instituto Patrícia Galvão",          "Pesquisas, notícias e campanhas sobre violência contra a mulher no Brasil.",                                         "https://agenciapatriciagalvao.org.br",                                                 "educação"),
]
if not db.query(Recurso).first():
    for titulo, descricao, link, categoria in recursos:
        db.add(Recurso(titulo=titulo, descricao=descricao, link=link, categoria=categoria))
    print(f"  Recursos: {len(recursos)} itens inseridos")
else:
    print("  Recursos: já possui dados, ignorado")

# ── QUIZ ─────────────────────────────────────────────────────────────────────
quiz_perguntas = [
    ("Alguém faz comentários, piadas ou gestos de conteúdo sexual ou íntimo sem sua permissão?",
     '["Sim, frequentemente|2", "Às vezes|1", "Não|0"]', 2),
    ("Você sente medo ou ansiedade quando vai ao trabalho, escola ou se relaciona com alguém específico?",
     '["Sim, sempre|2", "Às vezes|1", "Não|0"]', 2),
    ("Alguém te pressiona, chantageia ou ameaça para obter algum favor, presença ou contato?",
     '["Sim|2", "Já aconteceu uma vez|1", "Não|0"]', 2),
    ("Você recebe mensagens, ligações ou contatos insistentes mesmo depois de pedir que parem?",
     '["Sim, frequentemente|2", "Às vezes|1", "Não|0"]', 2),
    ("Alguém te humilha, grita, te diminui ou critica na frente de outras pessoas?",
     '["Sim, com frequência|2", "Raramente|1", "Não|0"]', 2),
    ("Você evita certos lugares, situações ou pessoas por se sentir insegura/o?",
     '["Sim, muito|2", "Um pouco|1", "Não|0"]', 1),
    ("Alguém controla o que você faz, com quem fala, onde vai ou como se veste?",
     '["Sim|2", "Às vezes tenta|1", "Não|0"]', 2),
    ("Você se culpa por situações em que foi tratada/o de forma desrespeitosa?",
     '["Sim, me culpo muito|2", "Às vezes|1", "Não|0"]', 1),
]
if not db.query(Quiz).first():
    for pergunta, opcoes, peso in quiz_perguntas:
        db.add(Quiz(pergunta=pergunta, opcoes=opcoes, peso=peso))
    print(f"  Quiz: {len(quiz_perguntas)} perguntas inseridas")
else:
    print("  Quiz: já possui dados, ignorado")

# ── LINHA DO TEMPO ───────────────────────────────────────────────────────────
eventos = [
    ("1988 — Constituição Federal",
     "A Constituição de 1988 estabelece igualdade de direitos entre homens e mulheres (Art. 5º, I) e proíbe discriminação por sexo.",
     datetime(1988, 10, 5)),
    ("1994 — Convenção de Belém do Pará",
     "O Brasil ratifica a Convenção Interamericana para Prevenir, Punir e Erradicar a Violência contra a Mulher.",
     datetime(1994, 6, 9)),
    ("2001 — Condenação pela OEA",
     "A Comissão Interamericana de Direitos Humanos condena o Brasil por omissão no caso Maria da Penha Maia Fernandes, impulsionando mudanças legislativas.",
     datetime(2001, 4, 16)),
    ("2006 — Lei Maria da Penha (nº 11.340)",
     "Considerada uma das melhores leis do mundo pela ONU, cria mecanismos para combater a violência doméstica e familiar contra a mulher. Sancionada em 7 de agosto.",
     datetime(2006, 8, 7)),
    ("2012 — Lei do Feminicídio aprovada em comissão",
     "A CPI da violência contra a mulher lança relatório que culminará na tipificação do feminicídio.",
     datetime(2012, 7, 4)),
    ("2015 — Lei do Feminicídio (nº 13.104)",
     "Inclui o feminicídio no Código Penal como homicídio qualificado quando praticado contra mulher por razões de gênero.",
     datetime(2015, 3, 9)),
    ("2018 — Lei de Importunação Sexual (nº 13.718)",
     "Criminaliza a importunação sexual e a divulgação de cena de estupro. Revenge porn passa a ter pena de 1 a 5 anos.",
     datetime(2018, 9, 24)),
    ("2018 — Proteção de registros íntimos (nº 13.772)",
     "Criminaliza o registro não autorizado de conteúdo íntimo e reconhece a violação da intimidade como forma de violência doméstica.",
     datetime(2018, 12, 19)),
    ("2021 — Lei do Stalking (nº 14.132)",
     "Torna a perseguição obsessiva (stalking) crime autônomo com pena de 1 a 2 anos, ampliada se cometida contra mulher.",
     datetime(2021, 3, 31)),
    ("2022 — Agosto Lilás institucionalizado",
     "O mês de agosto passa a ser reconhecido oficialmente como o mês de conscientização sobre a violência doméstica (Agosto Lilás), reforçando o aniversário da Lei Maria da Penha.",
     datetime(2022, 8, 1)),
    ("2023 — Lei 14.550 — Violência Digital",
     "Amplia a Lei Maria da Penha para incluir expressamente a violência doméstica praticada por meios digitais e eletrônicos.",
     datetime(2023, 4, 19)),
]
if not db.query(EventoLinhaDoTempo).first():
    for titulo, descricao, data in eventos:
        db.add(EventoLinhaDoTempo(titulo=titulo, descricao=descricao, data_evento=data))
    print(f"  Linha do tempo: {len(eventos)} eventos inseridos")
else:
    print("  Linha do tempo: já possui dados, ignorado")

# ── DELEGACIAS ───────────────────────────────────────────────────────────────
delegacias = [
    ("DEAM – São Paulo Centro",    "Av. Paulista, 900 – Bela Vista, SP",              "(11) 3392-9100", -23.5505, -46.6333),
    ("DEAM – Santo André",         "R. Senador Fláquer, 452, Santo André, SP",        "(11) 4438-1200", -23.6273, -46.6566),
    ("DEAM – Rio de Janeiro",      "R. Dom Manuel, 15 – Centro, RJ",                  "(21) 2332-2408", -22.9068, -43.1729),
    ("DEAM – Niterói",             "R. Visconde de Sepetiba, 990, Niterói, RJ",       "(21) 2620-0748", -22.8683, -43.2785),
    ("DEAM – Belo Horizonte",      "R. Guajajaras, 40 – Centro, BH, MG",             "(31) 3261-3197", -19.9191, -43.9386),
    ("DEAM – Brasília",            "SCS Qd. 6 – Asa Sul, DF",                         "(61) 3362-4563", -15.7801, -47.9292),
    ("DEAM – Salvador",            "Av. Oscar Pontes, 1247, Salvador, BA",            "(71) 3116-0800", -12.9714, -38.5014),
    ("DEAM – Fortaleza",           "R. 24 de Maio, 860 – Centro, Fortaleza, CE",      "(85) 3101-7300",  -3.7172, -38.5433),
    ("DEAM – Recife",              "R. do Imperador, 209 – Boa Vista, Recife, PE",    "(81) 3184-3500",  -8.0476, -34.8770),
    ("DEAM – Porto Alegre",        "R. dos Andradas, 1355 – Centro, Porto Alegre, RS","(51) 3289-2930", -30.0346, -51.2177),
    ("DEAM – Curitiba",            "R. Mar. Floriano Peixoto, 141, Curitiba, PR",     "(41) 3233-9060", -25.4284, -49.2733),
    ("DEAM – São Luís",            "Pça. João Lisboa, 10 – Centro, São Luís, MA",     "(98) 3212-2160",  -2.5307, -44.3068),
    ("DEAM – Manaus",              "R. Recife, 3782 – Adrianópolis, Manaus, AM",      "(92) 3214-4390",  -3.1190, -60.0217),
    ("DEAM – Goiânia",             "R. 82, 343 – Setor Sul, Goiânia, GO",             "(62) 3201-2033", -16.6869, -49.2648),
    ("DEAM – Belém",               "Tv. Campos Sales, 119 – Campina, Belém, PA",      "(91) 3215-3040",  -1.4558, -48.4902),
    ("DEAM – Natal",               "R. Trairi, 490 – Petrópolis, Natal, RN",          "(84) 3232-4518",  -5.7945, -35.2110),
    ("DEAM – Maceió",              "Av. Gustavo Paiva, 5921 – Cruz das Almas, AL",    "(82) 3315-4041",  -9.6658, -35.7350),
    ("DEAM – Teresina",            "R. 24 de Janeiro, 165 – Centro, Teresina, PI",    "(86) 3215-5400",  -5.0892, -42.8019),
    ("DEAM – Mossoró",             "R. Felipe Camarão, 1177, Mossoró, RN",            "(84) 3315-2200",  -5.1878, -37.3442),
    ("DEAM – Santa Maria",         "R. Floriano Peixoto, 1670, Santa Maria, RS",      "(55) 3220-1940", -29.6868, -53.8023),
    ("DEAM – Florianópolis",       "R. Esteves Júnior, 68 – Centro, Florianópolis, SC","(48) 3665-4500", -27.5954, -48.5480),
    ("DEAM – Santos",              "R. General Câmara, 23 – Centro, Santos, SP",      "(13) 3232-6060", -23.9035, -46.1800),
    ("DEAM – Campo Grande",        "R. Antônio Maria Coelho, 4155, Campo Grande, MS", "(67) 3311-2020", -20.4697, -54.6201),
    ("DEAM – Cuiabá",              "Av. Historiador Rubens de Mendonça, 4265, MT",    "(65) 3613-1890", -15.5961, -56.0966),
    ("DEAM – Porto Velho",         "Av. Farquar, 2986 – Pedrinhas, Porto Velho, RO",  "(69) 3216-5000",  -8.7612, -63.9039),
]
if not db.query(Delegacia).first():
    for nome, endereco, telefone, lat, lng in delegacias:
        db.add(Delegacia(nome=nome, endereco=endereco, telefone=telefone,
                         latitude=lat, longitude=lng, especializada=True))
    print(f"  Delegacias: {len(delegacias)} DEAMs inseridas")
else:
    print("  Delegacias: já possui dados, ignorado")

db.commit()
db.close()
print("\nSeed concluído com sucesso!")
