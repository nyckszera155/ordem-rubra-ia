import os
import re
import json
import random
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from openai import OpenAI

# ==============================
# CARREGAMENTO DE VARIÁVEIS
# ==============================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))

MODELO = "openrouter/free"

# ==============================
# CLIENTE OPENROUTER
# ==============================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# ==============================
# CONFIGURAÇÃO DO BOT
# ==============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Histórico de conversa por usuário
historico = {}

# Arquivo de warnings
ARQUIVO_WARN = "warnings.json"


# ==============================
# 📋 DADOS DOS PERCURSOS (fonte única de verdade)
# ==============================
# Estrutura: {percurso: {cargo: {"tempo": "...", "nota": "..."}}}
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

# Texto formatado para injetar no system prompt da IA
DADOS_PERCURSOS_TEXTO = """
📋 PERCURSOS, TEMPOS E NOTAS DE APROVAÇÃO:

1º Percurso (Balamentos):
- Praças: 45 segundos
- Graduados: 40 segundos

2º Percurso (Torre):
- Recruta: 25 segundos
- Soldado: 20 segundos
- Terceiro-Sargento: 16 segundos
- Segundo-Sargento: 14 segundos
- Primeiro-Sargento: 12 segundos

3º Percurso (Torre 2.0):
- Recruta: 30 segundos
- Soldado: 25 segundos
- Terceiro-Sargento: 18 segundos
- Segundo-Sargento: 16 segundos
- Primeiro-Sargento: 14 segundos

4º Percurso:
- Recruta: 35 segundos
- Soldado: 30 segundos

Percurso de Graduados:
- Graduados: 45 segundos

🎯 NOTA DE APROVAÇÃO (pontuação mínima):
- Recruta: 5,0 pontos
- Soldado: 5,5 pontos
- Terceiro-Sargento: 6,0 pontos
- Segundo-Sargento: 6,5 pontos
- Primeiro-Sargento: 6,5 pontos
"""


# ==============================
# 📅 DADOS DA CAPACITAÇÃO DE PATENTE (fonte única de verdade)
# ==============================
# Estrutura: {grupo: [{"cargo": "...", "dias": "...", "detalhe": "..."}]}
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


def montar_texto_cp():
    """Gera o texto da capacitação para injetar no system prompt da IA."""
    linhas = ["📅 CAPACITAÇÃO DE PATENTE (dias necessários e relatórios por patente):"]
    for grupo, itens in CAPACITACAO.items():
        linhas.append(f"\n{grupo}:")
        for item in itens:
            linha = f"- {item['cargo']}: {item['dias']}"
            if item["detalhe"]:
                linha += f" ({item['detalhe']})"
            linhas.append(linha)
    return "\n".join(linhas)


DADOS_CP_TEXTO = montar_texto_cp()


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
# FUNÇÃO DE IA
# ==============================
def perguntar_ia(user_id, texto):
    if user_id not in historico:
        historico[user_id] = [
            {
                "role": "system",
                "content": (
                    "Você é a Ordem Rubra IA, um assistente amigável e prestativo "
                    "no Discord. Responda em português do Brasil de forma natural, "
                    "útil e com personalidade marcante. Você também pode ajudar com "
                    "comandos de moderação quando solicitado.\n\n"
                    "⚠️ REGRA IMPORTANTE: Quando o assunto for tempos de percurso, "
                    "balamentos, torre, torre 2.0, notas de aprovação ou capacitação "
                    "de patente (dias e relatórios necessários), use "
                    "EXCLUSIVAMENTE os dados abaixo. Nunca invente ou estime valores.\n\n"
                    + DADOS_PERCURSOS_TEXTO
                    + "\n"
                    + DADOS_CP_TEXTO
                )
            }
        ]

    historico[user_id].append({"role": "user", "content": texto})

    if len(historico[user_id]) > 21:
        historico[user_id] = [historico[user_id][0]] + historico[user_id][-20:]

    try:
        resposta = client.chat.completions.create(
            model=MODELO,
            messages=historico[user_id],
            temperature=0.4,
            max_tokens=800,
        )
        texto_resposta = resposta.choices[0].message.content
        historico[user_id].append({"role": "assistant", "content": texto_resposta})
        return texto_resposta

    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return "Ops, tive um problema para pensar agora. Tente de novo em alguns instantes!"


# ==============================
# EVENTOS
# ==============================
@bot.event
async def on_ready():
    print(f"🤖 Ordem Rubra IA online como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="vigilância rubra 🔴"))
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash commands: {e}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        texto = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not texto:
            await message.reply("🔴 **Ordem Rubra IA** online. Como posso ajudar?")
            return

        async with message.channel.typing():
            resposta = perguntar_ia(str(message.author.id), texto)

        if len(resposta) > 1900:
            for i in range(0, len(resposta), 1900):
                await message.reply(resposta[i:i+1900])
        else:
            await message.reply(resposta)
        return

    await bot.process_commands(message)


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
    """Dropdown para escolher o percurso."""

    def __init__(self):
        options = [
            discord.SelectOption(label=nome, emoji="🏁", description="Ver cargos e tempos")
            for nome in PERCURSOS.keys()
        ]
        super().__init__(placeholder="Escolha um percurso...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        percurso_escolhido = self.values[0]
        cargos = PERCURSOS[percurso_escolhido]

        # Monta embed com todos os cargos daquele percurso
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

        # Envia um NOVO embed (não substitui o menu, assim a pessoa pode consultar outro)
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
# 📊 COMANDO /nota (consulta rápida de nota por cargo)
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
# COMANDOS DE PREFIXO (!)
# ==============================
@bot.command(name='ia')
async def conversar(ctx, *, texto: str):
    async with ctx.typing():
        resposta = perguntar_ia(str(ctx.author.id), texto)

    if len(resposta) > 1900:
        for i in range(0, len(resposta), 1900):
            await ctx.send(resposta[i:i+1900])
    else:
        await ctx.send(resposta)


@bot.command(name='limpar')
async def limpar(ctx):
    historico.pop(str(ctx.author.id), None)
    await ctx.send("🧹 Histórico limpo! Podemos começar de novo.")


@bot.command(name='modelo')
async def modelo(ctx):
    await ctx.send(f"🧠 Modelo atual: `{MODELO}`")


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
