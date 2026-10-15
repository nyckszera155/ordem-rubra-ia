import os
import re
import json
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ==============================
# CARREGAMENTO DE VARIÃVEIS
# ==============================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))

# Arquivo de warnings
ARQUIVO_WARN = "warnings.json"


# ==============================
# ðŸ“‹ DADOS DOS PERCURSOS (fonte Ãºnica de verdade)
# ==============================
PERCURSOS = {
    "1Âº Percurso â€” Balamentos": {
        "PraÃ§as": {"tempo": "45 segundos", "nota": "â€”"},
        "Graduados": {"tempo": "40 segundos", "nota": "â€”"},
    },
    "2Âº Percurso â€” Torre": {
        "Recruta": {"tempo": "25 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "20 segundos", "nota": "5,5 pontos"},
        "Terceiro-Sargento": {"tempo": "16 segundos", "nota": "6,0 pontos"},
        "Segundo-Sargento": {"tempo": "14 segundos", "nota": "6,5 pontos"},
        "Primeiro-Sargento": {"tempo": "12 segundos", "nota": "6,5 pontos"},
    },
    "3Âº Percurso â€” Torre 2.0": {
        "Recruta": {"tempo": "30 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "25 segundos", "nota": "5,5 pontos"},
        "Terceiro-Sargento": {"tempo": "18 segundos", "nota": "6,0 pontos"},
        "Segundo-Sargento": {"tempo": "16 segundos", "nota": "6,5 pontos"},
        "Primeiro-Sargento": {"tempo": "14 segundos", "nota": "6,5 pontos"},
    },
    "4Âº Percurso": {
        "Recruta": {"tempo": "35 segundos", "nota": "5,0 pontos"},
        "Soldado": {"tempo": "30 segundos", "nota": "5,5 pontos"},
    },
    "Percurso de Graduados": {
        "Graduados": {"tempo": "45 segundos", "nota": "â€”"},
    },
}

# Tabela de notas de aprovaÃ§Ã£o (geral, independente do percurso)
NOTAS_APROVACAO = {
    "Recruta": "5,0 pontos",
    "Soldado": "5,5 pontos",
    "Terceiro-Sargento": "6,0 pontos",
    "Segundo-Sargento": "6,5 pontos",
    "Primeiro-Sargento": "6,5 pontos",
}


# ==============================
# ðŸ“… DADOS DA CAPACITAÃ‡ÃƒO DE PATENTE (fonte Ãºnica de verdade)
# ==============================
CAPACITACAO = {
    "Graduados ã€ŒðŸŽ“ã€": [
        {"cargo": "Subtenente", "dias": "6 dias", "detalhe": "22 relatÃ³rios de recrutamentos registrados"},
        {"cargo": "Primeiro-Sargento", "dias": "5 dias", "detalhe": "18 relatÃ³rios de recrutamentos registrados"},
        {"cargo": "Segundo-Sargento", "dias": "4 dias", "detalhe": "15 relatÃ³rios de recrutamentos registrados"},
        {"cargo": "Terceiro-Sargento", "dias": "3 dias", "detalhe": "8 relatÃ³rios de recrutamentos registrados"},
    ],
    "PraÃ§as ã€ŒðŸ‡§ðŸ‡·ã€": [
        {"cargo": "Cabo", "dias": "2 dias", "detalhe": "5 relatÃ³rios de recrutamentos registrados + ESA"},
        {"cargo": "Soldado", "dias": "1 dia", "detalhe": ""},
        {"cargo": "Recruta", "dias": "N/A", "detalhe": ""},
    ],
}


def formatar_linha_cp(item):
    """Monta a linha de um cargo da capacitaÃ§Ã£o (ex: 'Cabo = 2 dias (5 relatÃ³rios...)')."""
    texto = f"â–ªï¸ **{item['cargo']}** = {item['dias']}"
    if item["detalhe"]:
        texto += f" ({item['detalhe']})"
    return texto


# ==============================
# ðŸª– HIERARQUIA DO EXÃ‰RCITO (fonte Ãºnica de verdade)
# ==============================
HIERARQUIA = {
    "[GOV] Governo Federalã€ŒðŸ”°ã€": [
        "[Pres] Presidente",
        "[V-Pres] Vice-Presidente",
    ],
    "[ACE] Alto Comando do ExÃ©rcitoã€ŒðŸ’«ã€": [
        "[Cmt] Comandante",
        "[SCmt] Subcomandante",
    ],
    "[OFGE] Oficiais Generaisã€Œâœ¨ã€": [
        "[Gen Ex] General-de-ExÃ©rcito",
        "[Gen Div] General-de-DivisÃ£o",
        "[Gen Bda] General-de-Brigada",
    ],
    "[OFSP] Oficiais Superioresã€Œâš”ï¸ã€": [
        "[Cel] Coronel",
        "[TenCel] Tenente-Coronel",
        "[Maj] Major",
    ],
    "[OFIT] Oficiais IntermediÃ¡riosã€ŒðŸ›¡ï¸ã€": [
        "[Cap] CapitÃ£o",
    ],
    "[OFSB] Oficiais Subalternosã€ŒðŸ—¡ï¸ã€": [
        "[1Âº Ten] Primeiro-Tenente",
        "[2Âº Ten] Segundo-Tenente",
        "[Asp] Aspirante-a-Oficial",
    ],
    "[GD] Graduadosã€ŒðŸŽ“ã€": [
        "[ST] Subtenente",
        "[1Âº Sgt] Primeiro-Sargento",
        "[2Âº Sgt] Segundo-Sargento",
        "[3Âº Sgt] Terceiro-Sargento",
    ],
    "[PR] PraÃ§asã€ŒðŸ‡§ðŸ‡·ã€": [
        "[Cb] Cabo",
        "[Sd] Soldado",
        "[Rcr] Recruta",
    ],
}


# ==============================
# ðŸ“Œ DADOS DOS REQUISITOS DOS Ã“RGÃƒOS (fonte Ãºnica de verdade)
# ==============================
REQUISITOS = {
    "BFEr": {
        "patente": "Rubro 1",
        "requisitos": [
            "Ser Ã³timo em PVP (combate)",
            "Responsabilidade",
            "GramÃ¡tica",
            "Disponibilidade",
            "Ter lideranÃ§a e estratÃ©gia nas raids",
        ],
        "extras": {
            "âš ï¸ ObservaÃ§Ã£o": [
                "NecessÃ¡rio ter comprovaÃ§Ã£o de terrorismo (vÃ­deo raidando) para avaliar se o candidato estÃ¡ apto para adentrar ao BFEr.",
            ],
        },
    },
    "CIR": {
        "patente": "Rubro 1",
        "requisitos": [
            "Ter no mÃ­nimo 1 semana (7 dias) de carreira na OR e ter relevÃ¢ncia na organizaÃ§Ã£o",
            "Possuir pelo menos 01 (um) exÃ­lio permanente no EB",
            "Manter boa postura e comportamento",
            "Saber lidar com situaÃ§Ãµes de pressÃ£o psicolÃ³gica",
            "Respeitar superiores, regras e a hierarquia",
            "Demonstrar disciplina e responsabilidade",
        ],
        "extras": {
            "ðŸ“ Conduta durante o formulÃ¡rio": [
                "Todas as respostas deverÃ£o ser feitas com suas prÃ³prias palavras",
                "PlÃ¡gio e uso de IA serÃ£o facilmente detectados",
                "O uso de IA ou cÃ³pia de respostas poderÃ¡ resultar em Black List",
                "Mantenha postura e respeito durante todo o processo",
                "O descumprimento das regras poderÃ¡ resultar na anulaÃ§Ã£o do formulÃ¡rio",
            ],
        },
    },
    "ACR": {
        "patente": "Candidato a Rubro ou superior",
        "requisitos": [
            "Ser Ãºtil, visando ampliar a atuaÃ§Ã£o da ACR",
            "Manter organizaÃ§Ã£o, postura e conduta adequada",
            "Demonstrar disponibilidade no dia a dia",
            "Conta do Discord com, no mÃ­nimo, trÃªs meses completos de criaÃ§Ã£o (caso esse requisito esteja faltando, a candidatura serÃ¡ retirada na hora)",
        ],
        "extras": {
            "âš ï¸ ObservaÃ§Ãµes": [
                "FaÃ§a o formulÃ¡rio com atenÃ§Ã£o e deixe todas as respostas claras",
                "Fale o que sabe sobre os Ã“rgÃ£os do EB do Apex em suas perguntas correspondentes",
                "Caso nÃ£o tenha disponibilidade, nem faÃ§a o formulÃ¡rio",
                "Em nenhum momento Ã© permitido falar sobre o formulÃ¡rio ou vazÃ¡-lo: quem fizer isso entrarÃ¡ na Black List da ACR e serÃ¡ expulso da Ordem Rubra",
            ],
        },
    },
}


def formatar_lista_req(itens):
    """Transforma uma lista de itens em linhas com marcador."""
    return "\n".join(f"â–ªï¸ {item}" for item in itens)


# ==============================
# â˜€ï¸ LEMA DA ORDEM RUBRA
# ==============================
LEMA_TEXTO = (
    "A cada alvorada, eis que o Sol se ergue, majestoso e tingido de carmesim, "
    "proclamando a sentenÃ§a inexorÃ¡vel contra os corruptos e os agressores. "
    "Pois de sua luz emana o juÃ­zo, e sob seu fulgor, nenhuma injustiÃ§a permanecerÃ¡ impune."
)
LEMA_GRITO = "VIDA LONGA ORDEM RUBRA!"


# ==============================
# âš–ï¸ DADOS DE REGULAMENTAÃ‡ÃƒO (ELEGIBILIDADE)
# ==============================
REGULAMENTACAO_DADOS = {
    "Geral e IntroduÃ§Ã£o": {
        "titulo": "âš–ï¸ RegulamentaÃ§Ã£o â€” Diretrizes Gerais",
        "texto": """O Tribunal Superior Eleitoral, na sua atribuiÃ§Ã£o de estabelecer as condiÃ§Ãµes de elegibilidade para os cargos de Presidente e Vice-Presidente da RepÃºblica, regula essas prerrogativas atravÃ©s da meticulosa observÃ¢ncia e aderÃªncia aos requisitos consignados na legislaÃ§Ã£o eleitoral vigente. Esses critÃ©rios, por sua vez, constituem uma compilaÃ§Ã£o de exigÃªncias cuidadosamente delineadas para assegurar a indispensÃ¡vel aptidÃ£o dos postulantes aos mais elevados cargos executivos do ExÃ©rcito Brasileiro.

Ressalta-se que mesmo no caso de revogaÃ§Ã£o de relatÃ³rios referentes a exÃ­lios, puniÃ§Ãµes ou rebaixamentos, isso nÃ£o exime os postulantes do escrutÃ­nio do histÃ³rico eleitoral. A anÃ¡lise e avaliaÃ§Ã£o desses aspectos continuam pautadas na integridade e idoneidade dos candidatos, essenciais para desempenhar funÃ§Ãµes de destaque no cenÃ¡rio polÃ­tico militar do ExÃ©rcito Brasileiro."""
    },
    "Presidente": {
        "titulo": "ðŸŽ–ï¸ Requisitos â€” Presidente",
        "texto": """Nesse contexto, Ã© imprescindÃ­vel destacar que, para se candidatar Ã  presidÃªncia, o postulante deve:
â–ªï¸ Possuir a graduaÃ§Ã£o de **Subtenente**.
â–ªï¸ MÃ­nimo de **dois meses** de efetivo exercÃ­cio no posto.
â–ªï¸ Apresentar uma ficha funcional desprovida de quaisquer antecedentes vinculados a rebaixamentos, exÃ­lios ou puniÃ§Ãµes no Ã¢mbito do BatalhÃ£o de PolÃ­cia do ExÃ©rcito.
â–ªï¸ Possuir **ficha limpa**.
â–ªï¸ Demonstrar disponibilidade para demonstrar sua voz e participar ativamente dos debates presidenciais.
â–ªï¸ Tempo mÃ­nimo de **oito meses** desde o seu primeiro recrutamento no ExÃ©rcito Brasileiro."""
    },
    "Vice-Presidente": {
        "titulo": "ðŸŽ–ï¸ Requisitos â€” Vice-Presidente",
        "texto": """Para o cargo de Vice-Presidente, as exigÃªncias estabelecem que o postulante deve:
â–ªï¸ Possuir, no mÃ­nimo, a patente de **Cabo**.
â–ªï¸ Apresentar uma ficha funcional limpa e isenta de qualquer histÃ³rico de rebaixamentos, exÃ­lios ou puniÃ§Ãµes.
â–ªï¸ Demonstrar disponibilidade para utilizar a voz e participar ativamente dos debates presidenciais.
â–ªï¸ Possuir tempo mÃ­nimo de **quatro meses** desde o seu primeiro recrutamento no ExÃ©rcito Brasileiro."""
    }
}


# ==============================
# ðŸª– DADOS DA ORDEM UNIDA (FONTE ÃšNICA DE VERDADE)
# ==============================
ORDEM_UNIDA = {
    "IntroduÃ§Ã£o": {
        "titulo": "Manual de Ordem Unida",
        "texto": """O objetivo deste documento Ã© instruir, orientar e padronizar a execuÃ§Ã£o da ordem unida, assegurando disciplina, coesÃ£o, postura militar e correta aplicaÃ§Ã£o dos movimentos e comandos conforme as normas estabelecidas pela instituiÃ§Ã£o.""",
    },
    "Parte 1 â€” Objetivo da Ordem Unida": {
        "titulo": "Parte 1 â€” Objetivo da Ordem Unida",
        "texto": """**FUNDAMENTOS, COMANDOS E APLICAÃ‡Ã•ES**
A Ordem Unida Ã© um dos fundamentos essenciais da formaÃ§Ã£o militar, tendo como finalidade padronizar a apresentaÃ§Ã£o, o deslocamento e a organizaÃ§Ã£o dos militares em conjunto. Por meio de seus comandos e movimentos, busca-se desenvolver disciplina, obediÃªncia imediata, coordenaÃ§Ã£o coletiva, atenÃ§Ã£o, postura e reflexos condicionados, atributos indispensÃ¡veis para qualquer militar. 
A correta execuÃ§Ã£o da Ordem Unida garante que o grupamento se apresente e se desloque de maneira organizada, harmÃ´nica e eficiente, respeitando a hierarquia e a padronizaÃ§Ã£o institucional.

O QUE Ã‰ ORDEM UNIDA - RESUMIDA
A Ordem Unida Ã© o conjunto de normas, comandos e movimentos utilizados para:
Padronizar a apresentaÃ§Ã£o do militar e do grupamento;
Organizar o deslocamento coletivo;
Garantir disciplina, hierarquia e harmonia nos movimentos.

Seu emprego desenvolve:
ObediÃªncia imediata Ã s ordens;
CoordenaÃ§Ã£o coletiva;
AtenÃ§Ã£o, postura e autocontrole;
EspÃ­rito de corpo e disciplina militar.

Ã‰ aplicada em instruÃ§Ãµes, apresentaÃ§Ãµes, deslocamentos formais e situaÃ§Ãµes administrativas dentro da instituiÃ§Ã£o.

Principal Objetivo da Ordem Unida
A Ordem Unida tem como principais objetivos permitir que o grupamento se apresente e se desloque em perfeita ordem, desenvolver a disciplina coletiva, estimular a obediÃªncia aos comandos, aprimorar a coordenaÃ§Ã£o e fortalecer o espÃ­rito de corpo. Esses fatores sÃ£o determinantes para o bom desempenho do militar em qualquer atividade dentro da instituiÃ§Ã£o.

OBJETIVOS DA ORDEM UNIDA - RESUMIDA
Permitir que o grupamento:
Apresente-se de forma organizada e padronizada;
Desloque-se com ordem, sincronia e disciplina.

Desenvolver no militar:
Reflexos condicionados;
Respeito Ã  hierarquia;
Capacidade de agir coletivamente;
ProntidÃ£o para cumprir ordens.""",
    },
    "Parte 2 â€” Tipos de Comandos": {
        "titulo": "Parte 2 â€” Tipos de Comandos",
        "texto": """Os comandos utilizados na Ordem Unida dividem-se em vozes de comando e comandos propriamente ditos.
A voz de comando Ã© utilizada para preparar o grupamento, alertando-o de que uma aÃ§Ã£o serÃ¡ executada. Dentro dela, destaca-se a voz de advertÃªncia, que serve exclusivamente como alerta inicial, nÃ£o possuindo carÃ¡ter de execuÃ§Ã£o. Exemplos incluem â€œGrupamentoâ€, â€œPelotÃ£oâ€ e â€œEsquadrÃ£oâ€. Essa voz deve ser empregada apenas uma vez, pois sua funÃ§Ã£o Ã© somente chamar a atenÃ§Ã£o do grupamento.
O meio comando Ã© aquele que antecede uma aÃ§Ã£o, preparando o grupamento para o movimento que serÃ¡ executado. Ele Ã© aplicÃ¡vel, principalmente, a comandos de marcha e de volver, pois nesses casos hÃ¡ movimentaÃ§Ã£o. Nos comandos de volver, o meio comando indica a direÃ§Ã£o do giro; nos comandos de marcha, indica o tipo e, quando necessÃ¡rio, a direÃ§Ã£o do deslocamento.
Os comandos propriamente ditos sÃ£o responsÃ¡veis por iniciar ou finalizar um movimento. Alguns sÃ£o antecedidos por meio comando, enquanto outros sÃ£o executados de forma direta. Exemplos incluem â€œSentidoâ€, â€œDescansarâ€, â€œAtenÃ§Ã£oâ€ e â€œMarcheâ€.

TIPOS DE COMANDOS - RESUMIDO
Vozes de Comando
Utilizadas para:
Alertar;
Preparar o grupamento para uma aÃ§Ã£o.

NÃ£o possuem execuÃ§Ã£o direta de movimento.
Voz de AdvertÃªncia
Finalidade:
Alertar o grupamento de que comandos serÃ£o emitidos.

CaracterÃ­sticas:
Deve ser dita apenas uma vez;
NÃ£o inicia movimento.

Exemplos:
â€œGRUPAMENTO!â€
â€œPELOTÃƒO!â€
â€œESQUADRÃƒO!â€

Meio Comando
Finalidade:
Preparar o grupamento para a aÃ§Ã£o que serÃ¡ executada.

AplicaÃ§Ã£o:
Apenas em comandos que envolvem movimentaÃ§Ã£o.

FunÃ§Ã£o:
Em marchas: indica o tipo e a direÃ§Ã£o;
Em volvers: indica a direÃ§Ã£o do giro.

Exemplos:
APRESENTAR, ARMA!
DESCANSAR, ARMA!
ESQUERDA VOLVER!
DIREITA VOLVER!

Comandos Propriamente Ditos
Finalidade:
Iniciar ou encerrar a execuÃ§Ã£o do movimento.
Podem ser:
Antecedidos por meio comando;
Executados de forma direta.

Exemplos:
SENTIDO!
DESCANSAR!
ATENÃ‡ÃƒO!
MARCHE!""",
    },
    "Parte 3 â€” Comandos de Postura": {
        "titulo": "Parte 3 â€” Comandos de Postura",
        "texto": """COMANDOS BÃSICOS DE POSTURA
O comando â€œAtenÃ§Ã£oâ€ tem a finalidade de alertar o grupamento para o inÃ­cio das ordens do instrutor ou xerife. O comando â€œSentidoâ€ determina que o grupamento permaneÃ§a imÃ³vel, com postura ereta e mÃ£os vazias, aguardando o prÃ³ximo comando. O comando â€œDescansarâ€ autoriza o grupamento a assumir a posiÃ§Ã£o de descanso, sendo vÃ¡lido apenas quando o grupamento estiver anteriormente em posiÃ§Ã£o de sentido. O comando â€œÃ€ vontadeâ€ concede maior liberdade de movimento, desde que o militar permaneÃ§a no local e mantenha postura adequada.
Os comandos â€œApresentar, armaâ€ e â€œDescansar, armaâ€ sÃ£o utilizados, respectivamente, para iniciar e finalizar a continÃªncia do grupamento, incluindo o instrutor ou xerife.

COMANDOS BÃSICOS DE POSTURA - RESUMIDO
ATENÃ‡ÃƒO!
Finalidade:
Alertar o grupamento para o inÃ­cio das ordens do instrutor.

ObservaÃ§Ã£o:
Prepara para o comando seguinte.

SENTIDO!
Finalidade:
Colocar o grupamento em postura rÃ­gida e imÃ³vel.

CaracterÃ­sticas:
MÃ£os vazias;
Olhar Ã  frente.

DESCANSAR!
Finalidade:
Permitir postura menos rÃ­gida.

ObservaÃ§Ã£o:
SÃ³ pode ser dado se o grupamento estiver em sentido.

Ã€ VONTADE!
Finalidade:
Conceder maior liberdade de movimento.

LimitaÃ§Ãµes:
NÃ£o sair do lugar;
Manter postura adequada.""",
    },
    "Parte 4 â€” Comandos de Marcha": {
        "titulo": "Parte 4 â€” Comandos de Marcha",
        "texto": """Existem trÃªs tipos principais de marcha aplicÃ¡veis no Ã¢mbito do jogo: ordinÃ¡rio, acelerado e sem cadÃªncia.
A marcha ordinÃ¡ria Ã© a mais formal e a mais utilizada. Nela, o grupamento deve seguir o instrutor ou xerife sem correr, mantendo rigorosamente a organizaÃ§Ã£o da fila e a sincronia coletiva. 
A marcha acelerada caracteriza-se pelo deslocamento correndo, devendo o grupamento, ainda assim, tentar manter a organizaÃ§Ã£o da fila. 
A marcha sem cadÃªncia Ã© considerada informal, permitindo que o grupamento siga o instrutor sem necessidade de manter alinhamento rigoroso, sendo proibido correr.
Para preparar corretamente o grupamento para marchar, os comandos devem seguir uma sequÃªncia padronizada. Para a marcha ordinÃ¡ria, o instrutor deve comandar, de frente para o grupamento: â€œGrupamento, atenÃ§Ã£oâ€ e â€œGrupamento, sentidoâ€. Em seguida, deve virar-se de costas para o grupamento e informar o destino com â€œEm direÃ§Ã£o ao (local)â€, indicar o tipo de marcha com â€œOrdinÃ¡rioâ€ e iniciar o deslocamento com â€œMarcheâ€. Ao tÃ©rmino da marcha, jÃ¡ de frente para o grupamento, deve finalizar com â€œGrupamento, faz altoâ€.
O mesmo procedimento Ã© aplicado Ã  marcha acelerada, substituindo-se apenas o tipo de marcha pelo comando â€œAceleradoâ€, e Ã  marcha sem cadÃªncia, utilizando-se o comando â€œSem cadÃªnciaâ€. Em todos os casos, o comando â€œGrupamento, faz altoâ€ Ã© obrigatÃ³rio para encerrar a marcha, devendo o grupamento permanecer em posiÃ§Ã£o de sentido apÃ³s a parada.

Tipos de Marcha
ORDINÃRIO
Marcha formal;
Sem correr;
Fila organizada;
Total sincronia com o instrutor.
ACELERADO
Marcha rÃ¡pida;
Grupamento corre;
OrganizaÃ§Ã£o da fila deve ser mantida.

SEM CADÃŠNCIA
Marcha informal;
NÃ£o exige alinhamento rÃ­gido;
Ã‰ proibido correr.

SEQUÃŠNCIA PADRÃƒO PARA MARCHAR
Marcha OrdinÃ¡ria
De frente:
GRUPAMENTO, ATENÃ‡ÃƒO!
GRUPAMENTO, SENTIDO!

De costas:
EM DIREÃ‡ÃƒO AO (LOCAL)!
ORDINÃRIO!
MARCHE!

De frente (finalizaÃ§Ã£o):
GRUPAMENTO, FAZ ALTO!

Marcha Acelerada
Mesma sequÃªncia, substituindo:
ORDINÃRIO! por ACELERADO!

Marcha Sem CadÃªncia
Mesma sequÃªncia, substituindo:
ORDINÃRIO! por SEM CADÃŠNCIA!""",
    },
    "Parte 5 â€” AlteraÃ§Ã£o de Dispositivo": {
        "titulo": "Parte 5 â€” AlteraÃ§Ã£o de Dispositivo",
        "texto": """O comando â€œFora de formaâ€ Ã© exclusivo para alteraÃ§Ãµes de dispositivo e jamais deve ser utilizado para deslocamento. Ele indica que o grupamento mudarÃ¡ sua organizaÃ§Ã£o, como de formaÃ§Ã£o para coluna ou de coluna para formaÃ§Ã£o.
A coluna por um Ã© uma forma de organizaÃ§Ã£o na qual os militares ficam posicionados um atrÃ¡s do outro, respeitando a distÃ¢ncia de uma pessoa entre si. Existem outras variaÃ§Ãµes, como coluna por dois, trÃªs ou quatro, nas quais se deve observar rigorosamente a obediÃªncia Ã s fileiras e Ã s linhas.
Para formar uma coluna por um, o instrutor deve permanecer de frente para o grupamento e comandar: â€œGrupamento, atenÃ§Ã£oâ€, â€œGrupamento, sentidoâ€ e, em seguida, explicar a aÃ§Ã£o com â€œDevem formar uma coluna por um em minha retaguardaâ€. ApÃ³s isso, utiliza-se o comando â€œFora de formaâ€ e, logo depois, â€œMarcheâ€. ApÃ³s o comando â€œMarcheâ€, o instrutor deve deslocar-se atÃ© o local desejado para que o grupamento se organize corretamente em coluna. Ao concluir a alteraÃ§Ã£o de dispositivo, o grupamento assume posiÃ§Ã£o de descanso, nÃ£o sendo utilizado o comando â€œGrupamento, faz altoâ€, pois nÃ£o se trata de uma marcha.
A formaÃ§Ã£o, por sua vez, ocorre quando o grupamento se organiza em linha, ombro a ombro. Fileira Ã© a disposiÃ§Ã£o dos militares lado a lado, voltados para a mesma frente. Linha caracteriza-se por possuir maior frente do que profundidade, ou seja, mais militares lado a lado do que em profundidade.
Para entrar em formaÃ§Ã£o, o instrutor deve comandar, de frente para o grupamento: â€œGrupamento, atenÃ§Ã£oâ€, â€œGrupamento, sentidoâ€ e, em seguida, explicar a aÃ§Ã£o com â€œDevem ir atÃ© a formaÃ§Ã£o ao meu lado e formar um ombro a ombro ao meu comandoâ€. ApÃ³s isso, utiliza-se o comando â€œFora de formaâ€ e, posteriormente, â€œMarcheâ€. Assim que o grupamento concluir a formaÃ§Ã£o, deve assumir posiÃ§Ã£o de descanso, sem o uso do comando â€œGrupamento, faz altoâ€.

ALTERAÃ‡ÃƒO DE DISPOSITIVO
FORA DE FORMA
Finalidade:
Alterar o formato do grupamento.

ProibiÃ§Ãµes:
Nunca usar para deslocamento.

Exemplos de alteraÃ§Ã£o:
FormaÃ§Ã£o para coluna;
Coluna para formaÃ§Ã£o.
COLUNA
Conceito
Coluna por um:
Militares posicionados um atrÃ¡s do outro;
DistÃ¢ncia de uma pessoa entre cada militar.

Existem:
Coluna por dois, trÃªs, quatro, etc.

Comandos para Formar Coluna
De frente:
GRUPAMENTO, ATENÃ‡ÃƒO!
GRUPAMENTO, SENTIDO!
DEVEM FORMAR UMA COLUNA POR UM EM MINHA RETAGUARDA!
FORA DE FORMA!
MARCHE!
ObservaÃ§Ã£o:
ApÃ³s â€œMARCHE!â€, o instrutor deve ir ao local desejado;
NÃ£o utilize â€œGRUPAMENTO, FAZ ALTOâ€.
FORMAÃ‡ÃƒO
Conceitos Fundamentais
Fileira:
Militares lado a lado, mesma linha e mesma frente.

Linha:
FormaÃ§Ã£o com frente maior que a profundidade.

Comandos para Formar
De frente:
GRUPAMENTO, ATENÃ‡ÃƒO!
GRUPAMENTO, SENTIDO!
DEVEM IR ATÃ‰ A FORMACÃƒO AO MEU LADO E FORMAR UM OMBRO A OMBRO AO MEU COMANDO!
FORA DE FORMA!
MARCHE!

ObservaÃ§Ã£o:
ApÃ³s a formaÃ§Ã£o, o grupamento entra em descanso;
NÃ£o usar â€œFAZ ALTOâ€.""",
    },
    "Parte 6 â€” Comandos de ApresentaÃ§Ã£o": {
        "titulo": "Parte 6 â€” Comandos de ApresentaÃ§Ã£o",
        "texto": """A apresentaÃ§Ã£o Ã© um ato formal que demonstra disciplina, organizaÃ§Ã£o e respeito Ã  hierarquia. O militar responsÃ¡vel deve apresentar-se informando seu posto ou graduaÃ§Ã£o seguido do nome de guerra. Para apresentar o grupamento a um superior, o grupamento deve estar previamente organizado e em posiÃ§Ã£o de sentido.
O xerife ou instrutor posiciona-se Ã  frente do grupamento, comanda â€œGrupamento, atenÃ§Ã£oâ€ e â€œGrupamento, sentidoâ€, vira-se para o superior, presta continÃªncia e se apresenta. Em seguida, informa se o grupamento estÃ¡ com ou sem faltas e com ou sem alteraÃ§Ãµes. ApÃ³s o superior declarar que o grupamento estÃ¡ apresentado, o xerife retorna-se ao grupamento, comanda â€œGrupamento, descansarâ€ e reassume sua posiÃ§Ã£o.
Considera-se falta a ausÃªncia de um integrante que nÃ£o compareceu Ã  instruÃ§Ã£o. Considera-se alteraÃ§Ã£o quando algum integrante se retira antes do tÃ©rmino da atividade. A inexistÃªncia de faltas e alteraÃ§Ãµes indica que todos os integrantes participaram integralmente da instruÃ§Ã£o.

APRESENTAÃ‡ÃƒO DO GRUPAMENTO
Finalidade:
Demonstrar disciplina e organizaÃ§Ã£o.

Procedimento:
Grupamento em sentido;
Xerife Ã  frente;
ContinÃªncia obrigatÃ³ria do xerife;
Informar:
Com ou sem faltas;
Com ou sem alteraÃ§Ãµes.

DefiniÃ§Ãµes:
Falta: ausÃªncia no inÃ­cio da instruÃ§Ã£o;
AlteraÃ§Ã£o: saÃ­da antes do tÃ©rmino.

SequÃªncia de Comandos
PreparaÃ§Ã£o do Grupamento
De frente para o grupamento, o xerife comanda:
GRUPAMENTO, ATENÃ‡ÃƒO!
GRUPAMENTO, SENTIDO!

ApresentaÃ§Ã£o ao Superior
O xerife:
Vira-se em direÃ§Ã£o ao superior;
Presta continÃªncia obrigatoriamente;
Realiza a apresentaÃ§Ã£o verbal, dizendo:
(POSTO/GRADUAÃ‡ÃƒO DO XERIFE) (NOME DE GUERRA), XERIFE DO CURSO!
Exemplo: SUBTENENTE AT, XERIFE DO CURSO!
Em seguida, ainda em continÃªncia, informa:
APRESENTO GRUPAMENTO PRONTO, COM/SEM FALTAS E COM/SEM ALTERAÃ‡Ã•ES!

Em seguida o superior deverÃ¡ responder algo semelhante Ã :
ESTÃ APRESENTADO.

FinalizaÃ§Ã£o da ApresentaÃ§Ã£o
ApÃ³s a resposta do superior, o xerife:
Cessa a continÃªncia;
Vira-se novamente para o grupamento;
Comanda:
GRUPAMENTO, DESCANSAR!

Retorno Ã  PosiÃ§Ã£o
O xerife:
Retorna ao seu local;
Assume posiÃ§Ã£o de descanso junto ao grupamento.""",
    },
    "Parte 7 â€” ObservaÃ§Ãµes Gerais": {
        "titulo": "Parte 7 â€” ObservaÃ§Ãµes Gerais",
        "texto": """OBSERVAÃ‡Ã•ES GERAIS
Todos os comandos devem ser executados com o militar em posiÃ§Ã£o de sentido, salvo quando o comando determinar outra postura.
A execuÃ§Ã£o de comandos fora da posiÃ§Ã£o correta caracteriza erro de procedimento.
O comando â€œGRUPAMENTO, FAZ ALTOâ€ deve ser utilizado exclusivamente para finalizar as marchas.
O comando â€œFAZ ALTOâ€ nunca deve ser empregado em alteraÃ§Ãµes de dispositivo, como formaÃ§Ã£o ou coluna.
O comando â€œFORA DE FORMAâ€ Ã© restrito Ã  mudanÃ§a do formato do grupamento, nÃ£o devendo ser utilizado para deslocamento.
Durante marchas, o grupamento deve manter atenÃ§Ã£o constante ao instrutor/xerife.
Em marchas ordinÃ¡rias, a sincronia e a organizaÃ§Ã£o da fila sÃ£o obrigatÃ³rias.
Em marchas aceleradas, apesar do deslocamento em corrida, deve-se manter o mÃ¡ximo de organizaÃ§Ã£o possÃ­vel.
Na marcha sem cadÃªncia, nÃ£o Ã© permitido correr.
Durante a apresentaÃ§Ã£o do grupamento, a continÃªncia do xerife ou instrutor Ã© obrigatÃ³ria.
O superior apresentado nÃ£o Ã© obrigado a prestar continÃªncia.
O grupamento deve permanecer imÃ³vel e em silÃªncio durante apresentaÃ§Ãµes e comunicaÃ§Ãµes formais.
Todos os comandos devem ser emitidos de forma:
Clara;
Firme;
AudÃ­vel a todo o grupamento.

Ã‰ responsabilidade do instrutor/xerife garantir que o grupamento compreenda o comando antes da execuÃ§Ã£o.""",
    },
    "Parte 8 â€” Perguntas Frequentes (FAQ)": {
        "titulo": "Parte 8 â€” Perguntas Frequentes (FAQ)",
        "texto": """1. O que Ã© Ordem Unida?
 Ã‰ o conjunto de comandos e movimentos que padroniza a apresentaÃ§Ã£o, o deslocamento e a organizaÃ§Ã£o do grupamento, promovendo disciplina e coesÃ£o.
2. Qual Ã© o principal objetivo da Ordem Unida?
 Desenvolver disciplina, obediÃªncia, coordenaÃ§Ã£o coletiva e postura militar.
3. Quem pode comandar a Ordem Unida?
 Militares designados como instrutores, xerifes ou responsÃ¡veis pelo grupamento.
4. O que Ã© voz de advertÃªncia?
 Ã‰ o comando usado apenas para alertar o grupamento de que uma ordem serÃ¡ executada.
5. A voz de advertÃªncia pode ser repetida?
 NÃ£o. Essa voz deve ser dita apenas uma vez.
6. O que Ã© meio comando?
 Ã‰ o comando que prepara o grupamento para uma movimentaÃ§Ã£o especÃ­fica.
7. Todo comando possui meio comando?
 NÃ£o. Apenas comandos que envolvem movimento, como marchas e volvers.
8. O que significa â€œSentidoâ€?
 Indica postura rÃ­gida, imÃ³vel e atenta, aguardando o prÃ³ximo comando.
9. Quando posso usar o comando â€œDescansarâ€?
 Somente quando o grupamento estiver em posiÃ§Ã£o de sentido.
10. Qual a diferenÃ§a entre â€œDescansarâ€ e â€œÃ€ vontadeâ€?
 â€œDescansarâ€ mantÃ©m postura controlada; â€œÃ€ vontadeâ€ permite mais liberdade sem sair do lugar.
11. Quais sÃ£o os tipos de marcha?
 OrdinÃ¡rio, Acelerado e Sem CadÃªncia.
12. Qual Ã© a marcha mais formal?
 A marcha OrdinÃ¡ria.
13. Em qual marcha Ã© permitido correr?
 Apenas na marcha Acelerada.
14. O que Ã© â€œSem cadÃªnciaâ€?
 Uma marcha informal, sem necessidade de alinhamento rigoroso e sem correr.
15. Quando devo usar â€œGrupamento, faz altoâ€?
 Exclusivamente para finalizar uma marcha.
16. Posso usar â€œFaz altoâ€ em formaÃ§Ã£o ou coluna?
 NÃ£o. Ele Ã© proibido em alteraÃ§Ãµes de dispositivo.
17. O que Ã© â€œFora de formaâ€?
 Comando utilizado para alterar o formato do grupamento.
18. â€œFora de formaâ€ serve para marchar?
 NÃ£o. Serve apenas para mudanÃ§a de dispositivo.
19. O que Ã© coluna por um?
 FormaÃ§Ã£o em que os militares ficam um atrÃ¡s do outro, respeitando a distÃ¢ncia.
20. O que Ã© formaÃ§Ã£o em linha?
 Quando os militares ficam lado a lado, com a frente maior que a profundidade.
21. O que Ã© fileira?
 DisposiÃ§Ã£o dos militares lado a lado, voltados para a mesma frente.
22. Quem deve prestar continÃªncia na apresentaÃ§Ã£o?
 O xerife ou instrutor Ã© obrigado; o superior nÃ£o.
23. O que sÃ£o faltas na apresentaÃ§Ã£o?
 AusÃªncia de integrante no inÃ­cio da instruÃ§Ã£o.
24. O que sÃ£o alteraÃ§Ãµes na apresentaÃ§Ã£o?
 SaÃ­da de integrante antes do tÃ©rmino da instruÃ§Ã£o.
25. O grupamento deve se mover durante a apresentaÃ§Ã£o?
 NÃ£o. Deve permanecer imÃ³vel em posiÃ§Ã£o de sentido.""",
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
# CONFIGURAÃ‡ÃƒO DO BOT
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
    print(f"ðŸ¤– Bot online como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="vigilÃ¢ncia rubra ðŸ”´"))
    try:
        synced = await bot.tree.sync()
        print(f"âœ… {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"âŒ Erro ao sincronizar slash commands: {e}")


# ==============================
# VERIFICAÃ‡ÃƒO DE STAFF
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
# ðŸƒ COMANDO /percurso (SISTEMA DE DROPDOWNS)
# ==============================
class PercursoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="ðŸ", description="Ver cargos e tempos")
            for nome in PERCURSOS.keys()
        ]
        super().__init__(placeholder="Escolha um percurso...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        percurso_escolhido = self.values[0]
        cargos = PERCURSOS[percurso_escolhido]

        embed = discord.Embed(
            title=f"ðŸ {percurso_escolhido}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )

        for cargo, info in cargos.items():
            embed.add_field(
                name=f"â–ªï¸ {cargo}",
                value=f"â±ï¸ **Tempo:** {info['tempo']}\nðŸŽ¯ **Nota mÃ­nima:** {info['nota']}",
                inline=False
            )

        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PercursoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(PercursoSelect())


@bot.tree.command(name="percurso", description="Consulta tempos e notas mÃ­nimas dos percursos")
async def percurso(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸ“‹ Tabela de Percursos",
        description=(
            "Escolha um percurso no menu abaixo para ver os tempos e notas mÃ­nimas.\n\n"
            "**Percursos disponÃ­veis:**\n"
            + "\n".join(f"ðŸ {nome}" for nome in PERCURSOS.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = PercursoView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# âš–ï¸ COMANDO /regulamentacao
# ==============================
class RegulamentacaoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="âš–ï¸", description="Ver regulamentaÃ§Ã£o e requisitos")
            for nome in REGULAMENTACAO_DADOS.keys()
        ]
        super().__init__(placeholder="Escolha uma categoria...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        escolha = self.values[0]
        info = REGULAMENTACAO_DADOS[escolha]

        embed = discord.Embed(
            title=info["titulo"],
            description=info["texto"],
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RegulamentacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RegulamentacaoSelect())


@bot.tree.command(name="regulamentacao", description="Consulta as regras de elegibilidade para Presidente e Vice")
async def regulamentacao(interaction: discord.Interaction):
    embed = discord.Embed(
        title="âš–ï¸ RegulamentaÃ§Ã£o de Elegibilidade",
        description=(
            "Escolha uma categoria no menu abaixo para ver os critÃ©rios e requisitos:\n\n"
            "**OpÃ§Ãµes disponÃ­veis:**\n"
            + "\n".join(f"âš–ï¸ {nome}" for nome in REGULAMENTACAO_DADOS.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = RegulamentacaoView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# ðŸ“‹ COMANDO /tarefas
# ==============================
@bot.tree.command(name="tarefas", description="Exibe o link das Tarefas, FunÃ§Ãµes e ExplicaÃ§Ãµes")
async def tarefas(interaction: discord.Interaction):
    embed = discord.Embed(
        title="âž£ 5.2 - Tarefas, FunÃ§Ãµes e ExplicaÃ§Ãµes",
        description=(
            "Acesse o documento completo contendo as tarefas, funÃ§Ãµes e explicaÃ§Ãµes de cada DivisÃ£o, SubdivisÃ£o, InstÃ¢ncia e Grupo de Tarefa.\n\n"
            "ðŸ”— **[CLIQUE AQUI PARA ABRIR O DOCUMENTO](https://docs.google.com/document/d/1mMtO0yBMCptw9jW4A7OucT737izGAL73A5oo3_jmf0I/edit?usp=sharing)**"
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# ðŸŽ“ COMANDO /cfap
# ==============================
@bot.tree.command(name="cfap", description="Exibe os links das aulas do CFAP")
async def cfap(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸŽ“ Aulas do CFAP",
        description=(
            "Acesse o conteÃºdo da aula do CFAP abaixo:\n\n"
            "â–ªï¸ **CFAP Aula 1:**\n"
            "ðŸ”— **[CLIQUE AQUI PARA ACESSAR](https://view.genially.com/6871cc992634eb8684507438/presentation-cfap-1degreeaula)**"
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# ðŸª– COMANDO /ordem unida
# ==============================
class OrdemUnidaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="ðŸª–", description="Ler esta parte do manual")
            for nome in ORDEM_UNIDA.keys()
        ]
        super().__init__(placeholder="Escolha uma parte do manual...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        parte_escolhida = self.values[0]
        info = ORDEM_UNIDA[parte_escolhida]

        embed = discord.Embed(
            title=f"ðŸª– {parte_escolhida}",
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
        title="ðŸª– Manual de Ordem Unida",
        description=(
            "Escolha uma parte no menu abaixo para ler o conteÃºdo completo.\n\n"
            "**Partes disponÃ­veis:**\n"
            + "\n".join(f"ðŸª– {nome}" for nome in ORDEM_UNIDA.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = OrdemUnidaView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


bot.tree.add_command(ordem)


# ==============================
# ðŸ“Š COMANDO /nota
# ==============================
@bot.tree.command(name="nota", description="Mostra a nota mÃ­nima de aprovaÃ§Ã£o de um cargo")
@app_commands.describe(cargo="Cargo para consultar a nota mÃ­nima")
@app_commands.choices(cargo=[
    app_commands.Choice(name="Recruta", value="Recruta"),
    app_commands.Choice(name="Soldado", value="Soldado"),
    app_commands.Choice(name="Terceiro-Sargento", value="Terceiro-Sargento"),
    app_commands.Choice(name="Segundo-Sargento", value="Segundo-Sargento"),
    app_commands.Choice(name="Primeiro-Sargento", value="Primeiro-Sargento"),
])
async def nota(interaction: discord.Interaction, cargo: app_commands.Choice[str]):
    valor = NOTAS_APROVACAO.get(cargo.value, "â€”")
    embed = discord.Embed(
        title=f"ðŸŽ¯ Nota mÃ­nima â€” {cargo.value}",
        description=f"**{cargo.value}** precisa de **{valor}** para aprovaÃ§Ã£o.",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# ðŸ“… COMANDO /cp (CAPACITAÃ‡ÃƒO DE PATENTE)
# ==============================
@bot.tree.command(name="cp", description="Mostra a capacitaÃ§Ã£o de patente de cada patente")
async def cp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸ“… CapacitaÃ§Ã£o de Patente",
        description="Abaixo estarÃ¡ listada a capacitaÃ§Ã£o de cada patente, sendo elas:",
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
# ðŸª– COMANDO /hierarquia
# ==============================
@bot.tree.command(name="hierarquia", description="Mostra a hierarquia completa do ExÃ©rcito")
async def hierarquia(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸª– Hierarquia do ExÃ©rcito",
        description="Estrutura hierÃ¡rquica completa da Ordem Rubra:",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )

    for grupo, cargos in HIERARQUIA.items():
        valor = "\n".join(f"â–ªï¸ {cargo}" for cargo in cargos)
        embed.add_field(
            name=f"**{grupo}**",
            value=valor,
            inline=False
        )

    embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================
# ðŸ“Œ COMANDO /requisitos
# ==============================
class RequisitosSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="ðŸ“Œ", description="Ver patente e requisitos")
            for nome in REQUISITOS.keys()
        ]
        super().__init__(placeholder="Escolha um Ã³rgÃ£o...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        orgao = self.values[0]
        info = REQUISITOS[orgao]

        embed = discord.Embed(
            title=f"ðŸ“Œ Requisitos â€” {orgao}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="ðŸŽ–ï¸ Patente necessÃ¡ria", value=info["patente"], inline=False)
        embed.add_field(name="âœ… Requisitos", value=formatar_lista_req(info["requisitos"]), inline=False)

        for titulo, itens in info.get("extras", {}).items():
            embed.add_field(name=titulo, value=formatar_lista_req(itens), inline=False)

        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RequisitosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RequisitosSelect())


@bot.tree.command(name="requisitos", description="Consulta a patente e os requisitos de cada Ã³rgÃ£o")
async def requisitos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸ“Œ Requisitos dos Ã“rgÃ£os",
        description=(
            "Escolha um Ã³rgÃ£o no menu abaixo para ver a patente necessÃ¡ria e os requisitos.\n\n"
            "**Ã“rgÃ£os disponÃ­veis:**\n"
            + "\n".join(f"ðŸ“Œ {nome}" for nome in REQUISITOS.keys())
        ),
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="O menu fica ativo por 3 minutos.")

    view = RequisitosView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==============================
# â˜€ï¸ COMANDO /lema
# ==============================
@bot.tree.command(name="lema", description="Mostra o lema da Ordem Rubra")
async def lema(interaction: discord.Interaction):
    embed = discord.Embed(
        title="â˜€ï¸ Lema da Ordem Rubra",
        description=f'*"{LEMA_TEXTO}"*\n\n**{LEMA_GRITO}**',
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# ðŸ›¡ï¸ COMANDOS DE MODERAÃ‡ÃƒO
# ==============================
@bot.tree.command(name="ban", description="Bane um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser banido", motivo="Motivo do banimento")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "NÃ£o especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("âŒ NÃ£o posso banir este membro (cargo maior ou igual ao meu).", ephemeral=True)
        return
    try:
        await membro.ban(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="ðŸ”´ Banimento Executado",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"âŒ Erro ao banir: {e}", ephemeral=True)


@bot.tree.command(name="kick", description="Expulsa um membro do servidor")
@is_staff()
@app_commands.describe(membro="Membro a ser expulso", motivo="Motivo da expulsÃ£o")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "NÃ£o especificado"):
    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("âŒ NÃ£o posso expulsar este membro.", ephemeral=True)
        return
    try:
        await membro.kick(reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="ðŸŸ  ExpulsÃ£o Executada",
            description=f"**Membro:** {membro.mention}\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"âŒ Erro ao expulsar: {e}", ephemeral=True)


@bot.tree.command(name="mute", description="Silencia um membro temporariamente (timeout)")
@is_staff()
@app_commands.describe(membro="Membro a ser silenciado", duracao="DuraÃ§Ã£o (ex: 10m, 1h, 1d)", motivo="Motivo")
async def mute(interaction: discord.Interaction, membro: discord.Member, duracao: str, motivo: str = "NÃ£o especificado"):
    padrao = re.compile(r"(\d+)([smhd])")
    matches = list(padrao.finditer(duracao.lower()))
    if not matches:
        await interaction.response.send_message("âŒ Formato invÃ¡lido. Use: `10m`, `1h`, `2d`.", ephemeral=True)
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
        await interaction.response.send_message("âŒ DuraÃ§Ã£o mÃ¡xima: 28 dias.", ephemeral=True)
        return

    try:
        await membro.timeout(total, reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="ðŸŸ¡ Membro Silenciado",
            description=(f"**Membro:** {membro.mention}\n"
                         f"**DuraÃ§Ã£o:** {duracao}\n"
                         f"**Motivo:** {motivo}\n"
                         f"**Moderador:** {interaction.user.mention}"),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"âŒ Erro ao silenciar: {e}", ephemeral=True)


@bot.tree.command(name="unmute", description="Remove o silenciamento de um membro")
@is_staff()
@app_commands.describe(membro="Membro a ser dessilenciado")
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    try:
        await membro.timeout(None, reason=f"Unmute por {interaction.user}")
        embed = discord.Embed(
            title="ðŸ”Š Membro Dessilenciado",
            description=f"**Membro:** {membro.mention}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"âŒ Erro: {e}", ephemeral=True)


@bot.tree.command(name="unban", description="Remove o banimento de um usuÃ¡rio pelo ID")
@is_staff()
@app_commands.describe(user_id="ID do usuÃ¡rio banido", motivo="Motivo do unban")
async def unban(interaction: discord.Interaction, user_id: str, motivo: str = "NÃ£o especificado"):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=f"{interaction.user} | {motivo}")
        embed = discord.Embed(
            title="ðŸŸ¢ Banimento Removido",
            description=f"**UsuÃ¡rio:** {user.mention} (`{user.id}`)\n**Motivo:** {motivo}\n**Moderador:** {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("âŒ UsuÃ¡rio nÃ£o encontrado ou nÃ£o estÃ¡ banido.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"âŒ Erro: {e}", ephemeral=True)


@bot.tree.command(name="warning", description="Aplica uma advertÃªncia a um membro")
@is_staff()
@app_commands.describe(membro="Membro a ser advertido", motivo="Motivo da advertÃªncia")
async def warning(interaction: discord.Interaction, membro: discord.Member, motivo: str = "NÃ£o especificado"):
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
        title="âš ï¸ AdvertÃªncia Registrada",
        description=(f"**Membro:** {membro.mention}\n"
                     f"**Motivo:** {motivo}\n"
                     f"**Moderador:** {interaction.user.mention}\n"
                     f"**Total de advertÃªncias:** {total}"),
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)
    try:
        await membro.send(f"âš ï¸ VocÃª recebeu uma advertÃªncia no servidor **{interaction.guild.name}**.\n**Motivo:** {motivo}\n**Total:** {total}")
    except discord.Forbidden:
        pass


@bot.tree.command(name="warnings", description="Mostra as advertÃªncias de um membro")
@is_staff()
@app_commands.describe(membro="Membro para consultar")
async def warnings(interaction: discord.Interaction, membro: discord.Member):
    dados = carregar_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(membro.id)

    lista = dados.get(guild_id, {}).get(user_id, [])

    if not lista:
        await interaction.response.send_message(f"âœ… {membro.mention} nÃ£o tem advertÃªncias.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"âš ï¸ AdvertÃªncias de {membro.display_name}",
        color=discord.Color.orange()
    )
    for i, w in enumerate(lista, 1):
        embed.add_field(
            name=f"#{i} â€” {w['data'][:10]}",
            value=f"**Motivo:** {w['motivo']}\n**Por:** {w['moderador']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clearwarnings", description="Remove todas as advertÃªncias de um membro")
@is_staff()
@app_commands.describe(membro="Membro para limpar advertÃªncias")
async def clearwarnings(interaction: discord.Interaction, membro: discord.Member):
    dados = carregar_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(membro.id)

    if guild_id in dados and user_id in dados[guild_id]:
        dados[guild_id][user_id] = []
        salvar_warnings(dados)
        await interaction.response.send_message(f"ðŸ§¹ AdvertÃªncias de {membro.mention} limpas.")
    else:
        await interaction.response.send_message(f"âœ… {membro.mention} jÃ¡ nÃ£o tinha advertÃªncias.", ephemeral=True)


@bot.tree.command(name="clear", description="Apaga uma quantidade de mensagens do canal")
@is_staff()
@app_commands.describe(quantidade="Quantas mensagens apagar (1-100)")
async def clear(interaction: discord.Interaction, quantidade: int):
    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message("âŒ Use um valor entre 1 e 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deletadas = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"ðŸ§¹ **{len(deletadas)}** mensagens apagadas.", ephemeral=True)


@bot.tree.command(name="slowmode", description="Define o modo lento do canal em segundos")
@is_staff()
@app_commands.describe(segundos="Segundos entre mensagens (0 desativa)")
async def slowmode(interaction: discord.Interaction, segundos: int):
    if segundos < 0 or segundos > 21600:
        await interaction.response.send_message("âŒ Use entre 0 e 21600 segundos (6 horas).", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=segundos)
    if segundos == 0:
        await interaction.response.send_message("âš¡ Modo lento **desativado**.")
    else:
        await interaction.response.send_message(f"ðŸ¢ Modo lento definido para **{segundos}s**.")


@bot.tree.command(name="lock", description="Tranca o canal para @everyone")
@is_staff()
async def lock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("ðŸ”’ Canal trancado.")


@bot.tree.command(name="unlock", description="Destranca o canal para @everyone")
@is_staff()
async def unlock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("ðŸ”“ Canal destrancado.")


@bot.tree.command(name="userinfo", description="Mostra informaÃ§Ãµes de um usuÃ¡rio")
@app_commands.describe(membro="Membro para consultar (opcional)")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"ðŸ‘¤ {membro}", color=membro.color or discord.Color.blue())
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id, inline=True)
    embed.add_field(name="Apelido", value=membro.nick or "Nenhum", inline=True)
    embed.add_field(name="Bot?", value="Sim" if membro.bot else "NÃ£o", inline=True)
    embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrou em", value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "?", inline=True)
    embed.add_field(name="Cargo mais alto", value=membro.top_role.mention, inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Mostra informaÃ§Ãµes do servidor")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"ðŸ° {g.name}", color=discord.Color.dark_red())
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
# ERROS DE PERMISSÃƒO
# ==============================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("âŒ VocÃª nÃ£o tem permissÃ£o para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"âŒ Erro: {error}", ephemeral=True)


# ==============================
# INICIALIZAÃ‡ÃƒO
# ==============================
bot.run(DISCORD_TOKEN)
