import os
import re
import json
import random
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ==============================
# CARREGAMENTO DE VARIÁVEIS
# ==============================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))

# Arquivo de warnings
ARQUIVO_WARN = "warnings.json"


# ==============================
# 📋 DADOS DOS PERCURSOS (fonte única de verdade)
# ==============================
PERCURSOS = {
    "1º Percurso — Balamentos": {
        "Praças": {"tempo": "45 segundos", "nota": "—"},
        "Graduados": {"tempo": "40 segundos", "nota": "—"},
    },
    "2º Percurso — Torre": {
        "Recruta": {"tempo": "25 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "20 segundos", "nota": "5,5 pontos"},
        "Terceiro-Sargento": {"tempo": "16 segundos", "nota": "6,0 pontos"},
        "Segundo-Sargento": {"tempo": "14 segundos", "nota": "6,5 pontos"},
        "Primeiro-Sargento": {"tempo": "12 segundos", "nota": "6,5 pontos"},
    },
    "3º Percurso — Torre 2.0": {
        "Recruta": {"tempo": "30 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "25 segundos", "nota": "5,5 pontos"},
        "Terceiro-Sargento": {"tempo": "18 segundos", "nota": "6,0 pontos"},
        "Segundo-Sargento": {"tempo": "16 segundos", "nota": "6,5 pontos"},
        "Primeiro-Sargento": {"tempo": "14 segundos", "nota": "6,5 pontos"},
    },
    "4º Percurso": {
        "Recruta": {"tempo": "35 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "30 segundos", "nota": "5,5 pontos"},
    },
    "Percurso de Graduados": {
        "Graduados": {"tempo": "45 segundos", "nota": "—"},
    },
}

# Tabela de notas de aprovação (geral, independente do percurso)
NOTAS_APROVACAO = {
    "Recruta": "5,0 pontos",
    "Soldado": "5,5 pontos",
    "Terceiro-Sargento": "6,0 pontos",
    "Segundo-Sargento": "6,5 pontos",
    "Primeiro-Sargento": "6,5 pontos",
}


# ==============================
# 📅 DADOS DA CAPACITAÇÃO DE PATENTE (fonte única de verdade)
# ==============================
CAPACITACAO = {
    "Graduados 「🎓」": [
        {"cargo": "Subtenente", "dias": "6 dias", "detalhe": "22 relatórios de recrutamentos registrados"},
        {"cargo": "Primeiro-Sargento", "dias": "5 dias", "detalhe": "18 relatórios de recrutamentos registrados"},
        {"cargo": "Segundo-Sargento", "dias": "4 dias", "detalhe": "15 relatórios de recrutamentos registrados"},
        {"cargo": "Terceiro-Sargento", "dias": "3 dias", "detalhe": "8 relatórios de recrutamentos registrados"},
    ],
    "Praças 「🇧🇷」": [
        {"cargo": "Cabo", "dias": "2 dias", "detalhe": "5 relatórios de recrutamentos registrados + ESA"},
        {"cargo": "Soldado", "dias": "1 dia", "detalhe": ""},
        {"cargo": "Recruta", "dias": "N/A", "detalhe": ""},
    ],
}


def formatar_linha_cp(item):
    """Monta a linha de um cargo da capacitação (ex: 'Cabo = 2 dias (5 relatórios...)')."""
    texto = f"▪️ **{item['cargo']}** = {item['dias']}"
    if item["detalhe"]:
        texto += f" ({item['detalhe']})"
    return texto


# ==============================
# 📌 DADOS DOS REQUISITOS DOS ÓRGÃOS (fonte única de verdade)
# ==============================
REQUISITOS = {
    "BFEr": {
        "patente": "Rubro 1",
        "requisitos": [
            "Ser ótimo em PVP (combate)",
            "Responsabilidade",
            "Gramática",
            "Disponibilidade",
            "Ter liderança e estratégia nas raids",
        ],
        "extras": {
            "⚠️ Observação": [
                "Necessário ter comprovação de terrorismo (vídeo raidando) para avaliar se o candidato está apto para adentrar ao BFEr.",
            ],
        },
    },
    "CIR": {
        "patente": "Rubro 1",
        "requisitos": [
            "Ter no mínimo 1 semana (7 dias) de carreira na OR e ter relevância na organização",
            "Possuir pelo menos 01 (um) exílio permanente no EB",
            "Manter boa postura e comportamento",
            "Saber lidar com situações de pressão psicológica",
            "Respeitar superiores, regras e a hierarquia",
            "Demonstrar disciplina e responsabilidade",
        ],
        "extras": {
            "📝 Conduta durante o formulário": [
                "Todas as respostas deverão ser feitas com suas próprias palavras",
                "Plágio e uso de IA serão facilmente detectados",
                "O uso de IA ou cópia de respostas poderá resultar em Black List",
                "Mantenha postura e respeito durante todo o processo",
                "O descumprimento das regras poderá resultar na anulação do formulário",
            ],
        },
    },
    "ACR": {
        "patente": "Candidato a Rubro ou superior",
        "requisitos": [
            "Ser útil, visando ampliar a atuação da ACR",
            "Manter organização, postura e conduta adequada",
            "Demonstrar disponibilidade no dia a dia",
            "Conta do Discord com, no mínimo, três meses completos de criação (caso esse requisito esteja faltando, a candidatura será retirada na hora)",
        ],
        "extras": {
            "⚠️ Observações": [
                "Faça o formulário com atenção e deixe todas as respostas claras",
                "Fale o que sabe sobre os Órgãos do EB do Apex em suas perguntas correspondentes",
                "Caso não tenha disponibilidade, nem faça o formulário",
                "Em nenhum momento é permitido falar sobre o formulário ou vazá-lo: quem fizer isso entrará na Black List da ACR e será expulso da Ordem Rubra",
            ],
        },
    },
}


def formatar_lista_req(itens):
    """Transforma uma lista de itens em linhas com marcador."""
    return "\n".join(f"▪️ {item}" for item in itens)


# ==============================
# ☀️ LEMA DA ORDEM RUBRA
# ==============================
LEMA_TEXTO = (
    "A cada alvorada, eis que o Sol se ergue, majestoso e tingido de carmesim, "
    "proclamando a sentença inexorável contra os corruptos e os agressores. "
    "Pois de sua luz emana o juízo, e sob seu fulgor, nenhuma injustiça permanecerá impune."
)
LEMA_GRITO = "VIDA LONGA ORDEM RUBRA!"


# ==============================
# 🪖 DADOS DA ORDEM UNIDA (FONTE ÚNICA DE VERDADE)
# ==============================
ORDEM_UNIDA = {
    "Introdução": {
        "titulo": "Manual de Ordem Unida",
        "texto": """O objetivo deste documento é instruir, orientar e padronizar a execução da ordem unida, assegurando disciplina, coesão, postura militar e correta aplicação dos movimentos e comandos conforme as normas estabelecidas pela instituição.""",
    },
    "Parte 1 — Objetivo da Ordem Unida": {
        "titulo": "Parte 1 — Objetivo da Ordem Unida",
        "texto": """**FUNDAMENTOS, COMANDOS E APLICAÇÕES**
A Ordem Unida é um dos fundamentos essenciais da formação militar, tendo como finalidade padronizar a apresentação, o deslocamento e a organização dos militares em conjunto. Por meio de seus comandos e movimentos, busca-se desenvolver disciplina, obediência imediata, coordenação coletiva, atenção, postura e reflexos condicionados, atributos indispensáveis para qualquer militar. 
A correta execução da Ordem Unida garante que o grupamento se apresente e se desloque de maneira organizada, harmônica e eficiente, respeitando a hierarquia e a padronização institucional.

O QUE É ORDEM UNIDA - RESUMIDA
A Ordem Unida é o conjunto de normas, comandos e movimentos utilizados para:
Padronizar a apresentação do militar e do grupamento;
Organizar o deslocamento coletivo;
Garantir disciplina, hierarquia e harmonia nos movimentos.

Seu emprego desenvolve:
Obediência imediata às ordens;
Coordenação coletiva;
Atenção, postura e autocontrole;
Espírito de corpo e disciplina militar.

É aplicada em instruções, apresentações, deslocamentos formais e situações administrativas dentro da instituição.

Principal Objetivo da Ordem Unida
A Ordem Unida tem como principais objetivos permitir que o grupamento se apresente e se desloque em perfeita ordem, desenvolver a disciplina coletiva, estimular a obediência aos comandos, aprimorar a coordenação e fortalecer o espírito de corpo. Esses fatores são determinantes para o bom desempenho do militar em qualquer atividade dentro da instituição.

OBJETIVOS DA ORDEM UNIDA - RESUMIDA
Permitir que o grupamento:
Apresente-se de forma organizada e padronizada;
Desloque-se com ordem, sincronia e disciplina.

Desenvolver no militar:
Reflexos condicionados;
Respeito à hierarquia;
Capacidade de agir coletivamente;
Prontidão para cumprir ordens.""",
    },
    "Parte 2 — Tipos de Comandos": {
        "titulo": "Parte 2 — Tipos de Comandos",
        "texto": """Os comandos utilizados na Ordem Unida dividem-se em vozes de comando e comandos propriamente ditos.
A voz de comando é utilizada para preparar o grupamento, alertando-o de que uma ação será executada. Dentro dela, destaca-se a voz de advertência, que serve exclusivamente como alerta inicial, não possuindo caráter de execução. Exemplos incluem “Grupamento”, “Pelotão” e “Esquadrão”. Essa voz deve ser empregada apenas uma vez, pois sua função é somente chamar a atenção do grupamento.
O meio comando é aquele que antecede uma ação, preparando o grupamento para o movimento que será executado. Ele é aplicável, principalmente, a comandos de marcha e de volver, pois nesses casos há movimentação. Nos comandos de volver, o meio comando indica a direção do giro; nos comandos de marcha, indica o tipo e, quando necessário, a direção do deslocamento.
Os comandos propriamente ditos são responsáveis por iniciar ou finalizar um movimento. Alguns são antecedidos por meio comando, enquanto outros são executados de forma direta. Exemplos incluem “Sentido”, “Descansar”, “Atenção” e “Marche”.

TIPOS DE COMANDOS - RESUMIDO
Vozes de Comando
Utilizadas para:
Alertar;
Preparar o grupamento para uma ação.

Não possuem execução direta de movimento.
Voz de Advertência
Finalidade:
Alertar o grupamento de que comandos serão emitidos.

Características:
Deve ser dita apenas uma vez;
Não inicia movimento.

Exemplos:
“GRUPAMENTO!”
“PELOTÃO!”
“ESQUADRÃO!”

Meio Comando
Finalidade:
Preparar o grupamento para a ação que será executada.

Aplicação:
Apenas em comandos que envolvem movimentação.

Função:
Em marchas: indica o tipo e a direção;
Em volvers: indica a direção do giro.

Exemplos:
APRESENTAR, ARMA!
DESCANSAR, ARMA!
ESQUERDA VOLVER!
DIREITA VOLVER!

Comandos Propriamente Ditos
Finalidade:
Iniciar ou encerrar a execução do movimento.
Podem ser:
Antecedidos por meio comando;
Executados de forma direta.

Exemplos:
SENTIDO!
DESCANSAR!
ATENÇÃO!
MARCHE!""",
    },
    "Parte 3 — Comandos de Postura": {
        "titulo": "Parte 3 — Comandos de Postura",
        "texto": """COMANDOS BÁSICOS DE POSTURA
O comando “Atenção” tem a finalidade de alertar o grupamento para o início das ordens do instrutor ou xerife. O comando “Sentido” determina que o grupamento permaneça imóvel, com postura ereta e mãos vazias, aguardando o próximo comando. O comando “Descansar” autoriza o grupamento a assumir a posição de descanso, sendo válido apenas quando o grupamento estiver anteriormente em posição de sentido. O comando “À vontade” concede maior liberdade de movimento, desde que o militar permaneça no local e mantenha postura adequada.
Os comandos “Apresentar, arma” e “Descansar, arma” são utilizados, respectivamente, para iniciar e finalizar a continência do grupamento, incluindo o instrutor ou xerife.

COMANDOS BÁSICOS DE POSTURA - RESUMIDO
ATENÇÃO!
Finalidade:
Alertar o grupamento para o início das ordens do instrutor.

Observação:
Prepara para o comando seguinte.

SENTIDO!
Finalidade:
Colocar o grupamento em postura rígida e imóvel.

Características:
Mãos vazias;
Olhar à frente.

DESCANSAR!
Finalidade:
Permitir postura menos rígida.

Observação:
Só pode ser dado se o grupamento estiver em sentido.

À VONTADE!
Finalidade:
Conceder maior liberdade de movimento.

Limitações:
Não sair do lugar;
Manter postura adequada.""",
    },
    "Parte 4 — Comandos de Marcha": {
        "titulo": "Parte 4 — Comandos de Marcha",
        "texto": """Existem três tipos principais de marcha aplicáveis no âmbito do jogo: ordinário, acelerado e sem cadência.
A marcha ordinária é a mais formal e a mais utilizada. Nela, o grupamento deve seguir o instrutor ou xerife sem correr, mantendo rigorosamente a organização da fila e a sincronia coletiva. 
A marcha acelerada caracteriza-se pelo deslocamento correndo, devendo o grupamento, ainda assim, tentar manter a organização da fila. 
A marcha sem cadência é considerada informal, permitindo que o grupamento siga o instrutor sem necessidade de manter alinhamento rigoroso, sendo proibido correr.
Para preparar corretamente o grupamento para marchar, os comandos devem seguir uma sequência padronizada. Para a marcha ordinária, o instrutor deve comandar, de frente para o grupamento: “Grupamento, atenção” e “Grupamento, sentido”. Em seguida, deve virar-se de costas para o grupamento e informar o destino com “Em direção ao (local)”, indicar o tipo de marcha com “Ordinário” e iniciar o deslocamento com “Marche”. Ao término da marcha, já de frente para o grupamento, deve finalizar com “Grupamento, faz alto”.
O mesmo procedimento é aplicado à marcha acelerada, substituindo-se apenas o tipo de marcha pelo comando “Acelerado”, e à marcha sem cadência, utilizando-se o comando “Sem cadência”. Em todos os casos, o comando “Grupamento, faz alto” é obrigatório para encerrar a marcha, devendo o grupamento permanecer em posição de sentido após a parada.

Tipos de Marcha
ORDINÁRIO
Marcha formal;
Sem correr;
Fila organizada;
Total sincronia com o instrutor.
ACELERADO
Marcha rápida;
Grupamento corre;
Organização da fila deve ser mantida.

SEM CADÊNCIA
Marcha informal;
Não exige alinhamento rígido;
É proibido correr.

SEQUÊNCIA PADRÃO PARA MARCHAR
Marcha Ordinária
De frente:
GRUPAMENTO, ATENÇÃO!
GRUPAMENTO, SENTIDO!

De costas:
EM DIREÇÃO AO (LOCAL)!
ORDINÁRIO!
MARCHE!

De frente (finalização):
GRUPAMENTO, FAZ ALTO!

Marcha Acelerada
Mesma sequência, substituindo:
ORDINÁRIO! por ACELERADO!

Marcha Sem Cadência
Mesma sequência, substituindo:
ORDINÁRIO! por SEM CADÊNCIA!""",
    },
    "Parte 5 — Alteração de Dispositivo": {
        "titulo": "Parte 5 — Alteração de Dispositivo",
        "texto": """O comando “Fora de forma” é exclusivo para alterações de dispositivo e jamais deve ser utilizado para deslocamento. Ele indica que o grupamento mudará sua organização, como de formação para coluna ou de coluna para formação.
A coluna por um é uma forma de organização na qual os militares ficam posicionados um atrás do outro, respeitando a distância de uma pessoa entre si. Existem outras variações, como coluna por dois, três ou quatro, nas quais se deve observar rigorosamente a obediência às fileiras e às linhas.
Para formar uma coluna por um, o instrutor deve permanecer de frente para o grupamento e comandar: “Grupamento, atenção”, “Grupamento, sentido” e, em seguida, explicar a ação com “Devem formar uma coluna por um em minha retaguarda”. Após isso, utiliza-se o comando “Fora de forma” e, logo depois, “Marche”. Após o comando “Marche”, o instrutor deve deslocar-se até o local desejado para que o grupamento se organize corretamente em coluna. Ao concluir a alteração de dispositivo, o grupamento assume posição de descanso, não sendo utilizado o comando “Grupamento, faz alto”, pois não se trata de uma marcha.
A formação, por sua vez, ocorre quando o grupamento se organiza em linha, ombro a ombro. Fileira é a disposição dos militares lado a lado, voltados para a mesma frente. Linha caracteriza-se por possuir maior frente do que profundidade, ou seja, mais militares lado a lado do que em profundidade.
Para entrar em formação, o instrutor deve comandar, de frente para o grupamento: “Grupamento, atenção”, “Grupamento, sentido” e, em seguida, explicar a ação com “Devem ir até a formação ao meu lado e formar um ombro a ombro ao meu comando”. Após isso, utiliza-se o comando “Fora de forma” e, posteriormente, “Marche”. Assim que o grupamento concluir a formação, deve assumir posição de descanso, sem o uso do comando “Grupamento, faz alto”.

ALTERAÇÃO DE DISPOSITIVO
FORA DE FORMA
Finalidade:
Alterar o formato do grupamento.

Proibições:
Nunca usar para deslocamento.

Exemplos de alteração:
Formação para coluna;
Coluna para formação.
COLUNA
Conceito
Coluna por um:
Militares posicionados um atrás do outro;
Distância de uma pessoa entre cada militar.

Existem:
Coluna por dois, três, quatro, etc.

Comandos para Formar Coluna
De frente:
GRUPAMENTO, ATENÇÃO!
GRUPAMENTO, SENTIDO!
DEVEM FORMAR UMA COLUNA POR UM EM MINHA RETAGUARDA!
FORA DE FORMA!
MARCHE!
Observação:
Após “MARCHE!”, o instrutor deve ir ao local desejado;
Não utilize “GRUPAMENTO, FAZ ALTO”.
FORMAÇÃO
Conceitos Fundamentais
Fileira:
Militares lado a lado, mesma linha e mesma frente.

Linha:
Formação com frente maior que a profundidade.

Comandos para Formar
De frente:
GRUPAMENTO, ATENÇÃO!
GRUPAMENTO, SENTIDO!
DEVEM IR ATÉ A FORMAÇÃO AO MEU LADO E FORMAR UM OMBRO A OMBRO AO MEU COMANDO!
FORA DE FORMA!
MARCHE!

Observação:
Após a formação, o grupamento entra em descanso;
Não usar “FAZ ALTO”.""",
    },
    "Parte 6 — Comandos de Apresentação": {
        "titulo": "Parte 6 — Comandos de Apresentação",
        "texto": """A apresentação é um ato formal que demonstra disciplina, organização e respeito à hierarquia. O militar responsável deve apresentar-se informando seu posto ou graduação seguido do nome de guerra. Para apresentar o grupamento a um superior, o grupamento deve estar previamente organizado e em posição de sentido.
O xerife ou instrutor posiciona-se à frente do grupamento, comanda “Grupamento, atenção” e “Grupamento, sentido”, vira-se para o superior, presta continência e se apresenta. Em seguida, informa se o grupamento está com ou sem faltas e com ou sem alterações. Após o superior declarar que o grupamento está apresentado, o xerife retorna-se ao grupamento, comanda “Grupamento, descansar” e reassume sua posição.
Considera-se falta a ausência de um integrante que não compareceu à instrução. Considera-se alteração quando algum integrante se retira antes do término da atividade. A inexistência de faltas e alterações indica que todos os integrantes participaram integralmente da instrução.

APRESENTAÇÃO DO GRUPAMENTO
Finalidade:
Demonstrar disciplina e organização.

Procedimento:
Grupamento em sentido;
Xerife à frente;
Continência obrigatória do xerife;
Informar:
Com ou sem faltas;
Com ou sem alterações.

Definições:
Falta: ausência no início da instrução;
Alteração: saída antes do término.

Sequência de Comandos
Preparação do Grupamento
De frente para o grupamento, o xerife comanda:
GRUPAMENTO, ATENÇÃO!
GRUPAMENTO, SENTIDO!

Apresentação ao Superior
O xerife:
Vira-se em direção ao superior;
Presta continência obrigatoriamente;
Realiza a apresentação verbal, dizendo:
(POSTO/GRADUAÇÃO DO XERIFE) (NOME DE GUERRA), XERIFE DO CURSO!
Exemplo: SUBTENENTE AT, XERIFE DO CURSO!
Em seguida, ainda em continência, informa:
APRESENTO GRUPAMENTO PRONTO, COM/SEM FALTAS E COM/SEM ALTERAÇÕES!

Em seguida o superior deverá responder algo semelhante à:
ESTÁ APRESENTADO.

Finalização da Apresentação
Após a resposta do superior, o xerife:
Cessa a continência;
Vira-se novamente para o grupamento;
Comanda:
GRUPAMENTO, DESCANSAR!

Retorno à Posição
O xerife:
Retorna ao seu local;
Assume posição de descanso junto ao grupamento.""",
    },
    "Parte 7 — Observações Gerais": {
        "titulo": "Parte 7 — Observações Gerais",
        "texto": """OBSERVAÇÕES GERAIS
Todos os comandos devem ser executados com o militar em posição de sentido, salvo quando o comando determinar outra postura.
A execução de comandos fora da posição correta caracteriza erro de procedimento.
O comando “GRUPAMENTO, FAZ ALTO” deve ser utilizado exclusivamente para finalizar as marchas.
O comando “FAZ ALTO” nunca deve ser empregado em alterações de dispositivo, como formação ou coluna.
O comando “FORA DE FORMA” é restrito à mudança do formato do grupamento, não devendo ser utilizado para deslocamento.
Durante marchas, o grupamento deve manter atenção constante ao instrutor/xerife.
Em marchas ordinárias, a sincronia e a organização da fila são obrigatórias.
Em marchas aceleradas, apesar do deslocamento em corrida, deve-se manter o máximo de organização possível.
Na marcha sem cadência, não é permitido correr.
Durante a apresentação do grupamento, a continência do xerife ou instrutor é obrigatória.
O superior apresentado não é obrigado a prestar continência.
O grupamento deve permanecer imóvel e em silêncio durante apresentações e comunicações formais.
Todos os comandos devem ser emitidos de forma:
Clara;
Firme;
Audível a todo o grupamento.

É responsabilidade do instrutor/xerife garantir que o grupamento compreenda o comando antes da execução.""",
    },
    "Parte 8 — Perguntas Frequentes (FAQ)": {
        "titulo": "Parte 8 — Perguntas Frequentes (FAQ)",
        "texto": """1. O que é Ordem Unida?
 É o conjunto de comandos e movimentos que padroniza a apresentação, o deslocamento e a organização do grupamento, promovendo disciplina e coesão.
2. Qual é o principal objetivo da Ordem Unida?
 Desenvolver disciplina, obediência, coordenação coletiva e postura militar.
3. Quem pode comandar a Ordem Unida?
 Militares designados como instrutores, xerifes ou responsáveis pelo grupamento.
4. O que é voz de advertência?
 É o comando usado apenas para alertar o grupamento de que uma ordem será executada.
5. A voz de advertência pode ser repetida?
 Não. Essa voz deve ser dita apenas uma vez.
6. O que é meio comando?
 É o comando que prepara o grupamento para uma movimentação específica.
7. Todo comando possui meio comando?
 Não. Apenas comandos que envolvem movimento, como marchas e volvers.
8. O que significa “Sentido”?
 Indica postura rígida, imóvel e atenta, aguardando o próximo comando.
9. Quando posso usar o comando “Descansar”?
 Somente quando o grupamento estiver em posição de sentido.
10. Qual a diferença entre “Descansar” e “À vontade”?
 “Descansar” mantém postura controlada; “À vontade” permite mais liberdade sem sair do lugar.
11. Quais são os tipos de marcha?
 Ordinário, Acelerado e Sem Cadência.
12. Qual é a marcha mais formal?
 A marcha Ordinária.
13. Em qual marcha é permitido correr?
 Apenas na marcha Acelerada.
14. O que é “Sem cadência”?
 Uma marcha informal, sem necessidade de alinhamento rigoroso e sem correr.
15. Quando devo usar “Grupamento, faz alto”?
 Exclusivamente para finalizar uma marcha.
16. Posso usar “Faz alto” em formação ou coluna?
 Não. Ele é proibido em alterações de dispositivo.
17. O que é “Fora de forma”?
 Comando utilizado para alterar o formato do grupamento.
18. “Fora de forma” serve para marchar?
 Não. Serve apenas para mudança de dispositivo.
19. O que é coluna por um?
 Formação em que os militares ficam um atrás do outro, respeitando a distância.
20. O que é formação em linha?
 Quando os militares ficam lado a lado, com a frente maior que a profundidade.
21. O que é fileira?
 Disposição dos militares lado a lado, voltados para a mesma frente.
22. Quem deve prestar continência na apresentação?
 O xerife ou instrutor é obrigado; o superior não.
23. O que são faltas na apresentação?
 Ausência de integrante no início da instrução.
24. O que são alterações na apresentação?
 Saída de integrante antes do término da instrução.
25. O grupamento deve se mover durante a apresentação?
 Não. Deve permanecer imóvel em posição de sentido.""",
    },
}


# ==============================
# SISTEMA DE WARNINGS PERSISTENTE
# ==============================
def carregar_warnings():
    if os.path.exists(ARQUIVO_WARN):
        with open(ARQUIVO_WARN, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_warnings(dados):
    with open(ARQUIVO_WARN, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


# ==============================
# CONFIGURAÇÃO DO BOT
# ==============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


# ==============================
# EVENTOS
# ==============================
@bot.event
async def on_ready():
    print(f"🤖 Bot online como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="vigilância rubra 🔴"))
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash commands: {e}")


# ==============================
# VERIFICAÇÃO DE STAFF
# ==============================
def is_staff():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        role = interaction.guild.get_role(STAFF_ROLE_ID)
        if role and role in interaction.user.roles:
            return True
        return False
    return app_commands.check(predicate)


# ==============================
# 🏃 COMANDO /percurso (SISTEMA DE DROPDOWNS)
# ==============================
class PercursoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🏁", description="Ver cargos e tempos")
            for nome in PERCURSOS.keys()
        ]
        super().__init__(placeholder="Escolha um percurso...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        percurso_escolhido = self.values[0]
        cargos = PERCURSOS[percurso_escolhido]

        embed = discord.Embed(
            title=f"🏁 {percurso_escolhido}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )

        for cargo, info in cargos.items():
            embed.add_field(
                name=f"▪️ {cargo}",
                value=f"⏱️ **Tempo:** {info['tempo']}\n🎯 **Nota mínima:** {info['nota']}",
                inline=False
            )

        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PercursoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(PercursoSelect())


@bot.tree.command(name="percurso", description="Consulta tempos e notas mínimas dos percursos")
async def percurso(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Tabela de Percursos",
        description=(
            "Escolha um percurso no menu abaixo para ver os tempos e notas mínimas.\n\n"
            "**Percursos disponíveis:**\n"
            + "\n".join(f"🏁 {nome}" for nome in PERCURSOS.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = PercursoView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# 🪖 COMANDO /ordem unida (SISTEMA DE DROPDOWNS - IDÊNTICO AO /percurso)
# ==============================
class OrdemUnidaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🪖", description="Ler esta parte do manual")
            for nome in ORDEM_UNIDA.keys()
        ]
        super().__init__(placeholder="Escolha uma parte do manual...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        parte_escolhida = self.values[0]
        info = ORDEM_UNIDA[parte_escolhida]

        embed = discord.Embed(
            title=f"🪖 {parte_escolhida}",
            description=info["texto"],
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class OrdemUnidaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(OrdemUnidaSelect())


ordem = app_commands.Group(name="ordem", description="Consultas da Ordem Rubra")


@ordem.command(name="unida", description="Consulta o Manual de Ordem Unida por partes")
async def ordem_unida(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🪖 Manual de Ordem Unida",
        description=(
            "Escolha uma parte no menu abaixo para ler o conteúdo completo.\n\n"
            "**Partes disponíveis:**\n"
            + "\n".join(f"🪖 {nome}" for nome in ORDEM_UNIDA.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = OrdemUnidaView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


bot.tree.add_command(ordem)


# ==============================
# 📊 COMANDO /nota
# ==============================
@bot.tree.command(name="nota", description="Mostra a nota mínima de aprovação de um cargo")
@app_commands.describe(cargo="Cargo para consultar a nota mínima")
@app_commands.choices(cargo=[
    app_commands.Choice(name="Recruta", value="Recruta"),
    app_commands.Choice(name="Soldado", value="Soldado"),
    app_commands.Choice(name="Terceiro-Sargento", value="Terceiro-Sargento"),
    app_commands.Choice(name="Segundo-Sargento", value="Segundo-Sargento"),
    app_commands.Choice(name="Primeiro-Sargento", value="Primeiro-Sargento"),
])
async def nota(interaction: discord.Interaction, cargo: app_commands.Choice[str]):
    valor = NOTAS_APROVACAO.get(cargo.value, "—")
    embed = discord.Embed(
        title=f"🎯 Nota mínima — {cargo.value}",
        description=f"**{cargo.value}** precisa de **{valor}** para aprovação.",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# 📅 COMANDO /cp (CAPACITAÇÃO DE PATENTE)
# ==============================
@bot.tree.command(name="cp", description="Mostra a capacitação de patente de cada patente")
async def cp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 Capacitação de Patente",
        description="Abaixo estará listada a capacitação de cada patente, sendo elas:",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )

    for grupo, itens in CAPACITACAO.items():
        embed.add_field(
            name=f"| {grupo} |",
            value="\n".join(formatar_linha_cp(item) for item in itens),
            inline=False
        )

    embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# 📌 COMANDO /requisitos
# ==============================
class RequisitosSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="📌", description="Ver patente e requisitos")
            for nome in REQUISITOS.keys()
        ]
        super().__init__(placeholder="Escolha um órgão...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        orgao = self.values[0]
        info = REQUISITOS[orgao]

        embed = discord.Embed(
            title=f"📌 Requisitos — {orgao}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="🎖️ Patente necessária", value=info["patente"], inline=False)
        embed.add_field(name="✅ Requisitos", value=formatar_lista_req(info["requisitos"]), inline=False)

        for titulo, itens in info.get("extras", {}).items():
            embed.add_field(name=titulo, value=formatar_lista_req(itens), inline=False)

        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RequisitosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RequisitosSelect())


@bot.tree.command(name="requisitos", description="Consulta a patente e os requisitos de cada órgão")
async def requisitos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📌 Requisitos dos Órgãos",
        description=(
            "Escolha um órgão no menu abaixo para ver a patente necessária e os requisitos.\n\n"
            "**Órgãos disponíveis:**\n"
            + "\n".join(f"📌 {nome}" for nome in REQUISITOS.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = RequisitosView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# ☀️ COMANDO /lema
# ==============================
@bot.tree.command(name="lema", description="Mostra o lema da Ordem Rubra")
async def lema(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☀️ Lema da Ordem Rubra",
        description=f'*"{LEMA_TEXTO}"*\n\n**{LEMA_GRITO}**',
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🛡️ COMANDOS DE MODERAÇÃO
# ==============================
@bot.tree.command(name="ban", description="Bane um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser banido", motivo="Motivo do banimento")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ Não posso banir este membro (cargo maior ou igual ao meu).", ephemeral=True)
        return
    try:
        await membro.ban(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🔴 Banimento Executado",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao banir: {e}", ephemeral=True)


@bot.tree.command(name="kick", description="Expulsa um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser expulso", motivo="Motivo da expulsão")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ Não posso expulsar este membro.", ephemeral=True)
        return
    try:
        await membro.kick(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🟠 Expulsão Executada",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao expulsar: {e}", ephemeral=True)


@bot.tree.command(name="mute", description="Silencia um membro temporariamente (timeout)")
@is_staff()
@app_commands.describe(membro="Membro a ser silenciado", duracao="Duração (ex: 10m, 1h, 1d)", motivo="Motivo")
async def mute(interaction: discord.Interaction, membro: discord.Member, duracao: str, motivo: str = "Não especificado"):
    padrao = re.compile(r"(\d+)([smhd])")
    matches = list(padrao.finditer(duracao.lower()))
    if not matches:
        await interaction.response.send_message("❌ Formato inválido. Use: `10m`, `1h`, `2d`.", ephemeral=True)
        return

    total = datetime.timedelta()
    for m in matches:
        valor = int(m.group(1))
        unidade = m.group(2)
        if unidade == 's':
            total += datetime.timedelta(seconds=valor)
        elif unidade == 'm':
            total += datetime.timedelta(minutes=valor)
        elif unidade == 'h':
            total += datetime.timedelta(hours=valor)
        elif unidade == 'd':
            total += datetime.timedelta(days=valor)

    if total > datetime.timedelta(days=28):
        await interaction.response.send_message("❌ Duração máxima: 28 dias.", ephemeral=True)
        return

    try:
        await membro.timeout(total, reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🟡 Membro Silenciado",
            description=(f"**Membro:** {membro.mention}\n"
                         f"**Duração:** {duracao}\n"
                         f"**Motivo:** {motivo}\n"
                         f"**Moderador:** {interaction.user.mention}"),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao silenciar: {e}", ephemeral=True)


@bot.tree.command(name="unmute", description="Remove o silenciamento de um membro")
@is_staff()
@app_commands.describe(membro="Membro a ser dessilenciado")
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    try:
        await membro.timeout(None, reason=f"Unmute por {interaction.user}")
        embed = discord.Embed(
            title="🔊 Membro Dessilenciado",
            description=f"**Membro:** {membro.mention}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)


@bot.tree.command(name="unban", description="Remove o banimento de um usuário pelo ID")
@is_staff()
@app_commands.describe(user_id="ID do usuário banido", motivo="Motivo do unban")
async def unban(interaction: discord.Interaction, user_id: str, motivo: str = "Não especificado"):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🟢 Banimento Removido",
            description=f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("❌ Usuário não encontrado ou não está banido.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)


@bot.tree.command(name="warning", description="Aplica uma advertência a um membro")
@is_staff()
@app_commands.describe(membro="Membro a ser advertido", motivo="Motivo da advertência")
async def warning(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    dados = carregar_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(membro.id)

    dados.setdefault(guild_id, {}).setdefault(user_id, [])
    dados[guild_id][user_id].append({
        "motivo": motivo,
        "moderador": str(interaction.user),
        "data": datetime.datetime.utcnow().isoformat()
    })
    salvar_warnings(dados)

    total = len(dados[guild_id][user_id])

    embed = discord.Embed(
        title="⚠️ Advertência Registrada",
        description=(f"**Membro:** {membro.mention}\n"
                     f"**Motivo:** {motivo}\n"
                     f"**Moderador:** {interaction.user.mention}\n"
                     f"**Total de advertências:** {total}"),
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)
    try:
        await membro.send(f"⚠️ Você recebeu uma advertência no servidor **{interaction.guild.name}**.\n**Motivo:** {motivo}\n**Total:** {total}")
    except discord.Forbidden:
        pass


@bot.tree.command(name="warnings", description="Mostra as advertências de um membro")
@is_staff()
@app_commands.describe(membro="Membro para consultar")
async def warnings(interaction: discord.Interaction, membro: discord.Member):
    dados = carregar_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(membro.id)

    lista = dados.get(guild_id, {}).get(user_id, [])

    if not lista:
        await interaction.response.send_message(f"✅ {membro.mention} não tem advertências.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"⚠️ Advertências de {membro.display_name}",
        color=discord.Color.orange()
    )
    for i, w in enumerate(lista, 1):
        embed.add_field(
            name=f"#{i} — {w['data'][:10]}",
            value=f"**Motivo:** {w['motivo']}\n**Por:** {w['moderador']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clearwarnings", description="Remove todas as advertências de um membro")
@is_staff()
@app_commands.describe(membro="Membro para limpar advertências")
async def clearwarnings(interaction: discord.Interaction, membro: discord.Member):
    dados = carregar_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(membro.id)

    if guild_id in dados and user_id in dados[guild_id]:
        dados[guild_id][user_id] = []
        salvar_warnings(dados)
        await interaction.response.send_message(f"🧹 Advertências de {membro.mention} limpas.")
    else:
        await interaction.response.send_message(f"✅ {membro.mention} já não tinha advertências.", ephemeral=True)


@bot.tree.command(name="clear", description="Apaga uma quantidade de mensagens do canal")
@is_staff()
@app_commands.describe(quantidade="Quantas mensagens apagar (1-100)")
async def clear(interaction: discord.Interaction, quantidade: int):
    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message("❌ Use um valor entre 1 e 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deletadas = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"🧹 **{len(deletadas)}** mensagens apagadas.", ephemeral=True)


@bot.tree.command(name="slowmode", description="Define o modo lento do canal em segundos")
@is_staff()
@app_commands.describe(segundos="Segundos entre mensagens (0 desativa)")
async def slowmode(interaction: discord.Interaction, segundos: int):
    if segundos < 0 or segundos > 21600:
        await interaction.response.send_message("❌ Use entre 0 e 21600 segundos (6 horas).", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=segundos)
    if segundos == 0:
        await interaction.response.send_message("⚡ Modo lento **desativado**.")
    else:
        await interaction.response.send_message(f"🐢 Modo lento definido para **{segundos}s**.")


@bot.tree.command(name="lock", description="Tranca o canal para @everyone")
@is_staff()
async def lock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔒 Canal trancado.")


@bot.tree.command(name="unlock", description="Destranca o canal para @everyone")
@is_staff()
async def unlock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔓 Canal destrancado.")


@bot.tree.command(name="userinfo", description="Mostra informações de um usuário")
@app_commands.describe(membro="Membro para consultar (opcional)")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"👤 {membro}", color=membro.color or discord.Color.blue())
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id, inline=True)
    embed.add_field(name="Apelido", value=membro.nick or "Nenhum", inline=True)
    embed.add_field(name="Bot?", value="Sim" if membro.bot else "Não", inline=True)
    embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrou em", value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "?", inline=True)
    embed.add_field(name="Cargo mais alto", value=membro.top_role.mention, inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Mostra informações do servidor")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"🏰 {g.name}", color=discord.Color.dark_red())
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="ID", value=g.id, inline=True)
    embed.add_field(name="Dono", value=g.owner.mention, inline=True)
    embed.add_field(name="Membros", value=g.member_count, inline=True)
    embed.add_field(name="Canais", value=len(g.channels), inline=True)
    embed.add_field(name="Cargos", value=len(g.roles), inline=True)
    embed.add_field(name="Criado em", value=g.created_at.strftime("%d/%m/%Y"), inline=True)
    await interaction.response.send_message(embed=embed)


# ==============================
# 🎲 COMANDOS DE DIVERSÃO
# ==============================
@bot.tree.command(name="roll", description="Rola dados no formato NdN (ex: 2d20)")
@app_commands.describe(dados="Formato NdN (ex: 1d20, 3d6, 2d10)")
async def roll(interaction: discord.Interaction, dados: str):
    try:
        rolls, limite = map(int, dados.lower().split('d'))
        if rolls > 100 or limite > 1000:
            await interaction.response.send_message("❌ Máximo: 100 dados de até 1000 lados.", ephemeral=True)
            return
        resultados = [random.randint(1, limite) for _ in range(rolls)]
        total = sum(resultados)
        resposta = ", ".join(str(r) for r in resultados)
        embed = discord.Embed(
            title=f"🎲 Rolagem: {dados}",
            description=f"**Resultados:** {resposta}\n**Total:** `{total}`",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)
    except Exception:
        await interaction.response.send_message("❌ Formato inválido! Use algo como `1d20`, `2d6`, `3d10`.", ephemeral=True)


@bot.tree.command(name="dado", description="Rola um dado de 6 lados")
async def dado(interaction: discord.Interaction):
    resultado = random.randint(1, 6)
    emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    await interaction.response.send_message(f"🎲 Você tirou: {emojis[resultado]} **{resultado}**")


@bot.tree.command(name="moeda", description="Joga uma moeda (cara ou coroa)")
async def moeda(interaction: discord.Interaction):
    resultado = random.choice(["🪙 **Cara**", "🪙 **Coroa**"])
    await interaction.response.send_message(resultado)


@bot.tree.command(name="8ball", description="Pergunte à bola mágica")
@app_commands.describe(pergunta="Sua pergunta")
async def oito_ball(interaction: discord.Interaction, pergunta: str):
    respostas = [
        "🎱 Sim, com certeza!", "🎱 Definitivamente sim!",
        "🎱 Sem dúvida!", "🎱 Pode contar com isso.",
        "🎱 Provavelmente sim.", "🎱 As perspectivas são boas.",
        "🎱 Sinais apontam que sim.", "🎱 Resposta nebulosa, tente de novo.",
        "🎱 Pergunte novamente mais tarde.", "🎱 Melhor não te contar agora.",
        "🎱 Não posso prever agora.", "🎱 Concentre-se e pergunte de novo.",
        "🎱 Não conte com isso.", "🎱 Minha resposta é não.",
        "🎱 Minhas fontes dizem não.", "🎱 As perspectivas não são boas.",
        "🎱 Muito duvidoso."
    ]
    embed = discord.Embed(title="🎱 Bola Mágica", color=discord.Color.dark_purple())
    embed.add_field(name="Pergunta", value=pergunta, inline=False)
    embed.add_field(name="Resposta", value=random.choice(respostas), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ship", description="Calcula a compatibilidade entre dois usuários")
@app_commands.describe(user1="Primeiro usuário", user2="Segundo usuário (opcional)")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member = None):
    user2 = user2 or interaction.user
    porcentagem = random.randint(0, 100)
    barra = "❤️" * (porcentagem // 10) + "🖤" * (10 - porcentagem // 10)

    if porcentagem >= 80:
        msg = "Casal perfeito! 💕"
    elif porcentagem >= 50:
        msg = "Tem potencial! 😊"
    elif porcentagem >= 20:
        msg = "Talvez com esforço... 🤔"
    else:
        msg = "Melhor continuar como amigos. 😅"

    embed = discord.Embed(title="💘 Ship", color=discord.Color.pink())
    embed.add_field(name="Casal", value=f"{user1.mention} + {user2.mention}", inline=False)
    embed.add_field(name="Compatibilidade", value=f"{barra}\n**{porcentagem}%**", inline=False)
    embed.add_field(name="Veredito", value=msg, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="abracar", description="Abraça alguém")
@app_commands.describe(membro="Quem você vai abraçar")
async def abracar(interaction: discord.Interaction, membro: discord.Member):
    embed = discord.Embed(
        title="🤗 Abraço!",
        description=f"{interaction.user.mention} abraçou {membro.mention}!",
        color=discord.Color.pink()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="beijar", description="Beija alguém")
@app_commands.describe(membro="Quem você vai beijar")
async def beijar(interaction: discord.Interaction, membro: discord.Member):
    embed = discord.Embed(
        title="😘 Beijo!",
        description=f"{interaction.user.mention} deu um beijo em {membro.mention}!",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="socar", description="Soca alguém (na brincadeira)")
@app_commands.describe(membro="Quem você vai socar")
async def socar(interaction: discord.Interaction, membro: discord.Member):
    embed = discord.Embed(
        title="👊 Pow!",
        description=f"{interaction.user.mention} socou {membro.mention}!",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sorteio", description="Sorteia um membro aleatório do servidor")
async def sorteio(interaction: discord.Interaction):
    membros = [m for m in interaction.guild.members if not m.bot]
    if not membros:
        await interaction.response.send_message("❌ Nenhum membro válido para sortear.", ephemeral=True)
        return
    escolhido = random.choice(membros)
    await interaction.response.send_message(f"🎉 O escolhido foi... {escolhido.mention}!")


@bot.tree.command(name="enquete", description="Cria uma enquete simples")
@is_staff()
@app_commands.describe(pergunta="A pergunta da enquete")
async def enquete(interaction: discord.Interaction, pergunta: str):
    embed = discord.Embed(
        title="📊 Enquete",
        description=pergunta,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Criada por {interaction.user}")
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await msg.add_reaction("🤷")


@bot.tree.command(name="ppt", description="Joga Pedra, Papel ou Tesoura contra o bot")
@app_commands.describe(escolha="pedra, papel ou tesoura")
@app_commands.choices(escolha=[
    app_commands.Choice(name="Pedra 🪨", value="pedra"),
    app_commands.Choice(name="Papel 📄", value="papel"),
    app_commands.Choice(name="Tesoura ✂️", value="tesoura"),
])
async def ppt(interaction: discord.Interaction, escolha: app_commands.Choice[str]):
    bot_escolha = random.choice(["pedra", "papel", "tesoura"])
    user = escolha.value

    if user == bot_escolha:
        resultado = "🤝 **Empate!**"
    elif (user == "pedra" and bot_escolha == "tesoura") or \
         (user == "papel" and bot_escolha == "pedra") or \
         (user == "tesoura" and bot_escolha == "papel"):
        resultado = "🎉 **Você venceu!**"
    else:
        resultado = "😢 **Você perdeu!**"

    emojis = {"pedra": "🪨", "papel": "📄", "tesoura": "✂️"}
    embed = discord.Embed(title="✂️ Pedra, Papel, Tesoura", color=discord.Color.teal())
    embed.add_field(name="Você", value=emojis[user], inline=True)
    embed.add_field(name="Bot", value=emojis[bot_escolha], inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Mostra o avatar de um usuário")
@app_commands.describe(membro="Membro (opcional)")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar de {membro.display_name}", color=membro.color or discord.Color.blue())
    embed.set_image(url=membro.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cantada", description="Recebe uma cantada aleatória")
async def cantada(interaction: discord.Interaction):
    cantadas = [
        "Você não é wifi, mas eu me conectei na hora. 📶",
        "Se beleza fosse tempo, você seria a eternidade. ⏳",
        "Você tem mapa? Porque eu me perdi nos seus olhos. 🗺️",
        "Você é a exceção de todas as minhas regras. 💫",
        "Seu nome é Google? Porque você tem tudo o que eu procuro. 🔍",
        "Você é um bug? Porque você travou meu coração. 💻",
        "Deve ser cansativo ser tão incrível assim. 😮‍💨",
        "Você não é a lua, mas ilumina a minha noite. 🌙",
    ]
    await interaction.response.send_message(random.choice(cantadas))


@bot.tree.command(name="piada", description="Conta uma piada aleatória")
async def piada_cmd(interaction: discord.Interaction):
    piadas = [
        "Por que o livro de matemática se matou? Porque tinha muitos problemas. 📘",
        "O que o pato disse para a pata? Vem quá! 🦆",
        "Por que o programador foi ao médico? Estava com um bug no sistema. 💻",
        "O que é um pontinho amarelo no céu? Um ET comendo pipoca. 👽",
        "Por que o elétron nunca erra? Porque está sempre certo. ⚡",
        "O que o zero disse para o oito? Bonito cinto! 👖",
    ]
    await interaction.response.send_message(random.choice(piadas))


# ==============================
# ERROS DE PERMISSÃO
# ==============================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Erro: {error}", ephemeral=True)


# ==============================
# INICIALIZAÇÃO
# ==============================
bot.run(DISCORD_TOKEN)
