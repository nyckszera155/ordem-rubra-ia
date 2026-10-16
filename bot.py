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
# 📚 TEXTOS INFORMATIVOS
# ==============================
TEXTO_HISTORICO_PRESIDENCIAL = """**Neste documento estará listado todos os Presidentes e Vice-Presidentes da República eleitos oficialmente de forma democrática:**
https://docs.google.com/document/d/1lCagVTXlaxZX7lal80h0y7rjfCVOe4g-E6B_xi-fZs4/edit?usp=sharing"""

TEXTO_PROCESSOS = """**➣ 1.1 - Processos Seletivos do Exército Brasileiro & Suas Designações**
-# Designações - Processos Seletivos:
> ⤷  **Cursos:** EsPCEx, ESA, ERP, CIOU e CFAP.
> ⤷  **Subdivisões:** STM e SGEx.
> ⤷  **Divisões:** BPE, BFE e BAC.
> ⤷  **Unidade:** CIE (contabiliza como divisão também).
> ⤷  **Especialização:** COpEsp.
> ⤷  **Setores:** Investidores e SCI.

-# Legislação vigente: cada militar poderá participar de apenas dois cursos e prestar no máximo quatro funções dentro da instituição: (divisão, subdivisão, curso e oficialato)"""

TEXTO_PRONOMES = """**Segue o link de pronomes do EB do Apex**

```II - PRONOMES.```
> **➣ Aqui ao lado os - Pronomes Vigentes do Exército Brasileiro.**
>
>  **[CLIQUE AQUI!](https://docs.google.com/document/d/1hdTXemfHoTXCG8i1xZcXFo06ntZCnSrtvpm6nsqaC8A/edit?usp=sharing)**"""

TEXTO_NORMAS = """> **➣ Segue as - Normas e Procedimentos de Arquivamentos Administrativos.**
>
>  **[CLIQUE AQUI!](https://docs.google.com/document/d/1H0QCw8CjO22AXeTrfsU__P1TngkmJ7x40gOBlxTxs4w/edit?usp=sharing)**"""

TEXTO_ADMINISTRADOR = """**Segue o link do que os administrador/moderadores fazem no EB Do Apex**
**[CLIQUE AQUI!](https://docs.google.com/document/d/1Od0rpORegpcvtwATTwaSYbvERpjib5pA4V_xyaDV5EE/edit?usp=sharing)**"""

TEXTO_VEDACAO = """> **➣ Segue o link da - Vedação de Acessos / Exilados Permanentes - IN GAME.**
>
> **[CLIQUE AQUI!](https://docs.google.com/document/d/13bpYEqPcT4EMISNtPQI4uodiA1frsBJ9u1r0TdXQNNY/edit?usp=sharing)**"""

TEXTO_MANUAL_RECRUTA = """> **➣ Segue o link do - Manual do Recruta.**
>
> **[CLIQUE AQUI!](https://docs.google.com/document/d/100aK96ecdRIHDpPaq0VEFVMnLHRMBrrHXPwM1-kEhRI/edit?usp=sharing)**"""

TEXTO_MANUAL_CABO = """> **➣ Segue o link do - Manual do Cabo.**
>
> **[CLIQUE AQUI!](https://drive.google.com/file/d/1CErMt2Q24Qbun44diCsnyx0hhVl9nX49/view)**"""


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


@historico.command(name="presidencial", description="Histórico de Presidentes e Vice-Presidentes eleitos")
async def historico_presidencial(interaction: discord.Interaction):
    embed = embed_info(
        "🗳️ Histórico Presidencial",
        "**Neste documento estará listado todos os Presidentes e Vice-Presidentes da República eleitos oficialmente de forma democrática:**\n\n"
        "🔗 **[CLIQUE AQUI PARA ABRIR O DOCUMENTO](https://docs.google.com/document/d/1lCagVTXlaxZX7lal80h0y7rjfCVOe4g-E6B_xi-fZs4/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


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
@bot.tree.command(name="pronomes", description="Link dos pronomes vigentes do Exército Brasileiro")
async def pronomes(interaction: discord.Interaction):
    embed = embed_info(
        "🏷️ Pronomes Vigentes — EB do Apex",
        "**II - PRONOMES**\n"
        "> ➣ Aqui ao lado os **Pronomes Vigentes do Exército Brasileiro**.\n\n"
        "🔗 **[CLIQUE AQUI!](https://docs.google.com/document/d/1hdTXemfHoTXCG8i1xZcXFo06ntZCnSrtvpm6nsqaC8A/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


# ==============================
# 🗂️ /normas
# ==============================
@bot.tree.command(name="normas", description="Normas e procedimentos de arquivamentos administrativos")
async def normas(interaction: discord.Interaction):
    embed = embed_info(
        "🗂️ Normas e Procedimentos",
        "> ➣ Segue as **Normas e Procedimentos de Arquivamentos Administrativos**.\n\n"
        "🔗 **[CLIQUE AQUI!](https://docs.google.com/document/d/1H0QCw8CjO22AXeTrfsU__P1TngkmJ7x40gOBlxTxs4w/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


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


@manual.command(name="recruta", description="Link do Manual do Recruta")
async def manual_recruta(interaction: discord.Interaction):
    embed = embed_info(
        "📘 Manual do Recruta",
        "> ➣ Segue o link do **Manual do Recruta**.\n\n"
        "🔗 **[CLIQUE AQUI!](https://docs.google.com/document/d/100aK96ecdRIHDpPaq0VEFVMnLHRMBrrHXPwM1-kEhRI/edit?usp=sharing)**",
    )
    await interaction.response.send_message(embed=embed)


@manual.command(name="cabo", description="Link do Manual do Cabo")
async def manual_cabo(interaction: discord.Interaction):
    embed = embed_info(
        "📘 Manual do Cabo",
        "> ➣ Segue o link do **Manual do Cabo**.\n\n"
        "🔗 **[CLIQUE AQUI!](https://drive.google.com/file/d/1CErMt2Q24Qbun44diCsnyx0hhVl9nX49/view)**",
    )
    await interaction.response.send_message(embed=embed)


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
