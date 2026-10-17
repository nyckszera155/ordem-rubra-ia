import os
import re
import json
import asyncio
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

ARQUIVO_WARN = "warnings.json"
ARQUIVO_DROPDOWNS = "dropdowns.json"
ARQUIVO_ENTRADA_SAIDA = "entrada_saida.json"

# Rodapé global
FOOTER = "Configurado por Baby (nyck)"

# 🩸 Vermelho sangue puro (padrão de TODOS os embeds)
COR_SANGUE = discord.Color.from_rgb(180, 0, 0)


# ==============================
# 📋 DADOS DOS PERCURSOS
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

NOTAS_APROVACAO = {
    "Recruta": "5,0 pontos",
    "Soldado": "5,5 pontos",
    "Terceiro-Sargento": "6,0 pontos",
    "Segundo-Sargento": "6,5 pontos",
    "Primeiro-Sargento": "6,5 pontos",
}


# ==============================
# 📅 CAPACITAÇÃO DE PATENTE
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
    texto = f"▪️ **{item['cargo']}** = {item['dias']}"
    if item["detalhe"]:
        texto += f" ({item['detalhe']})"
    return texto


# ==============================
# 🪖 HIERARQUIA
# ==============================
HIERARQUIA = {
    "[GOV] Governo Federal「🔰」": ["[Pres] Presidente", "[V-Pres] Vice-Presidente"],
    "[ACE] Alto Comando do Exército「💫」": ["[Cmt] Comandante", "[SCmt] Subcomandante"],
    "[OFGE] Oficiais Generais「✨」": [
        "[Gen Ex] General-de-Exército",
        "[Gen Div] General-de-Divisão",
        "[Gen Bda] General-de-Brigada",
    ],
    "[OFSP] Oficiais Superiores「⚔️」": ["[Cel] Coronel", "[TenCel] Tenente-Coronel", "[Maj] Major"],
    "[OFIT] Oficiais Intermediários「🛡️」": ["[Cap] Capitão"],
    "[OFSB] Oficiais Subalternos「🗡️」": [
        "[1º Ten] Primeiro-Tenente",
        "[2º Ten] Segundo-Tenente",
        "[Asp] Aspirante-a-Oficial",
    ],
    "[GD] Graduados「🎓」": [
        "[ST] Subtenente",
        "[1º Sgt] Primeiro-Sargento",
        "[2º Sgt] Segundo-Sargento",
        "[3º Sgt] Terceiro-Sargento",
    ],
    "[PR] Praças「🇧🇷」": ["[Cb] Cabo", "[Sd] Soldado", "[Rcr] Recruta"],
}


def montar_texto_hierarquia():
    blocos = []
    for grupo, cargos in HIERARQUIA.items():
        blocos.append(f"**| {grupo} |**\n" + "\n".join(cargos))
    return "\n\n".join(blocos)


# ==============================
# 📌 REQUISITOS DOS ÓRGÃOS
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
    return "\n".join(f"▪️ {item}" for item in itens)


# ==============================
# ☀️ LEMA
# ==============================
LEMA_TEXTO = (
    "A cada alvorada, eis que o Sol se ergue, majestoso e tingido de carmesim, "
    "proclamando a sentença inexorável contra os corruptos e os agressores. "
    "Pois de sua luz emana o juízo, e sob seu fulgor, nenhuma injustiça permanecerá impune."
)
LEMA_GRITO = "VIDA LONGA ORDEM RUBRA!"


# ==============================
# ⚖️ REGULAMENTAÇÃO
# ==============================
REGULAMENTACAO_DADOS = {
    "Geral e Introdução": {
        "titulo": "⚖️ Regulamentação — Diretrizes Gerais",
        "texto": """O Tribunal Superior Eleitoral, na sua atribuição de estabelecer as condições de elegibilidade para os cargos de Presidente e Vice-Presidente da República, regula essas prerrogativas através da meticulosa observância e aderência aos requisitos consignados na legislação eleitoral vigente. Esses critérios, por sua vez, constituem uma compilação de exigências cuidadosamente delineadas para assegurar a indispensável aptidão dos postulantes aos mais elevados cargos executivos do Exército Brasileiro.

Ressalta-se que mesmo no caso de revogação de relatórios referentes a exílios, punições ou rebaixamentos, isso não exime os postulantes do escrutínio do histórico eleitoral. A análise e avaliação desses aspectos continuam pautadas na integridade e idoneidade dos candidatos, essenciais para desempenhar funções de destaque no cenário político militar do Exército Brasileiro.""",
    },
    "Presidente": {
        "titulo": "🎖️ Requisitos — Presidente",
        "texto": """Nesse contexto, é imprescindível destacar que, para se candidatar à presidência, o postulante deve:
▪️ Possuir a graduação de **Subtenente**.
▪️ Mínimo de **dois meses** de efetivo exercício no posto.
▪️ Apresentar uma ficha funcional desprovida de quaisquer antecedentes vinculados a rebaixamentos, exílios ou punições no âmbito do Batalhão de Polícia do Exército.
▪️ Possuir **ficha limpa**.
▪️ Demonstrar disponibilidade para demonstrar sua voz e participar ativamente dos debates presidenciais.
▪️ Tempo mínimo de **oito meses** desde o seu primeiro recrutamento no Exército Brasileiro.""",
    },
    "Vice-Presidente": {
        "titulo": "🎖️ Requisitos — Vice-Presidente",
        "texto": """Para o cargo de Vice-Presidente, as exigências estabelecem que o postulante deve:
▪️ Possuir, no mínimo, a patente de **Cabo**.
▪️ Apresentar uma ficha funcional limpa e isenta de qualquer histórico de rebaixamentos, exílios ou punições.
▪️ Demonstrar disponibilidade para utilizar a voz e participar ativamente dos debates presidenciais.
▪️ Possuir tempo mínimo de **quatro meses** desde o seu primeiro recrutamento no Exército Brasileiro.""",
    },
}


# ==============================
# 🪖 ORDEM UNIDA
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

**O QUE É ORDEM UNIDA - RESUMIDA**
A Ordem Unida é o conjunto de normas, comandos e movimentos utilizados para:
• Padronizar a apresentação do militar e do grupamento;
• Organizar o deslocamento coletivo;
• Garantir disciplina, hierarquia e harmonia nos movimentos.

Seu emprego desenvolve:
• Obediência imediata às ordens;
• Coordenação coletiva;
• Atenção, postura e autocontrole;
• Espírito de corpo e disciplina militar.

É aplicada em instruções, apresentações, deslocamentos formais e situações administrativas dentro da instituição.""",
    },
    "Parte 2 — Tipos de Comandos": {
        "titulo": "Parte 2 — Tipos de Comandos",
        "texto": """Os comandos utilizados na Ordem Unida dividem-se em vozes de comando e comandos propriamente ditos.

A **voz de comando** é utilizada para preparar o grupamento, alertando-o de que uma ação será executada. Dentro dela, destaca-se a **voz de advertência**, que serve exclusivamente como alerta inicial, não possuindo caráter de execução. Exemplos: "Grupamento", "Pelotão" e "Esquadrão". Essa voz deve ser empregada apenas uma vez.

O **meio comando** é aquele que antecede uma ação, preparando o grupamento para o movimento que será executado. É aplicável principalmente a comandos de marcha e de volver.

Os **comandos propriamente ditos** são responsáveis por iniciar ou finalizar um movimento. Exemplos: "Sentido", "Descansar", "Atenção" e "Marche".""",
    },
    "Parte 3 — Comandos de Postura": {
        "titulo": "Parte 3 — Comandos de Postura",
        "texto": """**COMANDOS BÁSICOS DE POSTURA**
O comando **"Atenção"** tem a finalidade de alertar o grupamento para o início das ordens do instrutor.
O comando **"Sentido"** determina que o grupamento permaneça imóvel, com postura ereta e mãos vazias.
O comando **"Descansar"** autoriza o grupamento a assumir a posição de descanso (válido apenas quando estiver em sentido).
O comando **"À vontade"** concede maior liberdade de movimento, desde que o militar permaneça no local.
Os comandos **"Apresentar, arma"** e **"Descansar, arma"** iniciam e finalizam a continência do grupamento.""",
    },
    "Parte 4 — Comandos de Marcha": {
        "titulo": "Parte 4 — Comandos de Marcha",
        "texto": """Existem três tipos principais de marcha: **ordinário**, **acelerado** e **sem cadência**.

• **Marcha ordinária:** a mais formal e utilizada, sem correr, com fila organizada.
• **Marcha acelerada:** deslocamento correndo, mantendo ao máximo a organização.
• **Marcha sem cadência:** informal, proibido correr.

**Sequência padrão (Marcha Ordinária):**
De frente:
`GRUPAMENTO, ATENÇÃO!`
`GRUPAMENTO, SENTIDO!`

De costas:
`EM DIREÇÃO AO (LOCAL)!`
`ORDINÁRIO!`
`MARCHE!`

Finalização (de frente):
`GRUPAMENTO, FAZ ALTO!`

Para marcha acelerada, substituir `ORDINÁRIO!` por `ACELERADO!`.
Para marcha sem cadência, substituir por `SEM CADÊNCIA!`.""",
    },
    "Parte 5 — Alteração de Dispositivo": {
        "titulo": "Parte 5 — Alteração de Dispositivo",
        "texto": """O comando **"Fora de forma"** é exclusivo para alterações de dispositivo e **jamais** deve ser utilizado para deslocamento.

**Coluna por um:** militares um atrás do outro, distância de uma pessoa entre si.

**Comandos para formar coluna:**
`GRUPAMENTO, ATENÇÃO!`
`GRUPAMENTO, SENTIDO!`
`DEVEM FORMAR UMA COLUNA POR UM EM MINHA RETAGUARDA!`
`FORA DE FORMA!`
`MARCHE!`

**Formação (ombro a ombro):**
`GRUPAMENTO, ATENÇÃO!`
`GRUPAMENTO, SENTIDO!`
`DEVEM IR ATÉ A FORMAÇÃO AO MEU LADO E FORMAR UM OMBRO A OMBRO AO MEU COMANDO!`
`FORA DE FORMA!`
`MARCHE!`

Após a formação, o grupamento entra em descanso — **não** se usa `FAZ ALTO`.""",
    },
    "Parte 6 — Comandos de Apresentação": {
        "titulo": "Parte 6 — Comandos de Apresentação",
        "texto": """**Sequência de Apresentação:**

1. Xerife (de frente para o grupamento):
`GRUPAMENTO, ATENÇÃO!`
`GRUPAMENTO, SENTIDO!`

2. Xerife vira para o superior, presta continência e diz:
`(POSTO/GRADUAÇÃO) (NOME DE GUERRA), XERIFE DO CURSO!`
`APRESENTO GRUPAMENTO PRONTO, COM/SEM FALTAS E COM/SEM ALTERAÇÕES!`

3. Superior responde:
`ESTÁ APRESENTADO.`

4. Xerife cessa continência, vira para o grupamento e comanda:
`GRUPAMENTO, DESCANSAR!`

• **Falta:** ausência de integrante no início.
• **Alteração:** saída antes do término.""",
    },
    "Parte 7 — Observações Gerais": {
        "titulo": "Parte 7 — Observações Gerais",
        "texto": """• Todos os comandos devem ser executados com o militar em posição de sentido, salvo quando o comando determinar outra postura.
• O comando `GRUPAMENTO, FAZ ALTO` é exclusivo para finalizar marchas.
• `FAZ ALTO` nunca deve ser usado em formação ou coluna.
• `FORA DE FORMA` é restrito à mudança de dispositivo.
• Na marcha sem cadência, não é permitido correr.
• A continência do xerife/instrutor é obrigatória na apresentação.
• O grupamento deve permanecer imóvel e em silêncio durante apresentações.
• Todos os comandos devem ser: **claros**, **firmes** e **audíveis**.""",
    },
    "Parte 8 — Perguntas Frequentes (FAQ)": {
        "titulo": "Parte 8 — Perguntas Frequentes (FAQ)",
        "texto": """**1.** O que é Ordem Unida? → Conjunto de comandos que padroniza apresentação, deslocamento e organização.
**2.** Qual o principal objetivo? → Desenvolver disciplina, obediência e coordenação.
**3.** Quem pode comandar? → Instrutores, xerifes ou responsáveis designados.
**4.** O que é voz de advertência? → Alerta de que uma ordem será executada.
**5.** Pode repetir voz de advertência? → Não, apenas uma vez.
**6.** O que é meio comando? → Prepara o grupamento para uma movimentação.
**7.** Todo comando tem meio comando? → Não, apenas os que envolvem movimento.
**8.** O que significa "Sentido"? → Postura rígida e imóvel.
**9.** Quando usar "Descansar"? → Somente se estiver em sentido.
**10.** Diferença "Descansar" x "À vontade"? → "À vontade" permite mais liberdade.
**11.** Tipos de marcha? → Ordinário, Acelerado e Sem Cadência.
**12.** Marcha mais formal? → Ordinária.
**13.** Onde pode correr? → Apenas na Acelerada.
**14.** O que é "Sem cadência"? → Marcha informal sem correr.
**15.** Quando usar "Faz alto"? → Exclusivamente para finalizar marcha.
**16.** Pode usar em formação/coluna? → Não.
**17.** O que é "Fora de forma"? → Alteração de formato do grupamento.
**18.** Serve para marchar? → Não, apenas mudança de dispositivo.
**19.** Coluna por um? → Militares um atrás do outro.
**20.** Formação em linha? → Lado a lado, frente maior que profundidade.
**21.** O que é fileira? → Lado a lado, voltados para mesma frente.
**22.** Quem presta continência? → O xerife; o superior não é obrigado.
**23.** O que são faltas? → Ausência no início.
**24.** O que são alterações? → Saída antes do término.
**25.** Grupamento se move na apresentação? → Não, permanece imóvel.""",
    },
}

# ==============================
# 📘 MANUAL DO CABO
# ==============================
MANUAL_CABO_DADOS = {
    "Introdução e Pontuação": {
        "titulo": "📘 Manual do Cabo — Introdução e Pontuação",
        "texto": """**Bem-vindos, Cabos!**
Sejam oficialmente recebidos e reconhecidos nesta nova fase de vossa trajetória dentro de nossa instituição. A ascensão à patente de Cabo representa não apenas um avanço hierárquico, mas sobretudo o reflexo da dedicação, disciplina e comprometimento demonstrados ao longo de cada missão cumprida, cada ordem executada e cada conduta honrada perante nossos regulamentos e tradições.

**2. TABELA DE PONTUAÇÃO**
A tabela abaixo rege o sistema de avaliação de desempenho durante o recrutamento:
▪️ **Instruções do Recrutamento:** 0,5 ponto (Obrigatória)
▪️ **Comandos falsos:** 0,2 ponto cada (Obrigatória)
▪️ **Jumping Jacks (JJ's):** 1,0 ponto (Obrigatória)
▪️ **1º, 2º e 3º Parkour:** 1,0 ponto cada (Obrigatória)
▪️ **Comandos Volver:** 0,5 ponto (Obrigatória)
▪️ **Avaliação Gramatical:** 2,0 pontos (Obrigatória)
▪️ **Teste de Conhecimento:** 0,2 ponto cada (Opcional)"""
    },
    "Passo 1 ao 4: Preparação e Checagem": {
        "titulo": "📘 Manual do Cabo — Passos 1 ao 4",
        "texto": """**1º PASSO: ORGANIZE A FILA DO PORTÃO**
Instrua os civis a formarem uma fila ordenada, seguindo as orientações. Mesmo fora do quartel, devem manter a disciplina, permanecendo em suas marcações, sem brincadeiras, e aguardando a abertura do portão.

**2º PASSO: ORGANIZE A FILA SOB A LINHA AMARELA**
Permita a entrada controlada dos civis para o local do detector. Abra o portão e organize os civis sob a linha amarela. Posicionar-se adequadamente em frente ao detector enquanto aguarda a entrada dos civis evita a situação de eles passarem pelo detector sem sua autorização. Após a entrada de todos os civis, o portão deve ser fechado novamente.

**3º PASSO: CHECK - VALIDE OS CIVIS**
Realize a checagem individual de cada civil que entrou, verifique se não possuem cargo ativo em outra instituição militar. Antes de iniciar o recrutamento, é obrigatório realizar a checagem individual de cada civil presente, garantindo que nenhum deles possua cargo ativo em outra instituição militar. 
*Atenção:* o nome em vermelho nem sempre indica uma instituição militar. Nesses casos, verifique o cargo do jogador para confirmar.

**4º PASSO: PRANCHETA - REGISTRE OS CIVIS**
Após a validação de todos os civis, registre-os na prancheta oficial. Ative a "Prancheta" e adicione o nome de cada um."""
    },
    "Passo 5 ao 8: Detector, Instruções e Marcha": {
        "titulo": "📘 Manual do Cabo — Passos 5 ao 8",
        "texto": """**5º PASSO: PASSE OS CIVIS PELO DETECTOR**
Após registrá-los, encaminhe os civis para passarem pelo detector, pois este sistema irá remover qualquer objeto do inventário do civil. Permaneça atento aos civis que já conhecem o sistema e tentam burlar o procedimento saltando o detector sem serem notados. Recomendamos a passagem de um civil por vez.

**6º PASSO: APLIQUE AS INSTRUÇÕES INICIAIS**
Na área de instrução ao lado do detector, forneça as informações básicas sobre o recrutamento, tais como:
1) Utilização correta dos pronomes;
2) Uso apropriado da gramática;
3) Restrição ao uso de chat por voz (chat-voice);
4) Duração do processo de recrutamento;
5) Esclarecimento de que o recrutamento é baseado em um sistema de pontuação (atenção: não divulgar os valores dos pontos);
6) Comportamento disciplinado.

**7º PASSO: APLIQUE A PRIMEIRA MARCHA**
Após as Instruções Iniciais, os civis devem ser conduzidos a área de recrutamento. Como esta é sua primeira marcha oficial e eles ainda não conhecem os comandos de Ordem Unida, é essencial explicar brevemente cada comando. 
*Comandos:* FILA ÚNICA! / SENTIDO! / PREPARAR PARA MARCHAR! / MARCHANDO! / AUTO! / STS!

**8º PASSO: APLIQUE O SCRIPT DE RECRUTAMENTO**
Siga o roteiro oficial do processo, explicando cada etapa. Ao final de cada instrução, faça sempre a pergunta: “Alguma dúvida?”.
*Respostas esperadas:* “Sim, Cabo.” ou “Não, Cabo.”
É importante reforçar que os civis não podem cometer mais de 3 erros no processo de recrutamento. Caso atinjam 4 erros, devem ser automaticamente reprovados."""
    },
    "Passo 9 ao 13: Práticas e Parkour": {
        "titulo": "📘 Manual do Cabo — Passos 9 ao 13",
        "texto": """**9º PASSO: APLIQUE A SEGUNDA MARCHA E COMANDOS FALSOS**
Desloque os civis para a parte externa da área de recrutamento. Este é um momento oportuno para aplicar comandos falsos, acerta o civil que não executar o comando falso, reforçando atenção, obediência e disciplina.
*ATENÇÃO PONTUAÇÃO:* atribua 0,2 ponto a cada civil que acertar cada comando falso.

**10º PASSO: REALIZE O AQUECIMENTO COM JUMPING JACKS (JJ’S)**
Promova um breve aquecimento físico com exercícios coordenados. Lembre-se de instruir os civis sobre como ativar e como executar o JJ’s.
*ATENÇÃO PONTUAÇÃO:* atribua 1,0 ponto a cada civil que concluir esta etapa com sucesso.

**11º, 12º e 13º PASSOS: DESAFIOS DE "PARKOUR"**
Inicie os circuitos de parkour para testar a agilidade dos civis. É essencial explicar claramente as regras aos civis (o que é permitido e proibido, como burlar ou cortar caminho). Informe a duração da atividade (35-40 segundos), os comandos de início e o que deve ser feito ao término do tempo.
*ATENÇÃO PONTUAÇÃO:* atribua 1,0 ponto a cada civil que concluir cada “parkour” com sucesso."""
    },
    "Passo 14 ao 17: Volver, Gramática e Notas": {
        "titulo": "📘 Manual do Cabo — Passos 14 ao 17",
        "texto": """**14º PASSO: APLIQUE OS COMANDOS VOLVER**
Teste a capacidade dos civis de seguir comandos de movimentação com precisão.
*Comandos:* DIREITA VOLVER! / ESQUERDA VOLVER! / RETAGUARDA VOLVER! / CENTRAL FACE!
*ATENÇÃO PONTUAÇÃO:* atribua 0,5 ponto a cada civil que acertar todos os comandos.

**15º PASSO: APLIQUE A AVALIAÇÃO GRAMATICAL**
Será aplicada uma atividade escrita (mínimo 2 linhas completas). São permitidos apenas erros leves. O conteúdo deve ser coerente com o tema proposto. Não é permitido o uso de IA.
*Temas:* Como foi o processo de recrutamento na sua opinião? / O que foi mais importante neste recrutamento para você? / O que você achou do meu recrutamento?
*ATENÇÃO PONTUAÇÃO:* atribua até 2,0 pontos a cada civil que desenvolver o texto seguindo todas as orientações.

**16º PASSO: APLIQUE O TESTE DE CONHECIMENTO (OPCIONAL)**
Aplique uma avaliação teórica sobre temas das instruções recebidas (ex: O que é “PPAI”? O que é “PPSI”?). Útil para civis com desempenho parcial.
*ATENÇÃO PONTUAÇÃO:* atribua 0,2 ponto a cada civil que acertar cada resposta.

**17º PASSO: VALIDE A PONTUAÇÃO FINAL**
Some as pontuações da prancheta e verifique quem atingiu a nota mínima. Mantenha tudo organizado para garantir uma avaliação justa."""
    },
    "Passo 18 ao 22: Resultados e Relatório": {
        "titulo": "📘 Manual do Cabo — Passos 18 ao 22",
        "texto": """**18º PASSO: COMUNIQUE OS RESULTADOS**
Anuncie os resultados de forma clara e respeitosa aos participantes.

**19º PASSO: COLETE A PROVA DO RECRUTAMENTO**
Registre a aprovação com capturas de tela dos aprovados.

**20º PASSO: VALIDE OS CIVIS APROVADOS NO RELATÓRIO DE EXÍLIO PERMANENTE**
Confirme se algum participante está em exílio permanente ou possui mais de três exílios convencionais. Consulte no Discord, no canal “relatórios-de-exilio-permanente”.

**21º PASSO: REDIJA O RELATÓRIO DE RECRUTAMENTO VIA PRANCHETA**
1) Abra a prancheta; 2) Limpe todas as observações; 3) Clique no ícone do "Sistema de Relatório"; 4) Selecione "Recrutamento"; 5) Selecione os aprovados (botão verde); 6) Selecione os reprovados (botão vermelho); 7) Clique em "Avancar"; 8) Clique em "Liberar acesso para editar"; 9) Revise e edite; 10) Copie o texto gerado.

**22º PASSO: PUBLIQUE O RELATÓRIO DE RECRUTAMENTO NO CANAL DO EB (DISCORD)**
*Regras fundamentais:*
▪️ Não altere o modelo base.
▪️ O relatório deve estar inteiramente em negrito.
▪️ Não use itálico, sublinhado, emojis.
▪️ Jamais utilize IA para gerar o relatório.
▪️ Nunca publique um relatório sem provas anexadas.
▪️ O número do relatório deve vir junto aos dois pontos: Relatório N°:01▪️ Não mencione o @ de outras pessoas.
▪️ Não use ponto final nos itens "Civis", "Aprovados" e "Reprovados".
▪️ Não comece as observações com letra maiúscula.
▪️ Valide sempre o número do seu último relatório postado."""
    },
    "Passo 23: Aprovação na Comunidade": {
        "titulo": "📘 Manual do Cabo — Passo 23",
        "texto": """**23º PASSO: APROVE AS SOLICITAÇÕES DOS CIVIS NA COMUNIDADE (ROBLOX)**
Por fim, acesse o grupo da comunidade e aceite as solicitações dos civis aprovados. Só realize a aprovação após concluir todas as etapas dos passos 25 e 26. Jamais aprove um civil antes da publicação oficial do relatório.

**ATENÇÃO MÁXIMA:** Nunca clique em “Aceitar todos” ou “Recusar todos”! Se isso acontecer, você será automaticamente punido com rebaixamento, exílio e, dependendo da gravidade, até exílio permanente. FIQUE ATENTO: Os botões são parecidos e ficam muito próximos um do outro."""
    },
    "Regras e Promoção de Patente": {
        "titulo": "📘 Manual do Cabo — Regras e Promoção",
        "texto": """**4. REGRAS ESSENCIAIS SOB MEDIDAS DISCIPLINARES**
1) Não desrespeite os civis.
2) Nunca recrute um militar já alistado em outra instituição.
3) Nunca abra o portão por motivos que não sejam o recrutamento.
4) Nunca execute um civil sem antes orientá-lo sobre o motivo da reprovação.
5) Se estiver apenas auxiliando, jamais execute um civil sem autorização do instrutor.
6) Nunca favoreça um civil aplicando critérios especiais.
7) Nunca deixe de aplicar uma etapa obrigatória.
8) Nunca deixe de postar o relatório de recrutamento.
9) Nunca aprove um civil de forma deliberada e sem os devidos critérios.
10) Nunca realize um recrutamento em servidor privado.
11) Nunca facilite ou favoreça a aprovação de um civil.
12) Não conceda privilégios individuais usando o “Chat-Voice”.
13) Não realize o recrutamento por chat-voice.
14) Respeite os limites e capacidades de cada civil.
15) Nunca aplique pressão psicológica.
16) Na comunidade, jamais clique em “Aceitar todos” ou “Reprovar todos”.

**5. DIRETRIZES PARA PROMOÇÃO DE PATENTE**
▪️ **Como subir de patente?** Fazer a ESA. Antes, é necessário concluir a Capacitação de Patente (CP): entregar 3 relatórios de recrutamento e aguardar 3 dias.
▪️ **Como faço a prova da ESA?** Acontecem aos domingos. Inscrição via formulário no canal oficial. Tempo: 1h30min.
▪️ **Existe outra forma?** Não. O CFAP ajuda nos estudos, mas não substitui a ESA.
▪️ **Fazer a ESA é obrigatório?** Só se quiser subir de patente.
▪️ **Como estudar?** Documentos oficiais, leis, dicas de gramática e o CFAP.
▪️ **O que fazer se aprovado?** Escolher um membro da ESA, enviar print da lista e seu nome de usuário do Roblox.
▪️ **O que fazer se reprovado?** A equipe enviará a correção por e-mail. Continue estudando."""
    }
}

# ==============================
# 📘 MANUAL DO RECRUTA
# ==============================
MANUAL_RECRUTA_DADOS = {
    "Introdução": {
        "titulo": "📘 Manual do Recruta — Introdução",
        "texto": """Inicialmente gostaríamos de parabenizar você, o mais novo Recruta do Exército Brasileiro. O seu esforço durante o recrutamento foi reconhecido e fez com que você chegasse até aqui, parabéns.

Agora iremos continuar com a fase de aprendizagem regras e “bizus” para você ter uma boa convivência e iniciar sua carreira com o “pé direito” no EB.

Nas próximas páginas serão descritas todas as instruções necessárias para que você, Recruta, esteja no EB com as condições precisas para aprender e se portar."""
    },
    "Como se Verificar?": {
        "titulo": "📘 Manual do Recruta — Como se Verificar?",
        "texto": """Caso você seja um Recruta e já esteja dentro do grupo do Exército Brasileiro do Roblox, o próximo passo a ser seguido é o de entrar no grupo do Discord.

**Passo 1:** Entre na página do Roblox. Em seguida, entre no jogo da instituição.
**Passo 2:** Agora, arraste sua tela para baixo, encontrando algo parecido com o ícone do Discord ou escrito como “Servidor” e clique nele. Lembrando que deve ter uma conta no Discord, caso não tenha, não conseguirá entrar no servidor.
**Passo 3:** Agora que já entrou no Discord da instituição, clique no canal chamado “[✓] verificação”.
**Passo 4:** Clique em “Verify with Bloxlink” e logo em seguida irá receber sua patente."""
    },
    "Como Subir de Patente?": {
        "titulo": "📘 Manual do Recruta — Como Subir de Patente?",
        "texto": """Atualmente há duas formas de você, Recruta, subir de patente, sendo elas:

**FORMULÁRIOS:** os formulários são como se fosse uma prova que você realizou e caso possua a nota suficiente para aprovação, seu nome é postado no canal de relatórios de treino, sendo promovido para Soldado. Qualquer Recruta pode realizar o formulário, desde que sempre siga algumas regras, sendo elas:
I. NUNCA peça resposta do formulário.
II. NUNCA diga que fez o formulário.
III. NUNCA peça para que um Oficial poste um formulário.
IV. NUNCA dê a resposta de formulário para outros.
V. NUNCA use inteligência artificial (IA) para fazer um formulário.
VI. NUNCA cole.

**TREINAMENTOS:** os treinamentos são provas práticas no qual farás e caso consiga uma pontuação suficiente poderá ser promovido para Soldado. Os treinamentos normalmente sempre serão postados no canal chamado “[⏰] horários”."""
    },
    "Advertências e Punições": {
        "titulo": "📘 Manual do Recruta — Advertências e Punições",
        "texto": """Nossas legislações são feitas para serem cumpridas, porém, existem diversos casos onde infratores delas acabam infringindo elas e estarão sujeitos às seguintes penalidades e formas de advertências:
I - Aviso verbal
II - Punição
III - Rebaixamento
IV - Exílio
V - Exílio permanente
VI - Banimento por IP.

**O quadro a seguir estabelece as penalidades aplicáveis a cada artigo da legislação:**
➔ Artigo 7 – Exílio permanente;
➔ Artigo 8 – Exílio permanente;
➔ Artigo 9 – Punição em JJ's, rebaixamento ou exilio;
➔ Artigo 10 – Rebaixamento ou exílio;
➔ Artigo 11 – Exílio;
➔ Artigo 12 – Exílio;
➔ Artigo 13 – Exílio;
➔ Artigo 14 – Punição em JJ's ou rebaixamento;
➔ Artigo 15 – Exílio;
➔ Artigo 16 – Punição em JJ's até exílio permanente;
➔ Artigo 17 – Rebaixamento para Graduado;
➔ Artigo 18 – Exílio;
➔ Artigo 19 – Punição em JJ's ou exílio;
➔ Artigo 20 – Punição em JJ's (casos leves) ou exílio permanente (em caso de tentativa de burlar o sistema de relatórios);
➔ Artigo 21 – Exílio;
➔ Artigo 22 – Exílio permanente;
➔ Artigo 23 – Punição em JJ's até exílio;
➔ Artigo 24 – Advertência ou rebaixamento;
➔ Artigo 25 – Exílio permanente;
➔ Artigo 27 – Exílio permanente;
➔ Artigo 28 – Exílio;
➔ Artigo 29 – Exílio permanente;
➔ Artigo 30 – Exílio permanente;
➔ Artigo 31 – Exílio permanente;
➔ Artigo 32 – Rebaixamento e demissão do batalhão;
➔ Artigo 33 – Exílio permanente;
➔ Artigo 34 – Exílio;
➔ Artigo 35 – Exílio até exílio permanente;
➔ Artigo 36 – Exílio;
➔ Artigo 37 – Exílio;
➔ Artigo 43 – Exílio;
➔ Artigo 44 – Rebaixamento para Cabo;
➔ Artigo 47 – Rebaixamento para Cabo;
➔ Artigo 53 – Exílio permanente;
➔ Artigo 54 – Exílio;
➔ Artigo 55 – Banimento;
➔ Artigo 56 – Exílio; se comprovada má-fé, exílio permanente;
➔ Artigo 57 – Exílio permanente;
➔ Artigo 59 – Exílio permanente;
➔ Artigo 60 – Advertência ou rebaixamento;
➔ Artigo 61 – Rebaixamento ou exílio;
➔ Artigo 64 – Exílio até exílio permanente;
➔ Artigo 65 – Exílio permanente."""
    },
    "Sua Função como Recruta": {
        "titulo": "📘 Manual do Recruta — Sua Função",
        "texto": """Como Recruta, você desempenha funções essenciais para a ordem, disciplina e segurança do aquartelamento. Abaixo estão suas responsabilidades explicadas de forma clara e objetiva:

**I - Garantir a segurança interna e externa do quartel.**
→ Sua principal obrigação é zelar pela proteção do aquartelamento, tanto na parte interna quanto na externa, sempre respeitando os limites de atuação do Recruta. Em situações extremas e devidamente justificadas, o uso da força pode ser necessário, sempre seguindo as regras e normas vigentes.

**II – Manter os civis afastados do portão e impedir desordens.**
→ Você deve orientar e afastar civis que se aproximarem do portão sem autorização, prevenindo tumultos, badernas e qualquer comportamento que possa comprometer a rotina do quartel ou a segurança dos militares.

**III - Informar superiores sobre badernas e condutas inadequadas.**
→ Se identificar civis ou outros Recrutas causando baderna, desrespeitando normas ou insistindo em comportamentos inadequados, é seu dever comunicar imediatamente aos superiores. Civis reincidentes podem ser registrados em uma espécie de "lista restritiva", o que impede sua entrada futura no meio militar. Cada caso será avaliado conforme a gravidade da atitude e as regras internas do Exército.

**IV - Realizar auxílios em Recrutamentos de seus superiores hierárquicos.**
→ Como Recruta, é seu dever auxiliar seus superiores durante processos de recrutamento, garantindo que todo o procedimento ocorra de forma organizada, disciplinada e dentro das normas. Esse auxílio inclui orientar civis que chegam para o recrutamento, manter a ordem no ambiente, prestar informações básicas quando solicitado e apoiar o superior responsável em qualquer necessidade operacional. O Recruta não toma decisões no processo, mas atua como apoio para agilizar, organizar e assegurar que o recrutamento siga os padrões estabelecidos pelo Exército. Seu comportamento deve demonstrar disciplina, postura militar e respeito à hierarquia, fortalecendo a imagem da instituição e contribuindo diretamente para a formação de novos integrantes."""
    },
    "Capacitação de Patente (CP)": {
        "titulo": "📘 Manual do Recruta — Capacitação de Patente",
        "texto": """A Capacitação de Patente (CP) é o período obrigatório que o militar deve cumprir antes de estar apto a uma nova promoção, desde que seja aprovado nos treinamentos exigidos. Ela existe para manter equilíbrio nas promoções e garantir tempo suficiente para o desenvolvimento das habilidades necessárias à patente atual.

A CP é contada em tempo corrido: cada dia representa 24 horas após a publicação do relatório oficial. Após ser promovido, o militar deve cumprir a quantidade mínima de recrutamentos exigida para sua nova patente. Essa contagem é acumulativa, ou seja, não reinicia a cada promoção — apenas continua a partir do número já alcançado.

As CP’s são zeradas no momento da promoção, reiniciando automaticamente o tempo necessário para a próxima progressão.

**Exemplo:** fui promovido dia 21/12/2024 às 21:39. Se você realizar qualquer tentativa de subida de patente, antes do dia 22/12/2024 às 21:39, não será promovido.

**Para quem for Cabo ou superior:** deve a cada promoção, realizar a quantidade de relatórios de recrutamentos que é pedido ao lado da capacitação de dias.

**Exemplo:** sou Terceiro-Sargento e desejo me tornar Segundo-Sargento e passei na ESA anteriormente. Possuo 0 relatórios de recrutamentos que foram resetados, mas pode dar continuidade ao número de relatórios normalmente, ou seja, os 3 que chegou a realizar como Cabo. Então, para se tornar Segundo-Sargento, deve realizar 5 relatórios de recrutamentos e esperar 4 dias para subir de patente."""
    },
    "Cursos": {
        "titulo": "📘 Manual do Recruta — Cursos",
        "texto": """Vocês como Recrutas, contém direitos de participação em cursos especializados em áreas específicas. No caso somente de Recrutas ou Praças, existe somente um curso no qual serve para aperfeiçoamento de Praças, conhecido como **CFAP (Curso de Formação e Aperfeiçoamento de Praças)**.

Irão encontrá-lo na categoria de “Cursos”. Qualquer Recruta, Soldado ou Cabo pode fazê-lo."""
    },
    "Denúncias": {
        "titulo": "📘 Manual do Recruta — Denúncias",
        "texto": """Existem diversas formas de realizar uma denúncia no âmbito do Discord, e irei mostrar todos esses métodos para que tentem utilizar quaisquer dessas opções viáveis e não omitem nada que envolva um infrator na quebra das normas.

**1. Tíquetes**
Há como vocês realizarem denúncias através de tíquetes, no servidor de tíquetes.
Realização de denúncias; Respostas de dúvidas; Solicitação de evidências de exílios e rebaixamentos; Contato com o suporte.
**Convite:** https://discord.gg/fmBXTPBjYw

*Para realizar uma abertura de tíquete de denúncias, basta vir na aba "Solicitar Suporte" > "[🎫] abrir-tiquete". E, abrir ademais opções dentro do canal no "Ticket Tool", mostrando 4 categorias de aberturas, basta clicar em "Denúncias".*

**2. Privado de um membro da Secretária Geral do Exército**
Basta entrar em contato com algum membro da Secretária, que eles podem te atender via privado para pegar todas suas denúncias. Lembrando que não podem conversar com Oficial em privado devido ao Artigo 17, mas qualquer outro que não seja Oficial, de preferência da Secretária Geral do Exército, irão ajudar muito vocês.

**3. Blox.Report**
O Blox.Report é um novo método utilizado recentemente em nosso servidor, disponível para Cabos, Graduados e booster’s do servidor. Portanto, caso tenha alguma denúncia, pode mandar para essas pessoas citadas, que eles poderão encaminhar através do BloxReport."""
    },
    "Conduta e Vestimenta": {
        "titulo": "📘 Manual do Recruta — Conduta e Vestimenta",
        "texto": """Você como Recruta, deve-se atentar a normas e questões do cotidiano.

**Conduta**
➡️ Em todo momento, você deve manter postura respeitosa com todos ao seu redor. Como Recruta, estará constantemente diante de militares hierarquicamente superiores, e por isso é essencial obedecer prontamente e oferecer auxílio sempre que necessário.

Um exemplo de boa conduta é, ao solicitar “PPA!” e ter a permissão concedida, agir de forma organizada e colaborativa: ajude no que for preciso, sem atrapalhar o instrutor do recrutamento, evitando permanecer colado a ele e garantindo espaço adequado para os demais militares.

Seja responsável, tenha iniciativa e mantenha uma postura firme e ativa. Um bom Recruta é aquele que contribui com todos, demonstra disciplina e fortalece o ambiente militar com suas atitudes.

**Vestimenta**
Atentem-se sempre às roupas que utilizam. É permitido usar qualquer vestimenta que faça referência ao militarismo, desde que não contenha símbolos, insígnias e identificações de Divisões, Cursos ou Subdivisões, pois essas são restritas e não devem ser utilizadas por quem não as possui.

Priorize itens como boinas, coletes, mochilas, máscaras, óculos e acessórios militares em geral. A maioria desses itens é opcional, porém a boina é obrigatória, podendo ser substituída apenas por um gorro ou chapéu, caso autorizado.

Por fim, evite utilizar qualquer tipo de fardamento pertencente a Divisões, Cursos ou unidades específicas, preservando o respeito à hierarquia."""
    }
}

# ==============================
# 🗳️ HISTÓRICO PRESIDENCIAL
# ==============================
HISTORICO_PRESIDENCIAL_DADOS = {
    "Lista Completa": {
        "titulo": "🗳️ Histórico Presidencial — Lista Completa",
        "texto": """**PRIMEIRA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** xPlayDarkOFCx
▪️ **Vice-Presidente:** XTheGeovaManX
*Eleitos no dia 26/03/2023*

**SEGUNDA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** xPlayDarkOFCx
▪️ **Vice-Presidente:** 64x99s
*Eleitos no dia 26/11/2023*

**TERCEIRA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** IFelipe_GT3I
▪️ **Vice-Presidente:** Naremató
*Eleitos no dia 26/07/2024*

**QUARTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** ProGamers2k23
▪️ **Vice-Presidente:** GiihRamos
*Eleitos no dia 26/03/2025*

**QUINTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** ivan4015
▪️ **Vice-Presidente:** Mary091314
*Eleitos no dia 26/11/2025*

**SEXTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** vZeddy
▪️ **Vice-Presidente:** xPlayDarkOFCx
*Eleitos no dia 26/07/2026*"""
    },
    "Últimas Eleições": {
        "titulo": "🗳️ Histórico Presidencial — Últimas Eleições",
        "texto": """**QUARTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** ProGamers2k23
▪️ **Vice-Presidente:** GiihRamos
*Eleitos no dia 26/03/2025*

**QUINTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** ivan4015
▪️ **Vice-Presidente:** Mary091314
*Eleitos no dia 26/11/2025*

**SEXTA ELEIÇÃO PRESIDENCIAL**
▪️ **Presidente:** vZeddy
▪️ **Vice-Presidente:** xPlayDarkOFCx
*Eleitos no dia 26/07/2026*"""
    }
}

# ==============================
# 🏷️ PRONOMES
# ==============================
PRONOMES_DADOS = {
    "Geral e Hierarquia": {
        "titulo": "🏷️ Pronomes — Geral e Hierarquia",
        "texto": """**NO CONTEXTO MILITAR, “PATENTE”, “POSTO” E “GRADUAÇÃO” SÃO TERMOS RELACIONADOS À HIERARQUIA, MAS CADA UM POSSUI SIGNIFICADO ESPECÍFICO.**

**1. Patente:**
É o termo abrangente que designa o título ou distinção conferida a um militar, englobando **Oficiais** e **Praças**. A patente representa oficialmente a posição hierárquica dentro da instituição.

**2. Posto:**
Aplica-se exclusivamente aos **Oficiais** (por exemplo: Tenente, Capitão, Major). O posto indica uma posição elevada na hierarquia e está associado a funções de comando.

**3. Graduação:**
Refere-se especificamente à posição hierárquica dos **Graduados** (como Sargentos e Subtenentes).

- Postos são destinados aos **Oficiais**.
- Graduações aplicam-se aos **Graduados**.
- Patente é o conceito amplo que engloba ambos.

**Art. 14 – Da Utilização dos Pronomes**
*Art. 14 — Fica estabelecida a obrigatoriedade da utilização de pronomes e formas de tratamento apropriadas em todas as comunicações dirigidas aos militares do Exército Brasileiro, sejam elas verbais ou escritas, assegurando o respeito à hierarquia, à disciplina e às tradições militares.*
Essa obrigatoriedade inclui a aplicação adequada do pronome “Senhor”, quando pertinente, bem como o endereçamento correto conforme posto ou graduação, conforme descrito nas diretrizes abaixo."""
    },
    "Autoridades e Oficiais Generais": {
        "titulo": "🏷️ Pronomes — Autoridades e Oficiais Generais",
        "texto": """**1. Autoridades Superiores e Governo Federal**
❖ **Desenvolvedores**
➔ *Apex_Hard* - Embora não tenha sido informado qualquer pronome de referência, deve-se manter o devido respeito ao dirigir-se a ele.
➔ *Manager* - Senhor(a) Manager

❖ **Supremo Tribunal Federal**
➔ *[STF]* - Vossa Excelência

❖ **Tribunal Superior Eleitoral**
➔ *[TSE]* - Vossa Excelência

❖ **Governo Federal**
➔ *Presidente da República* - Presidente ou Vossa Excelência
➔ *Vice-Presidente da República* - Vice-Presidente ou Vossa Excelência

**2. Alto Comando do Exército**
*Modelo:* Senhor + Posto + Nome de Guerra
*Exemplos:*
Senhor(a) Comandante (Nome de Guerra) | Comandante (Nome de Guerra)
Senhor(a) Subcomandante (Nome de Guerra) | Subcomandante (Nome de Guerra)

**3. Oficiais Generais**
*Modelo:* Senhor + Posto + Nome de Guerra
*Exemplos:*
Senhor(a) General-de-Exército (Nome de Guerra) ou Senhor(a) General (Nome de Guerra)
Senhor(a) General-de-Divisão (Nome de Guerra) ou Senhor(a) General (Nome de Guerra)
Senhor(a) General-de-Brigada (Nome de Guerra) ou Senhor(a) General (Nome de Guerra)"""
    },
    "Oficiais e Praças": {
        "titulo": "🏷️ Pronomes — Oficiais e Praças",
        "texto": """**4. Oficiais Superiores**
*Modelo:* Senhor + Posto + Nome de Guerra
*Exemplos:*
Senhor(a) Coronel (Nome de Guerra) ou Coronel (Nome de Guerra)
Senhor(a) Tenente-Coronel (Nome de Guerra) ou Tenente-Coronel (Nome de Guerra)
Senhor(a) Major (Nome de Guerra) ou Major (Nome de Guerra)

**5. Oficiais Intermediários**
*Modelo:* Senhor + Posto + Nome de Guerra
*Exemplos:*
Senhor(a) Capitão ou Capitão (Nome de Guerra)
Senhor(a) Capitão ou Capitão (Nome de Guerra)

**6. Oficiais Subalternos**
*Modelo:* Senhor + Posto + Nome de Guerra
*Exemplos:*
Senhor Primeiro-Tenente ou Tenente (Nome de Guerra)
Senhor Segundo-Tenente ou Tenente (Nome de Guerra)
Senhor Aspirante-a-Oficial ou Tenente (Nome de Guerra)

**7. Graduados**
O uso de “Senhor” permanece obrigatório em comunicações formais — conforme o Art. 14
*Modelos:* Senhor + Graduação + Nome de Guerra (formal) | Graduação + Nome de Guerra (no cotidiano)
*Exemplos:*
Senhor Subtenente (Nome de Guerra) | Subtenente (Nome de Guerra)
Senhor Primeiro-Sargento (Nome de Guerra) | Sargento (Nome de Guerra)
Senhor Segundo-Sargento (Nome de Guerra) | Sargento (Nome de Guerra)
Senhor Terceiro-Sargento (Nome de Guerra) | Sargento (Nome de Guerra)

**8. Praças**
*Modelos:* Senhor + Patente + Nome de Guerra (formal) | Patente + Nome de Guerra (uso cotidiano)
*Exemplos:*
Senhor Cabo (Nome de Guerra) | Cabo (Nome de Guerra)
Senhor Soldado (Nome de Guerra) | Soldado (Nome de Guerra)
Recruta (Nome de Guerra)"""
    },
    "Divisões/Unidades Administrativas": {
        "titulo": "🏷️ Pronomes — Divisões/Unidades Administrativas",
        "texto": """**Centro de Inteligência do Exército (CIE)**
❖ **Alto Comando**
➔ [Cmt-CIE] - Senhor(a) Comandante
➔ [Dir-CIE] - Senhor(a) Diretor(a)
❖ **Alto Escalão**
➔ [Coms-Intlg-CIE] - Senhor(a) Comissário(a) de Inteligência
➔ [Insp-CIE] - Senhor(a) Inspetor(a)
➔ [Pto-Crim-CIE] - Senhor(a) Perito(a) Criminal
➔ [Prom-Exec-CIE] - Senhor(a) Promotor(a) Executivo
❖ **Agentes Superiores**
➔ [Ag-Esp-CIE] - Senhor(a) Agente Especial
➔ [Sup-Inv-CIE] - Senhor(a) Superintendente Investigativo
➔ [Ch-Gab-CIE] - Senhor(a) Chefe de Gabinete
➔ [Sup-CIE] - Senhor(a) Supervisor(a)
➔ [Del-CIE] - Senhor(a) Delegado(a)
❖ **Agentes**
➔ [Ag-CIE] ou [Ag-Jr-CIE] - Agente
❖ **Estagiários**
➔ [Est-CIE] - Estagiário"""
    },
    "Divisões Operacionais": {
        "titulo": "🏷️ Pronomes — Divisões Operacionais",
        "texto": """**Batalhão de Polícia do Exército (BPE)**
❖ **Alto Comando/Oficiais**
➔ [Ten-PE] ou Superior - Senhor(a) Policial
❖ **Graduados e Praças**
➔ [Sd-PE] ou Superior - Policial
❖ **Candidatos**
➔ [C-PE] - Candidato

**Batalhão de Forças Especiais (BFEsp)**
❖ **Alto Comando/Oficiais**
➔ [FE-Ten] ou Superior - Senhor(a) Fantasma
❖ **Graduados e Praças**
➔ [FE-Sd] ou Superior - Fantasma
❖ **Candidatos**
➔ [FE-C] - Candidato

**Batalhão de Ações de Comandos (BAC)**
❖ **Alto Comando**
➔ [BAC-S Cmt] ou Superior - Senhor(a) Comandos
❖ **Graduados, Praças e Oficiais**
➔ [BAC-Sd] ou Superior - Comandos
❖ **Candidatos**
➔ [BAC-A] - Aluno ou Caveira

**Comando de Operações Especiais (COpEsp)**
❖ **Alto Comando/Oficiais**
➔ [COpEsp] Oficial de Operações ou Superior - Senhor(a) Espectro
❖ **Graduados/Praças**
➔ [COpEsp] Operador de Campo ou Superior - Espectro"""
    },
    "Subdivisões": {
        "titulo": "🏷️ Pronomes — Subdivisões",
        "texto": """**Superior Tribunal Militar (STM)**
➔ Magistrado/Juiz - Meritíssimo(a) ou Vossa Excelência
➔ Escrevente - Senhor(a) Escrevente
➔ Promotor - Senhor(a) Promotor(a)
➔ Advogado - Doutor(a)
➔ Analista - Senhor(a) Analista(a)
➔ Consultor - Senhor(a) Consultor(a)

**Secretaria Geral do Exército (SGEx)**
❖ **Alto Comando**
➔ Secretário(a)-Geral - Vossa Excelência
➔ Secretário Adjunto - senhor(a) Adjunto
➔ Secretário de Departamento - senhor(a) Secretário(a)
❖ **Administradores**
➔ Diretor - Diretor(a)
➔ Inspetor - Inspetor(a)
➔ Coordenador - Coordenador(a)
➔ Supervisor - Secretário(a)
❖ **Nível de Ingresso**
➔ Auxiliar-Superior - Auxiliar-Superior
➔ Analista - Analista
➔ Aprendiz - Aprendiz"""
    },
    "Cursos": {
        "titulo": "🏷️ Pronomes — Cursos",
        "texto": """**Escola de Sargentos das Armas (ESA)**
❖ **Alto Comando**
➔ Diretor-Geral - Senhor(a) Diretor(a)-Geral
➔ Diretor - Senhor(a) Diretor(a)
❖ **Alto Escalão**
➔ Instrutor-Chefe - Senhor(a) Instrutor-Chefe
➔ Adjunto de Diretoria - Senhor(a) Adjunto de Diretoria
❖ **Administração**
➔ Adjunto de Comando - Senhor(a) Adjunto de Comando
➔ Coordenador - Senhor(a) Coordenador
❖ **Coordenação**
➔ Supervisor ou Supervisor em Treinamento - Senhor(a) Supervisor(a)
❖ **Equipe de Instrução**
➔ Instrutor ou Instrutor em Treinamento - Senhor(a) Instrutor(a)
➔ Monitor - Senhor(a) Monitor(a)

**Curso de Formação e Aperfeiçoamento de Praças (CFAP)**
❖ **Diretoria**
➔ Diretor-Geral - Senhor(a) Diretor(a)-Geral
➔ Diretor - Senhor(a) Diretor(a)
➔ Diretor-Adjunto - Senhor(a) Adjunto(a)
❖ **Coordenação**
➔ Adjunto de Comando - Senhor(a) Adjunto de Comando
➔ Coordenador - Senhor(a) Coordenador(a)
➔ Supervisor ou Supervisor em Treinamento - Senhor(a) Supervisor(a)
❖ **Equipe de Instrução**
➔ Instrutor-Chefe - Senhor(a) Instrutor-Chefe
➔ Instrutor ou Instrutor em Treinamento - Senhor(a) Instrutor(a)
➔ Auxiliar - Auxiliar

**Escola de Reabilitação de Punitividades (ERP)**
❖ **Direção**
➔ Diretor - Senhor(a) Diretor(a)
➔ Vice-Diretor - Senhor(a) Diretor(a)
➔ Adjunto - Senhor(a) Adjunto(a)
❖ **Gerência**
➔ Gerente - Senhor(a) Gerente
➔ Contador - Contador(a)
❖ **Organização**
➔ Coordenador - Coordenador(a)
➔ Analista - Analista
❖ **Instrução**
➔ Promotor - Promotor(a)
➔ Procurador - Procurador(a)

**Curso de Liderança e Estratégia Avançada (CLEA)**
❖ **Diretoria**
➔ Diretor-Geral - Senhor(a) Diretor(a)-Geral
➔ Diretor Administrativo - Senhor(a) Diretor(a) Administrativo(a)
➔ Diretor Adjunto Gerencial - Senhor(a) Diretor(a) Adjunto Gerencial
❖ **Coordenação**
➔ Chefe Administrativo - Senhor(a) Chefe Administrativo(a)
➔ Coordenador Administrativo - Senhor(a) Coordenador(a) Administrativo(a)
➔ Supervisor Operacional - Senhor(a) Supervisor(a) Operacional
➔ Supervisor Estratégico - Senhor(a) Supervisor(a) Estratégico(a)
❖ **Equipe de Instrução**
➔ Instrutor Estratégico - Senhor(a) Instrutor(a) Estratégico(a)
➔ Instrutor Operacional - Senhor(a) Instrutor(a) Operacional
➔ Auxiliar Estratégico - Senhor(a) Auxiliar Estratégico(a)
➔ Auxiliar Operacional - Senhor(a) Auxiliar Operacional

**Centro de Instrução de Operações Urbanas (CIOU)**
❖ **Alto Comando**
➔ Diretor-Geral - Senhor(a) Diretor(a)-Geral
➔ Diretor - Senhor(a) Diretor(a)
❖ **Alto Escalão**
➔ Instrutor-Chefe - Senhor(a) Instrutor-Chefe
➔ Adjunto de Diretoria - Senhor(a) Adjunto de Diretoria
❖ **Coordenação**
➔ Supervisor ou Supervisor em Treinamento - Senhor(a) Supervisor(a)
❖ **Equipe de Instrução**
➔ Instrutor ou Instrutor em Treinamento - Senhor(a) Instrutor(a)
➔ Monitor - Senhor(a) Monitor(a)

**Escola Preparatória de Cadetes do Exército (EsPCEx)**
❖ **Direção**
➔ Diretor - Senhor(a) Diretor(a)
❖ **Equipe de Instrução**
➔ Instrutor - Senhor(a) Instrutor(a)
❖ **Formados**
➔ Patente do Oficial - Senhor(a) + Posto + Nome de Guerra
❖ **Aluno**
➔ Aluno - Cadete ou Aluno"""
    },
    "Setores": {
        "titulo": "🏷️ Pronomes — Setores",
        "texto": """**Setor de Comunicação Institucional (SCI)**
❖ **Gabinete Superior**
➔ Diretora do Jornal - Senhor(a) Diretor(a)
➔ Vice-Diretor - Senhor(a) Vice-Diretor(a)
❖ **Comando Editorial**
➔ Coordenador de Edições - Senhor(a) Coordenador(a)
➔ Editor-Chefe - Editor(a)-Chefe
❖ **Setor de Comunicação Institucional**
➔ Redator - Senhor(a) Redator(a)
➔ Jornalista - Jornalista
➔ Repórter - Repórter

**Investidores**
➔ Diretor de Eventos - Senhor(a) Diretor(a)
➔ Vice Diretor de Eventos - Senhor(a) Vice-Diretor(a)
➔ Coordenador de Eventos - Senhor(a) Coordenador(a)
➔ Gerente de Eventos - Senhor(a) Gerente
➔ Supervisor de Eventos - Senhor(a) Supervisor(a)
➔ Investidor - Investidor(a)
➔ Investidor em Treinamento - Investidor(a)"""
    }
}

# ==============================
# 🗂️ NORMAS E PROCEDIMENTOS
# ==============================
NORMAS_DADOS = {
    "Introdução": {
        "titulo": "🗂️ Normas e Procedimentos — Introdução",
        "texto": """A Secretaria-Geral do Exército (SGEx) é o órgão responsável pela análise, autorização e arquivamento de diversas solicitações administrativas realizadas pelos militares da instituição. Para assegurar organização, transparência e controle institucional, todas as solicitações descritas neste documento devem ser formalizadas exclusivamente por meio de tíquete no STM-SGEx. 

Link de convite: https://discord.com/invite/fsc24A6X5a"""
    },
    "Artigo 37 (Relacionamentos)": {
        "titulo": "🗂️ Normas — Artigo 37 (Relacionamentos)",
        "texto": """**O que é:**
O registro previsto no Artigo 37 consiste na formalização oficial de relacionamentos entre militares, a fim de garantir controle institucional, evitar conflitos de interesse e assegurar o cumprimento de restrições hierárquicas e funcionais.

**Política Atualizada:**
O Artigo 37 passa a focar exclusivamente na prevenção de conflitos de interesse e na manutenção da conduta profissional. Relacionamentos são permitidos dentro da instituição, desde que não interfiram nas atividades funcionais, não gerem favorecimento e não comprometam a disciplina. A antiga obrigatoriedade de comunicar relacionamentos à Secretária Geral do Exército e ao Alto Comando do Exército está revogada, adotando-se agora uma política menos invasiva e mais adequada ao respeito individual.

**Privacidade e Conduta:**
Apesar de permitido o vínculo afetivo, qualquer forma de demonstração de afeto (atitudes românticas ou similares) permanece estritamente proibida em todos os ambientes institucionais. A privacidade é preservada, desde que condutas pessoais não ultrapassem o âmbito privado nem afetem a imagem, a ordem e a neutralidade da instituição.

**Orientações Finais:**
Caso um relacionamento gere conflito funcional comprovado, a instituição poderá realizar realocação, restrição de atuação conjunta ou, em último caso, remoção de função, garantindo imparcialidade e disciplina."""
    },
    "Mudança de Nome (Roblox)": {
        "titulo": "🗂️ Normas — Mudança de Nome (Roblox)",
        "texto": """**O que é:**
A mudança de nome é destinada aos militares que desejam alterar seu nickname no Roblox por motivos diversos, tais como adequação institucional, correção de nomenclatura, evitar nomes impróprios ou alinhar sua identificação com padrões internos.

**Por que abrir tíquete / O processo envolve:**
- Verificação da disponibilidade de recursos (Robux);
- Avaliação dos motivos apresentados;
- Autorização do Alto Comando do Exército (ACE) ou do Governo Federal;
- Registro oficial da alteração para preservação da consistência documental.

**Como solicitar:**
O militar deve criar um tíquete informando seu motivo e o novo nome desejado. A SGEx analisará, solicitará autorização e, quando aprovado, registrará o arquivamento."""
    },
    "Troca de Conta (Discord)": {
        "titulo": "🗂️ Normas — Troca de Conta (Discord)",
        "texto": """**O que é:**
A troca de conta do Discord é destinada aos militares que necessitam migrar para outra conta por questões de segurança, perda de acesso ou ajustes pessoais.

**Por que abrir tíquete:**
A solicitação via tíquete assegura:
- Verificação da autenticidade das contas envolvidas;
- Análise do motivo da troca;
- Autorização institucional;
- Registro correto para evitar inconsistências em históricos, relatórios e documentos.

**Como solicitar:**
O solicitante deve abrir um tíquete, apresentar as informações da conta antiga e da nova, e aguardar a deliberação da SGEx e do ACE."""
    },
    "Troca de Conta (Roblox)": {
        "titulo": "🗂️ Normas — Troca de Conta (Roblox)",
        "texto": """**O que é:**
Este requerimento permite que o militar registre oficialmente a troca de sua conta Roblox utilizada na instituição.

**Por que abrir tíquete:**
A troca deve ser registrada formalmente porque:
- Patentes não são transferíveis automaticamente entre contas;
- Pode haver sanções, advertências ou relatórios vinculados à conta anterior;
- A nova conta não pode ser vinculada à instituição sem autorização prévia;
- É necessário arquivar todas as informações para manter a coerência administrativa.

**Como solicitar:**
O militar abre o tíquete informando a conta antiga, a nova e o motivo da troca. Após análise e autorização, o registro é realizado."""
    },
    "Afastamento Militar": {
        "titulo": "🗂️ Normas — Afastamento Militar",
        "texto": """**O que é:**
O afastamento consiste na licença temporária concedida a militares que necessitam de um período sem atividades por motivos pessoais, acadêmicos, profissionais ou imprevistos.

**Por que abrir tíquete:**
A solicitação deve ser formalizada porque:
- A licença precisa de análise e autorização;
- O afastamento suspende direitos e deveres durante o período;
- É necessário registrar a duração, justificativa e restrições;
- Tempo mínimo de 15 dias e tempo máximo de 60 dias;
- Somente é liberado mais de 61 dias ou superior, em que o STF, ACE ou GOV, aprovem;
- Garante transparência e controle do militar ativo/inativo.

**Como solicitar:**
O militar (Graduado ou Superior) deve abrir o tíquete informando motivo e duração. Após aprovação, o afastamento é arquivado e comunicado ao requerente."""
    },
    "Requerimento de Influenciador": {
        "titulo": "🗂️ Normas — Requerimento de Influenciador",
        "texto": """**O que é:**
O cargo de Influenciador é destinado a militares que produzem conteúdo em plataformas como YouTube ou Twitch e desejam representar oficialmente a instituição.

**Por que abrir tíquete:**
A análise via tíquete é obrigatória, pois o cargo exige:
- Verificação de requisitos (inscritos, tempo de instituição, conduta, ausência de conteúdo ofensivo, afins);
- Avaliação da regularidade e frequência de conteúdo;
- Aprovação do ACE ou do Governo Federal;
- Registro oficial para controle institucional.

**Como solicitar:**
O militar deve abrir um tíquete apresentando seu canal, frequência de vídeos e comprovações solicitadas. Após aprovação, o arquivamento é realizado e o documento de diretrizes é enviado ao solicitante."""
    },
    "Transparência e Disposições Finais": {
        "titulo": "🗂️ Normas — Transparência e Disposições Finais",
        "texto": """**TRANSPARÊNCIA DO PROCESSO DE ANÁLISE E DELIBERAÇÃO**
Todas as solicitações registradas via tíquete no STM-SGEx são submetidas a análise criteriosa realizada por:
- Secretaria-Geral do Exército;
- Secretário-Geral;
- Oficialato;
- Estado-Maior do Exército (EME);
- Alto Comando do Exército (ACE);
- Governo Federal.

Será solicitado somente quando necessário. A aprovação ou indeferimento sempre é comunicada de forma clara e transparente ao solicitante.

**DISPOSIÇÕES FINAIS**
- Os procedimentos descritos representam os meios formais e legais para solicitações administrativas dentro da instituição.
- Cada caso será avaliado individualmente, podendo haver exceções conforme a situação apresentada.
- Para esclarecimentos adicionais, dúvidas ou sugestões, o militar poderá contatar diretamente a Secretaria-Geral ou o responsável pela elaboração deste documento."""
    }
}


# ==============================
# 📚 TEXTOS INFORMATIVOS
# ==============================
TEXTO_PROCESSOS = """**➣ 1.1 - Processos Seletivos do Exército Brasileiro & Suas Designações**
-# Designações - Processos Seletivos:
> ⤷  **Cursos:** EsPCEx, ESA, ERP, CIOU e CFAP.
> ⤷  **Subdivisões:** STM e SGEx.
> ⤷  **Divisões:** BPE, BFE e BAC.
> ⤷  **Unidade:** CIE (contabiliza como divisão também).
> ⤷  **Especialização:** COpEsp.
> ⤷  **Setores:** Investidores e SCI.

-# Legislação vigente: cada militar poderá participar de apenas dois cursos e prestar no máximo quatro funções dentro da instituição: (divisão, subdivisão, curso e oficialato)"""

TEXTO_ADMINISTRADOR = """**Segue o link do que os administrador/moderadores fazem no EB Do Apex**
**[CLIQUE AQUI!](https://docs.google.com/document/d/1Od0rpORegpcvtwATTwaSYbvERpjib5pA4V_xyaDV5EE/edit?usp=sharing)**"""

TEXTO_VEDACAO = """> **➣ Segue o link da - Vedação de Acessos / Exilados Permanentes - IN GAME.**
>
> **[CLIQUE AQUI!](https://docs.google.com/document/d/13bpYEqPcT4EMISNtPQI4uodiA1frsBJ9u1r0TdXQNNY/edit?usp=sharing)**"""


def embed_info(titulo: str, descricao: str, cor: discord.Color = COR_SANGUE):
    """Cria um embed padrão com o rodapé fixo."""
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    return embed


# ==============================
# SISTEMA DE WARNINGS
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
# SISTEMA DE DROPDOWNS CUSTOMIZADOS
# ==============================
def carregar_dropdowns():
    if os.path.exists(ARQUIVO_DROPDOWNS):
        with open(ARQUIVO_DROPDOWNS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_dropdowns(dados):
    with open(ARQUIVO_DROPDOWNS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def gerar_id_dropdown():
    return f"dd_{int(datetime.datetime.utcnow().timestamp() * 1000)}"


# ==============================
# SISTEMA DE ENTRADA / SAÍDA
# ==============================
def carregar_entrada_saida():
    if os.path.exists(ARQUIVO_ENTRADA_SAIDA):
        with open(ARQUIVO_ENTRADA_SAIDA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_entrada_saida(dados):
    with open(ARQUIVO_ENTRADA_SAIDA, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


class CustomDropdown(discord.ui.Select):
    def __init__(self, custom_id: str, placeholder: str, opcoes: list):
        self.custom_id_ = custom_id
        options = []
        for op in opcoes:
            options.append(
                discord.SelectOption(
                    label=op["label"],
                    value=op["value"],
                    description=op.get("description") or None,
                    emoji=op.get("emoji") or None,
                )
            )
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):
        dados = carregar_dropdowns()
        config = dados.get(self.custom_id)
        if not config:
            await interaction.response.send_message(
                "❌ Este dropdown não está mais configurado.", ephemeral=True
            )
            return

        escolha = self.values[0]
        opcao = next((o for o in config["opcoes"] if o["value"] == escolha), None)
        if not opcao:
            await interaction.response.send_message(
                "❌ Opção inválida.", ephemeral=True
            )
            return

        cargos_ids = opcao.get("cargos", [])
        cargos_dados = []
        cargos_falha = []
        for cid in cargos_ids:
            role = interaction.guild.get_role(int(cid))
            if role:
                try:
                    await interaction.user.add_roles(role, reason="Dropdown de verificação")
                    cargos_dados.append(role.mention)
                except discord.Forbidden:
                    cargos_falha.append(role.name)
            else:
                cargos_falha.append(f"ID {cid}")

        cor = discord.Color(int(config.get("cor", 0xB40000)))

        embed = discord.Embed(
            title=f"✅ {opcao['label']}",
            description=(
                f"Você escolheu **{opcao['label']}**.\n\n"
                + (f"**Cargos recebidos:** {', '.join(cargos_dados)}" if cargos_dados else "")
                + (f"\n**Falha ao dar:** {', '.join(cargos_falha)}" if cargos_falha else "")
            ),
            color=cor,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CustomDropdownView(discord.ui.View):
    def __init__(self, custom_id: str = None, placeholder: str = None, opcoes: list = None):
        super().__init__(timeout=None)
        if custom_id and opcoes is not None:
            self.add_item(CustomDropdown(custom_id, placeholder, opcoes))


# ==============================
# CONFIGURAÇÃO DO BOT
# ==============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


# ==============================
# SETUP HOOK (registra views persistentes)
# ==============================
@bot.event
async def setup_hook():
    """Roda antes do bot conectar — registra as views persistentes."""
    bot.add_view(PercursoView())
    bot.add_view(RegulamentacaoView())
    bot.add_view(OrdemUnidaView())
    bot.add_view(RequisitosView())
    bot.add_view(ManualCaboView())
    bot.add_view(ManualRecrutaView())
    bot.add_view(HistoricoPresidencialView())
    bot.add_view(PronomesView())
    bot.add_view(NormasView()) # NOVA VIEW ADICIONADA AQUI

    dados = carregar_dropdowns()
    for cid, config in dados.items():
        try:
            view = discord.ui.View(timeout=None)
            view.add_item(CustomDropdown(cid, config["placeholder"], config["opcoes"]))
            bot.add_view(view)
            print(f"✅ Dropdown persistente registrado: {cid}")
        except Exception as e:
            print(f"❌ Erro ao registrar dropdown {cid}: {e}")


# ==============================
# EVENTOS
# ==============================
@bot.event
async def on_ready():
    print(f"🤖 Bot online como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="**VIDA LONGA ORDEM RUBRA!**"))
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash commands: {e}")


# ==============================
# 🎉 EVENTOS AUTOMÁTICOS DE ENTRADA / SAÍDA
# ==============================
@bot.event
async def on_member_join(member: discord.Member):
    dados = carregar_entrada_saida()
    guild_id = str(member.guild.id)
    config = dados.get(guild_id, {})
    canal_id = config.get("canal_entrada")

    if not canal_id:
        return

    canal = member.guild.get_channel(canal_id)
    if not canal:
        return

    embed = discord.Embed(
        title="🎉 Bem-vindo(a)!",
        description=f"Que bom te ver {member.mention}",
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=FOOTER)

    try:
        await canal.send(embed=embed)
    except discord.Forbidden:
        pass
    except Exception as e:
        print(f"❌ Erro ao enviar boas-vindas: {e}")


@bot.event
async def on_member_remove(member: discord.Member):
    dados = carregar_entrada_saida()
    guild_id = str(member.guild.id)
    config = dados.get(guild_id, {})
    canal_id = config.get("canal_saida")

    if not canal_id:
        return

    canal = member.guild.get_channel(canal_id)
    if not canal:
        return

    embed = discord.Embed(
        title="😡 Até nunca mais!",
        description=f"Vai mas não volta {member.mention} 😡",
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=FOOTER)

    try:
        await canal.send(embed=embed)
    except discord.Forbidden:
        pass
    except Exception as e:
        print(f"❌ Erro ao enviar despedida: {e}")


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
# 🏃 /percurso
# ==============================
class PercursoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🏁", description="Ver cargos e tempos")
            for nome in PERCURSOS.keys()
        ]
        super().__init__(
            placeholder="Escolha um percurso...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_percurso",
        )

    async def callback(self, interaction: discord.Interaction):
        percurso_escolhido = self.values[0]
        cargos = PERCURSOS[percurso_escolhido]

        embed = discord.Embed(
            title=f"🏁 {percurso_escolhido}",
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        for cargo, info in cargos.items():
            embed.add_field(
                name=f"▪️ {cargo}",
                value=f"⏱️ **Tempo:** {info['tempo']}\n🎯 **Nota mínima:** {info['nota']}",
                inline=False,
            )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PercursoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
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
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=PercursoView())


# ==============================
# ⚖️ /regulamentacao
# ==============================
class RegulamentacaoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="⚖️", description="Ver regulamentação e requisitos")
            for nome in REGULAMENTACAO_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma categoria...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_regulamentacao",
        )

    async def callback(self, interaction: discord.Interaction):
        escolha = self.values[0]
        info = REGULAMENTACAO_DADOS[escolha]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RegulamentacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RegulamentacaoSelect())


@bot.tree.command(name="regulamentacao", description="Consulta as regras de elegibilidade para Presidente e Vice")
async def regulamentacao(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚖️ Regulamentação de Elegibilidade",
        description=(
            "Escolha uma categoria no menu abaixo para ver os critérios e requisitos:\n\n"
            "**Opções disponíveis:**\n"
            + "\n".join(f"⚖️ {nome}" for nome in REGULAMENTACAO_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=RegulamentacaoView())


# ==============================
# 📋 /tarefas
# ==============================
@bot.tree.command(name="tarefas", description="Exibe o link das Tarefas, Funções e Explicações")
async def tarefas(interaction: discord.Interaction):
    embed = embed_info(
        "➣ 5.2 - Tarefas, Funções e Explicações",
        "Acesse o documento completo contendo as tarefas, funções e explicações de cada Divisão, Subdivisão, Instância e Grupo de Tarefa.\n\n"
        "🔗 **[CLIQUE AQUI PARA ABRIR O DOCUMENTO](https://docs.google.com/document/d/1mMtO0yBMCptw9jW4A7OucT737izGAL73A5oo3_jmf0I/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🎓 /cfap
# ==============================
@bot.tree.command(name="cfap", description="Exibe os links das aulas do CFAP")
async def cfap(interaction: discord.Interaction):
    embed = embed_info(
        "🎓 Aulas do CFAP",
        "Acesse o conteúdo da aula do CFAP abaixo:\n\n"
        "▪️ **CFAP Aula 1:**\n"
        "🔗 **[CLIQUE AQUI PARA ACESSAR](https://view.genially.com/6871cc992634eb8684507438/presentation-cfap-1degreeaula)**",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🪖 /ordem unida
# ==============================
class OrdemUnidaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🪖", description="Ler esta parte do manual")
            for nome in ORDEM_UNIDA.keys()
        ]
        super().__init__(
            placeholder="Escolha uma parte do manual...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_ordem_unida",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = ORDEM_UNIDA[parte]
        embed = discord.Embed(
            title=f"🪖 {parte}",
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class OrdemUnidaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
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
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=OrdemUnidaView())


bot.tree.add_command(ordem)


# ==============================
# 📊 /nota
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
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


# ==============================
# 📅 /cdp
# ==============================
@bot.tree.command(name="cdp", description="Mostra a capacitação de patente de cada patente")
async def cp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 Capacitação de Patente",
        description="Abaixo estará listada a capacitação de cada patente, sendo elas:",
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    for grupo, itens in CAPACITACAO.items():
        embed.add_field(
            name=f"| {grupo} |",
            value="\n".join(formatar_linha_cp(item) for item in itens),
            inline=False,
        )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


# ==============================
# 🪖 /hierarquia
# ==============================
@bot.tree.command(name="hierarquia", description="Mostra a hierarquia completa do Exército")
async def hierarquia(interaction: discord.Interaction):
    texto = montar_texto_hierarquia()
    blocos = []
    buffer = ""
    for linha in texto.split("\n"):
        if len(buffer) + len(linha) + 1 > 3800:
            blocos.append(buffer)
            buffer = linha
        else:
            buffer += ("\n" if buffer else "") + linha
    if buffer:
        blocos.append(buffer)

    embed = discord.Embed(
        title="🪖 Hierarquia do Exército",
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.add_field(name="Categorias", value=blocos[0] if blocos else "—", inline=False)
    embed.set_footer(text=FOOTER)

    if len(blocos) > 1:
        await interaction.response.send_message(embed=embed)
        for bloco in blocos[1:]:
            extra = discord.Embed(color=COR_SANGUE)
            extra.add_field(name="Continuação", value=bloco, inline=False)
            extra.set_footer(text=FOOTER)
            await interaction.followup.send(embed=extra)
    else:
        await interaction.response.send_message(embed=embed)


# ==============================
# 🗳️ /historico presidencial
# ==============================
historico = app_commands.Group(name="historico", description="Consultas do histórico do Exército")


class HistoricoPresidencialSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🗳️", description="Ler esta parte do histórico")
            for nome in HISTORICO_PRESIDENCIAL_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma opção...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_historico_presidencial",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = HISTORICO_PRESIDENCIAL_DADOS[parte]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class HistoricoPresidencialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HistoricoPresidencialSelect())


@historico.command(name="presidencial", description="Histórico de Presidentes e Vice-Presidentes eleitos")
async def historico_presidencial(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🗳️ Histórico Presidencial",
        description=(
            "Escolha uma opção no menu abaixo para ler o conteúdo completo.\n\n"
            "**Opções disponíveis:**\n"
            + "\n".join(f"🗳️ {nome}" for nome in HISTORICO_PRESIDENCIAL_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=HistoricoPresidencialView())


bot.tree.add_command(historico)


# ==============================
# 📑 /processos
# ==============================
@bot.tree.command(name="processos", description="Processos seletivos do Exército Brasileiro e suas designações")
async def processos(interaction: discord.Interaction):
    embed = embed_info(
        "📑 Processos Seletivos & Designações",
        "**➣ 1.1 - Processos Seletivos do Exército Brasileiro & Suas Designações**\n\n"
        "**Designações - Processos Seletivos:**\n"
        "> ⤷ **Cursos:** EsPCEx, ESA, ERP, CIOU e CFAP.\n"
        "> ⤷ **Subdivisões:** STM e SGEx.\n"
        "> ⤷ **Divisões:** BPE, BFE e BAC.\n"
        "> ⤷ **Unidade:** CIE (contabiliza como divisão também).\n"
        "> ⤷ **Especialização:** COpEsp.\n"
        "> ⤷ **Setores:** Investidores e SCI.\n\n"
        "**Legislação vigente:** cada militar poderá participar de apenas dois cursos e prestar no máximo quatro funções dentro da instituição (divisão, subdivisão, curso e oficialato).",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🏷️ /pronomes
# ==============================
class PronomesSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🏷️", description="Ler esta parte dos pronomes")
            for nome in PRONOMES_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma categoria de pronomes...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_pronomes",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = PRONOMES_DADOS[parte]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PronomesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PronomesSelect())


@bot.tree.command(name="pronomes", description="Consulta os pronomes vigentes do Exército por categoria")
async def pronomes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏷️ Pronomes Vigentes — EB do Apex",
        description=(
            "Escolha uma categoria no menu abaixo para ler o conteúdo completo.\n\n"
            "**Categorias disponíveis:**\n"
            + "\n".join(f"🏷️ {nome}" for nome in PRONOMES_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=PronomesView())


# ==============================
# 🗂️ /normas (ATUALIZADO)
# ==============================
class NormasSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🗂️", description="Ler esta parte das normas")
            for nome in NORMAS_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma categoria de normas...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_normas",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = NORMAS_DADOS[parte]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class NormasView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NormasSelect())


@bot.tree.command(name="normas", description="Consulta as Normas e Procedimentos de Arquivamentos Administrativos")
async def normas(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🗂️ Normas e Procedimentos",
        description=(
            "Escolha uma categoria no menu abaixo para ler o conteúdo completo.\n\n"
            "**Categorias disponíveis:**\n"
            + "\n".join(f"🗂️ {nome}" for nome in NORMAS_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=NormasView())


# ==============================
# 🛠️ /administrador
# ==============================
@bot.tree.command(name="administrador", description="O que os administradores/moderadores fazem no EB do Apex")
async def administrador(interaction: discord.Interaction):
    embed = embed_info(
        "🛠️ Administradores / Moderadores",
        "Segue o link do que os **administradores/moderadores** fazem no EB do Apex:\n\n"
        "🔗 **[CLIQUE AQUI!](https://docs.google.com/document/d/1Od0rpORegpcvtwATTwaSYbvERpjib5pA4V_xyaDV5EE/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🚫 /vedacao
# ==============================
@bot.tree.command(name="vedacao", description="Vedação de acessos e exilados permanentes (in game)")
async def vedacao(interaction: discord.Interaction):
    embed = embed_info(
        "🚫 Vedação de Acessos",
        "> ➣ Segue o link da **Vedação de Acessos / Exilados Permanentes - IN GAME**.\n\n"
        "🔗 **[CLIQUE AQUI!](https://docs.google.com/document/d/13bpYEqPcT4EMISNtPQI4uodiA1frsBJ9u1r0TdXQNNY/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 📘 /manual recruta e cabo
# ==============================
manual = app_commands.Group(name="manual", description="Manuais do Exército Brasileiro")


class ManualRecrutaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="📘", description="Ler esta parte do manual")
            for nome in MANUAL_RECRUTA_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma parte do Manual do Recruta...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_manual_recruta",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = MANUAL_RECRUTA_DADOS[parte]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ManualRecrutaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ManualRecrutaSelect())


@manual.command(name="recruta", description="Consulta o Manual do Recruta por partes")
async def manual_recruta(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 Manual do Recruta",
        description=(
            "Escolha uma parte no menu abaixo para ler o conteúdo completo.\n\n"
            "**Partes disponíveis:**\n"
            + "\n".join(f"📘 {nome}" for nome in MANUAL_RECRUTA_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=ManualRecrutaView())


class ManualCaboSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="📘", description="Ler esta parte do manual")
            for nome in MANUAL_CABO_DADOS.keys()
        ]
        super().__init__(
            placeholder="Escolha uma parte do Manual do Cabo...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_manual_cabo",
        )

    async def callback(self, interaction: discord.Interaction):
        parte = self.values[0]
        info = MANUAL_CABO_DADOS[parte]
        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ManualCaboView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ManualCaboSelect())


@manual.command(name="cabo", description="Consulta o Manual do Cabo por partes")
async def manual_cabo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 Manual do Cabo",
        description=(
            "Escolha uma parte no menu abaixo para ler o conteúdo completo.\n\n"
            "**Partes disponíveis:**\n"
            + "\n".join(f"📘 {nome}" for nome in MANUAL_CABO_DADOS.keys())
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=ManualCaboView())


bot.tree.add_command(manual)


# ==============================
# 📌 /requisitos
# ==============================
class RequisitosSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="📌", description="Ver patente e requisitos")
            for nome in REQUISITOS.keys()
        ]
        super().__init__(
            placeholder="Escolha um órgão...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_requisitos",
        )

    async def callback(self, interaction: discord.Interaction):
        orgao = self.values[0]
        info = REQUISITOS[orgao]
        embed = discord.Embed(
            title=f"📌 Requisitos — {orgao}",
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="🎖️ Patente necessária", value=info["patente"], inline=False)
        embed.add_field(name="✅ Requisitos", value=formatar_lista_req(info["requisitos"]), inline=False)
        for titulo, itens in info.get("extras", {}).items():
            embed.add_field(name=titulo, value=formatar_lista_req(itens), inline=False)
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RequisitosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
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
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, view=RequisitosView())


# ==============================
# ☀️ /lema
# ==============================
@bot.tree.command(name="lema", description="Mostra o lema da Ordem Rubra")
async def lema(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☀️ Lema da Ordem Rubra",
        description=f'*"{LEMA_TEXTO}"*\n\n**{LEMA_GRITO}**',
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


# ==============================
# 🚪 CONFIGURAÇÃO DE ENTRADA / SAÍDA
# ==============================
@bot.tree.command(name="entrar", description="Define o canal de boas-vindas automático")
@is_staff()
@app_commands.describe(canal="Canal que vai receber as mensagens de boas-vindas")
async def entrar(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_entrada_saida()
    guild_id = str(interaction.guild.id)

    dados.setdefault(guild_id, {})
    dados[guild_id]["canal_entrada"] = canal.id
    salvar_entrada_saida(dados)

    await interaction.response.send_message(
        f"✅ **Sucesso!** Canal de entrada definido como {canal.mention}.\n"
        f"_(esta mensagem será apagada em 30 segundos)_",
        ephemeral=True,
    )

    async def apagar_depois():
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    asyncio.create_task(apagar_depois())


@bot.tree.command(name="sair", description="Define o canal de despedida automático")
@is_staff()
@app_commands.describe(canal="Canal que vai receber as mensagens de saída")
async def sair(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_entrada_saida()
    guild_id = str(interaction.guild.id)

    dados.setdefault(guild_id, {})
    dados[guild_id]["canal_saida"] = canal.id
    salvar_entrada_saida(dados)

    await interaction.response.send_message(
        f"✅ **Sucesso!** Canal de saída definido como {canal.mention}.\n"
        f"_(esta mensagem será apagada em 30 segundos)_",
        ephemeral=True,
    )

    async def apagar_depois():
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    asyncio.create_task(apagar_depois())


# ==============================
# 🎛️ SISTEMA DE DROPDOWNS CUSTOMIZADOS (COMANDOS)
# ==============================
dropdown = app_commands.Group(name="dropdown", description="Gerenciar dropdowns customizados")


@dropdown.command(name="create", description="Cria um dropdown customizado com cargos")
@is_staff()
@app_commands.describe(
    titulo="Título do embed do dropdown",
    descricao="Descrição do embed",
    placeholder="Texto que aparece no dropdown antes de escolher",
    cor_hex="Cor em hexadecimal (ex: B40000)",
    canal="Canal onde o dropdown será enviado",
)
async def dropdown_create(
    interaction: discord.Interaction,
    titulo: str,
    descricao: str,
    placeholder: str,
    cor_hex: str,
    canal: discord.TextChannel,
):
    try:
        cor_int = int(cor_hex.replace("#", ""), 16)
    except ValueError:
        await interaction.response.send_message(
            "❌ Cor inválida. Use hexadecimal, ex: `B40000`.", ephemeral=True
        )
        return

    cid = gerar_id_dropdown()

    dados = carregar_dropdowns()
    dados[cid] = {
        "titulo": titulo,
        "descricao": descricao,
        "placeholder": placeholder,
        "cor": cor_int,
        "canal_id": canal.id,
        "opcoes": [],
    }
    salvar_dropdowns(dados)

    embed = discord.Embed(
        title="🎛️ Dropdown criado",
        description=(
            f"**ID:** `{cid}`\n"
            f"**Título:** {titulo}\n"
            f"**Canal:** {canal.mention}\n"
            f"**Cor:** `#{cor_hex.replace('#', '').upper()}`\n\n"
            f"Agora use `/dropdown edit` com este ID para adicionar as opções (label + cargos)."
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@dropdown.command(name="edit", description="Edita um dropdown existente (cor, título, opções)")
@is_staff()
@app_commands.describe(
    id_dropdown="ID do dropdown (veja em /dropdown list)",
    titulo="Novo título (deixe vazio para manter)",
    descricao="Nova descrição (deixe vazio para manter)",
    cor_hex="Nova cor em hexadecimal (deixe vazio para manter)",
    opcoes="Formato: Label|cargo_id1,cargo_id2;Label2|cargo_id3",
)
async def dropdown_edit(
    interaction: discord.Interaction,
    id_dropdown: str,
    titulo: str = None,
    descricao: str = None,
    cor_hex: str = None,
    opcoes: str = None,
):
    dados = carregar_dropdowns()
    if id_dropdown not in dados:
        await interaction.response.send_message(
            f"❌ Nenhum dropdown com ID `{id_dropdown}`.", ephemeral=True
        )
        return

    config = dados[id_dropdown]

    if titulo:
        config["titulo"] = titulo
    if descricao:
        config["descricao"] = descricao
    if cor_hex:
        try:
            config["cor"] = int(cor_hex.replace("#", ""), 16)
        except ValueError:
            await interaction.response.send_message("❌ Cor inválida.", ephemeral=True)
            return

    if opcoes:
        novas = []
        try:
            for bloco in opcoes.split(";"):
                bloco = bloco.strip()
                if not bloco:
                    continue
                label, cargos_str = bloco.split("|")
                cargos = [c.strip() for c in cargos_str.split(",") if c.strip()]
                novas.append({
                    "label": label.strip(),
                    "value": label.strip().lower().replace(" ", "_"),
                    "cargos": cargos,
                })
            config["opcoes"] = novas
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Formato de opções inválido: {e}\n"
                f"Use: `Label|cargo_id1,cargo_id2;Label2|cargo_id3`",
                ephemeral=True,
            )
            return

    salvar_dropdowns(dados)

    embed = discord.Embed(
        title="✅ Dropdown atualizado",
        description=(
            f"**ID:** `{id_dropdown}`\n"
            f"**Título:** {config['titulo']}\n"
            f"**Opções:** {len(config['opcoes'])}"
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@dropdown.command(name="send", description="Envia o dropdown no canal configurado")
@is_staff()
@app_commands.describe(id_dropdown="ID do dropdown")
async def dropdown_send(interaction: discord.Interaction, id_dropdown: str):
    dados = carregar_dropdowns()
    if id_dropdown not in dados:
        await interaction.response.send_message(
            f"❌ Nenhum dropdown com ID `{id_dropdown}`.", ephemeral=True
        )
        return

    config = dados[id_dropdown]
    if not config["opcoes"]:
        await interaction.response.send_message(
            "❌ Esse dropdown não tem opções ainda. Use `/dropdown edit`.", ephemeral=True
        )
        return

    canal = interaction.guild.get_channel(config["canal_id"])
    if not canal:
        await interaction.response.send_message("❌ Canal não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(
        title=config["titulo"],
        description=config["descricao"],
        color=discord.Color(int(config["cor"])),
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)

    view = discord.ui.View(timeout=None)
    view.add_item(CustomDropdown(id_dropdown, config["placeholder"], config["opcoes"]))

    await canal.send(embed=embed, view=view)
    await interaction.response.send_message(
        f"✅ Dropdown enviado em {canal.mention}.", ephemeral=True
    )


@dropdown.command(name="list", description="Lista todos os dropdowns criados")
@is_staff()
async def dropdown_list(interaction: discord.Interaction):
    dados = carregar_dropdowns()
    if not dados:
        await interaction.response.send_message("📭 Nenhum dropdown criado ainda.", ephemeral=True)
        return

    linhas = []
    for cid, cfg in dados.items():
        canal = interaction.guild.get_channel(cfg["canal_id"])
        linhas.append(
            f"**`{cid}`** — {cfg['titulo']} "
            f"(#{canal.name if canal else '?'}) — {len(cfg['opcoes'])} opções"
        )

    embed = discord.Embed(
        title="🎛️ Dropdowns criados",
        description="\n".join(linhas),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@dropdown.command(name="delete", description="Deleta um dropdown")
@is_staff()
@app_commands.describe(id_dropdown="ID do dropdown")
async def dropdown_delete(interaction: discord.Interaction, id_dropdown: str):
    dados = carregar_dropdowns()
    if id_dropdown not in dados:
        await interaction.response.send_message("❌ ID não encontrado.", ephemeral=True)
        return
    del dados[id_dropdown]
    salvar_dropdowns(dados)
    await interaction.response.send_message(
        f"🗑️ Dropdown `{id_dropdown}` removido do banco.", ephemeral=True
    )


bot.tree.add_command(dropdown)


# ==============================
# 🛡️ MODERAÇÃO
# ==============================
@bot.tree.command(name="ban", description="Bane um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser banido", motivo="Motivo do banimento")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ Não posso banir este membro (cargo maior ou igual ao meu).")
        return
    try:
        await membro.ban(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🔴 Banimento Executado",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao banir: {e}")


@bot.tree.command(name="kick", description="Expulsa um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser expulso", motivo="Motivo da expulsão")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ Não posso expulsar este membro.")
        return
    try:
        await membro.kick(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🟠 Expulsão Executada",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao expulsar: {e}")


@bot.tree.command(name="mute", description="Silencia um membro temporariamente (timeout)")
@is_staff()
@app_commands.describe(membro="Membro a ser silenciado", duracao="Duração (ex: 10m, 1h, 1d)", motivo="Motivo")
async def mute(interaction: discord.Interaction, membro: discord.Member, duracao: str, motivo: str = "Não especificado"):
    padrao = re.compile(r"(\d+)([smhd])")
    matches = list(padrao.finditer(duracao.lower()))
    if not matches:
        await interaction.response.send_message("❌ Formato inválido. Use: `10m`, `1h`, `2d`.")
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
        await interaction.response.send_message("❌ Duração máxima: 28 dias.")
        return

    try:
        await membro.timeout(total, reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="🟡 Membro Silenciado",
            description=(f"**Membro:** {membro.mention}\n"
                         f"**Duração:** {duracao}\n"
                         f"**Motivo:** {motivo}\n"
                         f"**Moderador:** {interaction.user.mention}"),
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao silenciar: {e}")


@bot.tree.command(name="unmute", description="Remove o silenciamento de um membro")
@is_staff()
@app_commands.describe(membro="Membro a ser dessilenciado")
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    try:
        await membro.timeout(None, reason=f"Unmute por {interaction.user}")
        embed = discord.Embed(
            title="🔊 Membro Dessilenciado",
            description=f"**Membro:** {membro.mention}\n**Moderador:** {interaction.user.mention}",
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {e}")


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
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("❌ Usuário não encontrado ou não está banido.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {e}")


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
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)
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
        await interaction.response.send_message(f"✅ {membro.mention} não tem advertências.")
        return

    embed = discord.Embed(
        title=f"⚠️ Advertências de {membro.display_name}",
        color=COR_SANGUE,
    )
    for i, w in enumerate(lista, 1):
        embed.add_field(
            name=f"#{i} — {w['data'][:10]}",
            value=f"**Motivo:** {w['motivo']}\n**Por:** {w['moderador']}",
            inline=False,
        )
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


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
        await interaction.response.send_message(f"✅ {membro.mention} já não tinha advertências.")


# ==============================
# 🧹 SISTEMA DE LIMPEZA DE MENSAGENS
# ==============================
@bot.tree.command(name="clear", description="Apaga uma quantidade específica de mensagens do canal")
@is_staff()
@app_commands.describe(quantidade="Quantidade de mensagens a apagar (1-100)")
async def clear(interaction: discord.Interaction, quantidade: int):
    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message("❌ Use um valor entre **1** e **100**.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        deletadas = await interaction.channel.purge(limit=quantidade)
        embed = discord.Embed(
            title="🧹 Limpeza Executada",
            description=(
                f"**Canal:** {interaction.channel.mention}\n"
                f"**Mensagens apagadas:** {len(deletadas)}\n"
                f"**Moderador:** {interaction.user.mention}"
            ),
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Não tenho permissão para apagar mensagens neste canal.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao limpar: {e}", ephemeral=True)


@bot.tree.command(name="clearuser", description="Apaga mensagens de um usuário específico no canal")
@is_staff()
@app_commands.describe(membro="Membro cujas mensagens serão apagadas", quantidade="Quantidade (1-100)")
async def clearuser(interaction: discord.Interaction, membro: discord.Member, quantidade: int = 100):
    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message("❌ Use um valor entre **1** e **100**.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        def check(msg):
            return msg.author.id == membro.id
        deletadas = await interaction.channel.purge(limit=quantidade, check=check)
        embed = discord.Embed(
            title="🧹 Limpeza por Usuário",
            description=(
                f"**Canal:** {interaction.channel.mention}\n"
                f"**Usuário:** {membro.mention}\n"
                f"**Mensagens apagadas:** {len(deletadas)}\n"
                f"**Moderador:** {interaction.user.mention}"
            ),
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Não tenho permissão para apagar mensagens neste canal.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao limpar: {e}", ephemeral=True)


@bot.tree.command(name="clearbot", description="Apaga mensagens de bots no canal")
@is_staff()
@app_commands.describe(quantidade="Quantidade (1-100)")
async def clearbot(interaction: discord.Interaction, quantidade: int = 100):
    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message("❌ Use um valor entre **1** e **100**.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        def check(msg):
            return msg.author.bot
        deletadas = await interaction.channel.purge(limit=quantidade, check=check)
        embed = discord.Embed(
            title="🧹 Limpeza de Bots",
            description=(
                f"**Canal:** {interaction.channel.mention}\n"
                f"**Mensagens apagadas:** {len(deletadas)}\n"
                f"**Moderador:** {interaction.user.mention}"
            ),
            color=COR_SANGUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Não tenho permissão para apagar mensagens neste canal.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao limpar: {e}", ephemeral=True)


# ==============================
# 💥 SISTEMA DE DUPE (CLONAR CANAL)
# ==============================
class DupeConfirmView(discord.ui.View):
    def __init__(self, autor_id: int, canal_original: discord.TextChannel):
        super().__init__(timeout=60)
        self.autor_id = autor_id
        self.canal_original = canal_original

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message(
                "❌ Apenas quem executou o comando pode confirmar.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="💥 Confirmar Dupe", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="💥 **Dupe autorizado.** Clonando canal e apagando o antigo...",
            view=self,
        )

        canal_antigo = self.canal_original
        try:
            canal_novo = await canal_antigo.clone(
                reason=f"Dupe executado por {interaction.user} ({interaction.user.id})"
            )
            await canal_novo.edit(position=canal_antigo.position)
            await canal_antigo.delete(
                reason=f"Dupe executado por {interaction.user} ({interaction.user.id})"
            )

            embed = discord.Embed(
                title="💥 Canal Duplicado",
                description=(
                    f"Este canal foi **recriado** para limpar todas as mensagens antigas.\n\n"
                    f"**Executor:** {interaction.user.mention}\n"
                    f"**Canal original:** `#{canal_antigo.name}`"
                ),
                color=COR_SANGUE,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(text=FOOTER)
            await canal_novo.send(embed=embed)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Não tenho permissão para **Gerenciar Canais** neste servidor.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao executar dupe: {e}", ephemeral=True)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="❌ **Dupe cancelado.**",
            view=self,
        )


@bot.tree.command(name="dupe", description="Clona o canal e apaga o antigo (limpa TODAS as mensagens, até antigas)")
@is_staff()
async def dupe(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message(
            "❌ Este comando só funciona em canais de texto.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="💥 Confirmação de Dupe",
        description=(
            f"Você está prestes a **clonar** {interaction.channel.mention} e **apagar o canal original**.\n\n"
            "⚠️ **Isso vai remover TODAS as mensagens**, inclusive as com mais de 14 dias.\n"
            "⚠️ **Permissões, tópico, posição e categoria serão mantidos** no canal novo.\n\n"
            "Tem certeza?"
        ),
        color=COR_SANGUE,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER)

    view = DupeConfirmView(interaction.user.id, interaction.channel)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# 🐢 CANAL / TRAVA
# ==============================
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


# ==============================
# 🔎 UTILITÁRIOS
# ==============================
@bot.tree.command(name="userinfo", description="Mostra informações de um usuário")
@app_commands.describe(membro="Membro para consultar (opcional)")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"👤 {membro}", color=COR_SANGUE)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id, inline=True)
    embed.add_field(name="Apelido", value=membro.nick or "Nenhum", inline=True)
    embed.add_field(name="Bot?", value="Sim" if membro.bot else "Não", inline=True)
    embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrou em", value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "?", inline=True)
    embed.add_field(name="Cargo mais alto", value=membro.top_role.mention, inline=True)
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Mostra informações do servidor")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"🏰 {g.name}", color=COR_SANGUE)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="ID", value=g.id, inline=True)
    embed.add_field(name="Dono", value=g.owner.mention, inline=True)
    embed.add_field(name="Membros", value=g.member_count, inline=True)
    embed.add_field(name="Canais", value=len(g.channels), inline=True)
    embed.add_field(name="Cargos", value=len(g.roles), inline=True)
    embed.add_field(name="Criado em", value=g.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Mostra o avatar de um usuário")
@app_commands.describe(membro="Membro (opcional)")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar de {membro.display_name}", color=COR_SANGUE)
    embed.set_image(url=membro.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await interaction.response.send_message(embed=embed)


# ==============================
# ERROS
# ==============================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        try:
            await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message(f"❌ Erro: {error}", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(f"❌ Erro: {error}", ephemeral=True)


# ==============================
# INICIALIZAÇÃO
# ==============================
bot.run(DISCORD_TOKEN)
