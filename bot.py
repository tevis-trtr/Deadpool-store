import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
from datetime import datetime
import pytz
import json
import os
import asyncio

# ==========================================
# CONFIGURAÇÕES E VARIÁVEIS GLOBAIS
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN")
TIMEZONE = pytz.timezone("America/Sao_Paulo")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Arquivos de configuração
CONFIG_FILE = "logs_config.json"
VENDAS_CONFIG_FILE = "config.json"
PRODUTOS_FILE = "produtos.json"
PRODUTOS_DROP_FILE = "produtos_drop.json"

# ==========================================
# FUNÇÕES DE CONFIGURAÇÃO - LOGS
# ==========================================

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_logs_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_logs_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_log_channel(guild_id, log_type):
    data = load_logs_config()
    guild_data = data.get(str(guild_id), {})
    channel_id = guild_data.get(log_type)
    if channel_id:
        return bot.get_channel(channel_id)
    return None

def now():
    return datetime.now(TIMEZONE)

# ==========================================
# FUNÇÕES DE CONFIGURAÇÃO - VENDAS
# ==========================================

def load_vendas_config():
    if os.path.exists(VENDAS_CONFIG_FILE):
        with open(VENDAS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'categoria_id': None,
        'pix_info': 'Configure seu PIX com o comando /setup',
        'contador_carrinhos': {},
        'bot_voz_channel': None
    }

def save_vendas_config(config):
    with open(VENDAS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_produtos():
    if os.path.exists(PRODUTOS_FILE):
        with open(PRODUTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_produtos(produtos):
    with open(PRODUTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False)

def load_produtos_drop():
    if os.path.exists(PRODUTOS_DROP_FILE):
        with open(PRODUTOS_DROP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_produtos_drop(produtos_drop):
    with open(PRODUTOS_DROP_FILE, 'w', encoding='utf-8') as f:
        json.dump(produtos_drop, f, indent=4, ensure_ascii=False)

vendas_config = load_vendas_config()
produtos = load_produtos()
produtos_drop = load_produtos_drop()

# ==========================================
# EVENTO ON_READY
# ==========================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"╔══════════════════════════════════════╗")
    print(f"║   🤖 VIREX STORE BOT ONLINE!        ║")
    print(f"║   Bot: {bot.user.name:<25} ║")
    print(f"║   ID: {bot.user.id:<26} ║")
    print(f"╚══════════════════════════════════════╝")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="vendas | /ajudavirexstore"
        )
    )

# ==========================================
# COMANDO: /AJUDAVIREXSTORE
# ==========================================

@bot.tree.command(name="ajudavirexstore", description="📋 Ver todos os comandos disponíveis do VIREX STORE")
async def ajudavirexstore(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 VIREX STORE - Comandos Disponíveis",
        description="Sistema completo de vendas e logs para Discord",
        color=discord.Color.blue()
    )
    
    # Comandos de Vendas
    embed.add_field(
        name="💰 **SISTEMA DE VENDAS**",
        value=(
            "`/setup` - Painel principal de configuração\n"
            "`/enviarproduto` - Enviar painel de produto\n"
            "`/enviardrop` - Enviar painel dropdown"
        ),
        inline=False
    )
    
    # Comandos de Logs
    embed.add_field(
        name="📊 **SISTEMA DE LOGS**",
        value=(
            "`/setuplogs` - Configurar canais de logs\n"
            "• Entradas, Saídas, Mensagens\n"
            "• Edições, Deleções, Bans\n"
            "• Cargos, Canais, Voz"
        ),
        inline=False
    )
    
    # Comandos de Utilidades
    embed.add_field(
        name="🛠️ **UTILIDADES**",
        value=(
            "`/botvoz` - Bot entra em canal de voz\n"
            "`/banfake` - Simula um ban (brincadeira)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👑 **PERMISSÕES**",
        value="Comandos de configuração requerem:\n• Dono do Servidor\n• Administrador",
        inline=False
    )
    
    embed.set_footer(
        text=f"Solicitado por: {interaction.user.name} | VIREX STORE",
        icon_url=interaction.user.display_avatar.url
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# COMANDO: /SETUPLOGS
# ==========================================

@bot.tree.command(name="setuplogs", description="⚙️ Configurar canal de logs")
@app_commands.describe(
    tipo="Tipo de log",
    canal="Canal para enviar os logs"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="📥 Entradas", value="join"),
    app_commands.Choice(name="📤 Saídas", value="leave"),
    app_commands.Choice(name="💬 Mensagens", value="message"),
    app_commands.Choice(name="✏️ Edição", value="edit"),
    app_commands.Choice(name="🗑️ Delete", value="delete"),
    app_commands.Choice(name="🔨 Ban", value="ban"),
    app_commands.Choice(name="🎭 Cargos", value="role"),
    app_commands.Choice(name="📁 Canais", value="channel"),
    app_commands.Choice(name="🔊 Voz", value="voice"),
])
async def setuplogs(interaction: discord.Interaction, tipo: app_commands.Choice[str], canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        return

    data = load_logs_config()
    guild_id = str(interaction.guild.id)

    if guild_id not in data:
        data[guild_id] = {}

    data[guild_id][tipo.value] = canal.id
    save_logs_config(data)

    await interaction.response.send_message(
        f"✅ Log **{tipo.name}** configurado em {canal.mention}",
        ephemeral=True
    )

# ==========================================
# COMANDO: /BOTVOZ
# ==========================================

@bot.tree.command(name="botvoz", description="🔊 Bot entra em um canal de voz (mutado e sem ouvir)")
@app_commands.describe(
    canal="Canal de voz onde o bot entrará",
    imagem="URL da imagem para o bot mostrar (opcional)"
)
async def botvoz(interaction: discord.Interaction, canal: discord.VoiceChannel, imagem: str = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        return

    try:
        # Verificar se já está conectado
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
        
        # Conectar ao canal
        vc = await canal.connect()
        
        # Mutar e desmutar áudio (surdo)
        await vc.guild.change_voice_state(channel=canal, self_mute=True, self_deaf=True)
        
        # Salvar configuração
        vendas_config['bot_voz_channel'] = canal.id
        save_vendas_config(vendas_config)
        
        embed = discord.Embed(
            title="✅ Bot Conectado em Voz!",
            description=f"🔊 Conectado em: {canal.mention}\n🔇 Status: Mutado e Surdo",
            color=discord.Color.green()
        )
        
        if imagem:
            embed.set_image(url=imagem)
        
        embed.set_footer(text=f"Bot permanecerá no canal até ser desconectado manualmente")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erro ao conectar: {str(e)}\n\n💡 **Nota:** Para usar áudio, instale: `pip install PyNaCl`",
            ephemeral=True
        )

# ==========================================
# COMANDO: /BANFAKE
# ==========================================

@bot.tree.command(name="banfake", description="🔨 Simula um ban falso (brincadeira)")
@app_commands.describe(membro="Membro para 'banir' (fake)")
async def banfake(interaction: discord.Interaction, membro: discord.Member):
    embed = discord.Embed(
        title="🔨 Você foi banido!",
        description=f"{membro.mention} foi banido do servidor por violação das regras.",
        color=discord.Color.dark_red()
    )
    
    embed.add_field(name="Motivo", value="Comportamento inadequado", inline=False)
    embed.add_field(name="Duração", value="Permanente", inline=False)
    
    embed.set_footer(text="⚠️ ISTO É UMA BRINCADEIRA - Nenhuma ação real foi tomada")
    
    await interaction.response.send_message(embed=embed)

# ==========================================
# COMANDO: /SETUP (Sistema de Vendas)
# ==========================================

@bot.tree.command(name="setup", description="⚙️ Painel de configuração do sistema de vendas")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⚙️ VIREX STORE - Painel de Configuração",
        description="**Bem-vindo ao sistema de vendas!**\n\nEscolha uma opção abaixo para configurar seu bot:",
        color=discord.Color.blue()
    )
    
    categoria_status = "✅ Configurada" if vendas_config.get('categoria_id') else "❌ Não configurada"
    pix_status = "✅ Configurado" if vendas_config.get('pix_info') != 'Configure seu PIX com o comando /setup' else "❌ Não configurado"
    produtos_count = len(produtos)
    produtos_drop_count = len(produtos_drop)
    
    embed.add_field(name="📁 Categoria", value=categoria_status, inline=True)
    embed.add_field(name="💳 PIX", value=pix_status, inline=True)
    embed.add_field(name="📦 Produtos", value=f"{produtos_count} cadastrados", inline=True)
    embed.add_field(name="📋 Produtos Drop", value=f"{produtos_drop_count} cadastrados", inline=True)
    
    embed.set_footer(text=f"Comando usado por: {interaction.user.name}")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    # Criar botões
    btn_categoria = Button(label="📁 Categoria", style=discord.ButtonStyle.primary, row=0)
    btn_pix = Button(label="💳 PIX", style=discord.ButtonStyle.primary, row=0)
    
    btn_criar_produto = Button(label="➕ Produto", style=discord.ButtonStyle.success, row=1)
    btn_criar_drop = Button(label="📋 Dropdown", style=discord.ButtonStyle.success, row=1)
    
    btn_enviar_painel = Button(label="📤 Enviar Produto", style=discord.ButtonStyle.secondary, row=2)
    btn_enviar_drop = Button(label="📤 Enviar Drop", style=discord.ButtonStyle.secondary, row=2)
    
    btn_listar = Button(label="📋 Listar Tudo", style=discord.ButtonStyle.secondary, row=3)
    
    def check_permissions(inter):
        return (inter.user.id == inter.guild.owner_id or inter.user.guild_permissions.administrator)
    
    # Callbacks dos botões
    async def categoria_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        categorias = [cat for cat in inter.guild.categories]
        if not categorias:
            await inter.response.send_message("❌ Nenhuma categoria encontrada!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(label=cat.name, value=str(cat.id), description=f"ID: {cat.id}")
            for cat in categorias[:25]
        ]
        
        select = Select(placeholder="Escolha uma categoria...", options=options)
        
        async def select_callback(sel_inter):
            if not check_permissions(sel_inter):
                await sel_inter.response.send_message("❌ Sem permissão!", ephemeral=True)
                return
            
            vendas_config['categoria_id'] = int(select.values[0])
            save_vendas_config(vendas_config)
            await sel_inter.response.send_message("✅ Categoria configurada!", ephemeral=True)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        await inter.response.send_message("📁 Selecione a categoria:", view=view_select, ephemeral=True)
    
    async def pix_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        modal = Modal(title="Configurar PIX")
        pix_input = TextInput(
            label="Informações do PIX",
            placeholder="Ex: Chave PIX: seuemail@exemplo.com",
            style=discord.TextStyle.paragraph,
            max_length=500,
            default=vendas_config.get('pix_info', '')
        )
        modal.add_item(pix_input)
        
        async def on_submit(modal_inter):
            vendas_config['pix_info'] = pix_input.value
            save_vendas_config(vendas_config)
            await modal_inter.response.send_message("✅ PIX configurado!", ephemeral=True)
        
        modal.on_submit = on_submit
        await inter.response.send_modal(modal)
    
    async def criar_produto_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        modal = CriarProdutoModal()
        await inter.response.send_modal(modal)
    
    async def criar_drop_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        modal = CriarProdutoDropModal1()
        await inter.response.send_modal(modal)
    
    async def enviar_painel_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        if not produtos:
            await inter.response.send_message("❌ Nenhum produto cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(label=prod['titulo'], value=prod_id, description=f"R$ {prod['preco']}")
            for prod_id, prod in produtos.items()
        ]
        
        select = Select(placeholder="Escolha o produto...", options=options[:25])
        
        async def select_callback(sel_inter):
            if not check_permissions(sel_inter):
                await sel_inter.response.send_message("❌ Sem permissão!", ephemeral=True)
                return
            
            prod_id = select.values[0]
            produto = produtos[prod_id]
            
            embed_produto = discord.Embed(
                title=produto['titulo'],
                description=produto['descricao'],
                color=discord.Color.gold()
            )
            embed_produto.add_field(name="💰 Preço", value=f"R$ {produto['preco']}", inline=True)
            
            if produto.get('imagem_url'):
                embed_produto.set_image(url=produto['imagem_url'])
            
            embed_produto.set_footer(text="Clique em 'Comprar' para iniciar sua compra!")
            
            button = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)
            
            async def comprar_callback(btn_inter):
                await criar_carrinho(btn_inter, produto, prod_id)
            
            button.callback = comprar_callback
            view_produto = View(timeout=None)
            view_produto.add_item(button)
            
            await sel_inter.channel.send(embed=embed_produto, view=view_produto)
            await sel_inter.response.send_message("✅ Painel enviado!", ephemeral=True)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        await inter.response.send_message("📤 Selecione o produto:", view=view_select, ephemeral=True)
    
    async def enviar_drop_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        if not produtos_drop:
            await inter.response.send_message("❌ Nenhum dropdown cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(
                label=drop['titulo_painel'],
                value=drop_id,
                description=f"{len(drop['opcoes'])} opções",
                emoji=drop['emoji_painel']
            )
            for drop_id, drop in produtos_drop.items()
        ]
        
        select = Select(placeholder="Escolha o dropdown...", options=options[:25])
        
        async def select_callback(sel_inter):
            if not check_permissions(sel_inter):
                await sel_inter.response.send_message("❌ Sem permissão!", ephemeral=True)
                return
            
            drop_id = select.values[0]
            painel = produtos_drop[drop_id]
            
            embed_painel = discord.Embed(
                title=f"{painel['emoji_painel']} {painel['titulo_painel']}",
                description=painel['descricao_painel'],
                color=discord.Color.gold()
            )
            
            if painel.get('imagem_url'):
                embed_painel.set_image(url=painel['imagem_url'])
            
            embed_painel.set_footer(text="Selecione uma opção no menu abaixo!")
            
            opcoes_select = []
            for i, opcao in enumerate(painel['opcoes'][:25]):
                opcoes_select.append(
                    discord.SelectOption(
                        label=opcao['nome'],
                        value=str(i),
                        description=opcao['descricao'],
                        emoji=opcao['emoji']
                    )
                )
            
            produto_select = Select(placeholder="Selecione uma opção", options=opcoes_select)
            
            async def produto_select_callback(prod_inter):
                opcao_index = int(produto_select.values[0])
                opcao_selecionada = painel['opcoes'][opcao_index]
                
                produto_temp = {
                    'titulo': f"{painel['titulo_painel']} - {opcao_selecionada['nome']}",
                    'descricao': f"{painel['descricao_painel']}\n\n**Opção:** {opcao_selecionada['nome']}",
                    'preco': opcao_selecionada['preco'],
                    'imagem_url': painel.get('imagem_url'),
                    'tipo_imagem': painel.get('tipo_imagem', 'gif')
                }
                
                await criar_carrinho(prod_inter, produto_temp, f"{drop_id}_{opcao_index}")
            
            produto_select.callback = produto_select_callback
            view_painel = View(timeout=None)
            view_painel.add_item(produto_select)
            
            await sel_inter.channel.send(embed=embed_painel, view=view_painel)
            await sel_inter.response.send_message("✅ Dropdown enviado!", ephemeral=True)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        await inter.response.send_message("📤 Selecione o dropdown:", view=view_select, ephemeral=True)
    
    async def listar_callback(inter):
        if not check_permissions(inter):
            await inter.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        embed_lista = discord.Embed(
            title="📋 Produtos e Dropdowns Cadastrados",
            color=discord.Color.blue()
        )
        
        if produtos:
            produtos_text = "\n".join([f"• **{prod['titulo']}** - R$ {prod['preco']}" for prod['titulo'] in produtos])
            embed_lista.add_field(name="📦 Produtos", value=produtos_text or "Nenhum", inline=False)
        
        if produtos_drop:
            drops_text = "\n".join([f"• **{drop['titulo_painel']}** - {len(drop['opcoes'])} opções" for drop in produtos_drop.values()])
            embed_lista.add_field(name="📋 Dropdowns", value=drops_text or "Nenhum", inline=False)
        
        if not produtos and not produtos_drop:
            embed_lista.description = "❌ Nenhum produto ou dropdown cadastrado ainda!"
        
        await inter.response.send_message(embed=embed_lista, ephemeral=True)
    
    # Atribuir callbacks
    btn_categoria.callback = categoria_callback
    btn_pix.callback = pix_callback
    btn_criar_produto.callback = criar_produto_callback
    btn_criar_drop.callback = criar_drop_callback
    btn_enviar_painel.callback = enviar_painel_callback
    btn_enviar_drop.callback = enviar_drop_callback
    btn_listar.callback = listar_callback
    
    # Criar view
    view = View(timeout=300)
    view.add_item(btn_categoria)
    view.add_item(btn_pix)
    view.add_item(btn_criar_produto)
    view.add_item(btn_criar_drop)
    view.add_item(btn_enviar_painel)
    view.add_item(btn_enviar_drop)
    view.add_item(btn_listar)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==========================================
# MODALS - Sistema de Vendas
# ==========================================

class CriarProdutoModal(Modal):
    def __init__(self):
        super().__init__(title="Criar Novo Produto")
        
        self.titulo = TextInput(label="Título", placeholder="Ex: VIP Premium", max_length=100)
        self.descricao = TextInput(label="Descrição", placeholder="Descreva o produto...", style=discord.TextStyle.paragraph, max_length=1000)
        self.preco = TextInput(label="Preço (R$)", placeholder="Ex: 29.90", max_length=10)
        self.imagem_url = TextInput(label="URL da Imagem", placeholder="https://...", required=False, max_length=500)
        
        self.add_item(self.titulo)
        self.add_item(self.descricao)
        self.add_item(self.preco)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        produto_id = f"prod_{len(produtos) + 1}"
        
        produtos[produto_id] = {
            'titulo': self.titulo.value,
            'descricao': self.descricao.value,
            'preco': self.preco.value,
            'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
            'tipo_imagem': 'gif',
            'criado_em': datetime.now().isoformat()
        }
        
        save_produtos(produtos)
        
        embed = discord.Embed(
            title="✅ Produto Criado!",
            description=f"**ID:** {produto_id}\n**Título:** {self.titulo.value}\n**Preço:** R$ {self.preco.value}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CriarProdutoDropModal1(Modal):
    def __init__(self):
        super().__init__(title="Criar Painel Dropdown")
        
        self.titulo_painel = TextInput(label="Título do Painel", placeholder="Ex: Escolha seu pacote", max_length=100)
        self.descricao_painel = TextInput(label="Descrição", placeholder="Selecione a quantidade", style=discord.TextStyle.paragraph, max_length=1000)
        self.emoji_painel = TextInput(label="Emoji (opcional)", placeholder="Ex: 💎", required=False, max_length=10)
        self.imagem_url = TextInput(label="URL da Imagem", placeholder="https://...", required=False, max_length=500)
        
        self.add_item(self.titulo_painel)
        self.add_item(self.descricao_painel)
        self.add_item(self.emoji_painel)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        temp_id = f"temp_{interaction.user.id}"
        
        if not hasattr(bot, 'temp_produtos_drop'):
            bot.temp_produtos_drop = {}
        
        bot.temp_produtos_drop[temp_id] = {
            'titulo_painel': self.titulo_painel.value,
            'descricao_painel': self.descricao_painel.value,
            'emoji_painel': self.emoji_painel.value if self.emoji_painel.value else '📦',
            'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
            'tipo_imagem': 'gif',
            'opcoes': []
        }
        
        button_add = Button(label="➕ Adicionar Opção", style=discord.ButtonStyle.success)
        button_finish = Button(label="✅ Finalizar", style=discord.ButtonStyle.primary)
        
        async def add_option_callback(btn_inter):
            modal = CriarOpcaoDropModal(temp_id)
            await btn_inter.response.send_modal(modal)
        
        async def finish_callback(btn_inter):
            if len(bot.temp_produtos_drop[temp_id]['opcoes']) == 0:
                await btn_inter.response.send_message("❌ Adicione pelo menos uma opção!", ephemeral=True)
                return
            
            drop_id = f"drop_{len(produtos_drop) + 1}"
            produtos_drop[drop_id] = bot.temp_produtos_drop[temp_id]
            produtos_drop[drop_id]['criado_em'] = datetime.now().isoformat()
            save_produtos_drop(produtos_drop)
            
            del bot.temp_produtos_drop[temp_id]
            
            embed = discord.Embed(
                title="✅ Dropdown Criado!",
                description=f"**ID:** {drop_id}\n**Opções:** {len(produtos_drop[drop_id]['opcoes'])}",
                color=discord.Color.green()
            )
            
            await btn_inter.response.send_message(embed=embed, ephemeral=True)
        
        button_add.callback = add_option_callback
        button_finish.callback = finish_callback
        
        view = View(timeout=300)
        view.add_item(button_add)
        view.add_item(button_finish)
        
        embed = discord.Embed(
            title="➕ Adicionar Opções",
            description=f"**Painel:** {self.titulo_painel.value}\n\nClique em 'Adicionar Opção' para cada produto.",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CriarOpcaoDropModal(Modal):
    def __init__(self, temp_id):
        super().__init__(title="Adicionar Opção")
        self.temp_id = temp_id
        
        self.nome_opcao = TextInput(label="Nome", placeholder="Ex: 10 SALAS", max_length=100)
        self.descricao_opcao = TextInput(label="Descrição", placeholder="Ex: Valor: 2.90", max_length=100, required=False)
        self.preco = TextInput(label="Preço (R$)", placeholder="Ex: 2.90", max_length=10)
        self.emoji_opcao = TextInput(label="Emoji (opcional)", placeholder="Ex: 💰", required=False, max_length=10)
        
        self.add_item(self.nome_opcao)
        self.add_item(self.descricao_opcao)
        self.add_item(self.preco)
        self.add_item(self.emoji_opcao)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.temp_id not in bot.temp_produtos_drop:
            await interaction.response.send_message("❌ Erro: dados não encontrados!", ephemeral=True)
            return
        
        opcao = {
            'nome': self.nome_opcao.value,
            'descricao': self.descricao_opcao.value if self.descricao_opcao.value else f"Valor: {self.preco.value}",
            'preco': self.preco.value,
            'emoji': self.emoji_opcao.value if self.emoji_opcao.value else '💎'
        }
        
        bot.temp_produtos_drop[self.temp_id]['opcoes'].append(opcao)
        
        embed = discord.Embed(
            title="✅ Opção Adicionada!",
            description=f"**Nome:** {opcao['nome']}\n**Preço:** R$ {opcao['preco']}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# FUNÇÃO CRIAR CARRINHO
# ==========================================

async def criar_carrinho(interaction, produto, prod_id):
    guild = interaction.guild
    user = interaction.user
    
    if not vendas_config.get('categoria_id'):
        await interaction.response.send_message("❌ Categoria não configurada! Use /setup", ephemeral=True)
        return
    
    categoria = guild.get_channel(vendas_config['categoria_id'])
    
    if not categoria:
        await interaction.response.send_message("❌ Categoria não encontrada!", ephemeral=True)
        return
    
    if str(guild.id) not in vendas_config['contador_carrinhos']:
        vendas_config['contador_carrinhos'][str(guild.id)] = 0
    
    numero = vendas_config['contador_carrinhos'][str(guild.id)]
    vendas_config['contador_carrinhos'][str(guild.id)] += 1
    save_vendas_config(vendas_config)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    nome_canal = f"🛒{user.name}-{numero}"
    canal = await categoria.create_text_channel(name=nome_canal, overwrites=overwrites)
    
    embed_carrinho = discord.Embed(
        title=f"🛒 Carrinho - {produto['titulo']}",
        description=produto['descricao'],
        color=discord.Color.blue()
    )
    
    embed_carrinho.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=True)
    embed_carrinho.add_field(name="👤 Cliente", value=user.mention, inline=True)
    
    if produto.get('imagem_url'):
        embed_carrinho.set_image(url=produto['imagem_url'])
    
    embed_carrinho.set_footer(text="Use os botões abaixo para gerenciar o pagamento")
    
    pix_btn = Button(label="💳 Ver PIX", style=discord.ButtonStyle.primary)
    aprovar_btn = Button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    fechar_btn = Button(label="🔒 Fechar", style=discord.ButtonStyle.danger)
    
    async def pix_callback(btn_inter):
        embed_pix = discord.Embed(
            title="💳 Informações PIX",
            description=vendas_config.get('pix_info', 'Configure o PIX com /setup'),
            color=discord.Color.gold()
        )
        embed_pix.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=False)
        await btn_inter.response.send_message(embed=embed_pix, ephemeral=True)
    
    async def aprovar_callback(btn_inter):
        if btn_inter.user.id != guild.owner_id and not btn_inter.user.guild_permissions.administrator:
            await btn_inter.response.send_message("❌ Apenas admins podem aprovar!", ephemeral=True)
            return
        
        await btn_inter.response.send_message(f"✅ Pagamento aprovado! {user.mention}, obrigado! 🎉")
    
    async def fechar_callback(btn_inter):
        if btn_inter.user.id != guild.owner_id and not btn_inter.user.guild_permissions.administrator:
            await btn_inter.response.send_message("❌ Apenas admins podem fechar!", ephemeral=True)
            return
        
        await btn_inter.response.send_message("🔒 Fechando em 5 segundos...")
        await asyncio.sleep(5)
        await canal.delete()
    
    pix_btn.callback = pix_callback
    aprovar_btn.callback = aprovar_callback
    fechar_btn.callback = fechar_callback
    
    view = View(timeout=None)
    view.add_item(pix_btn)
    view.add_item(aprovar_btn)
    view.add_item(fechar_btn)
    
    await canal.send(f"{user.mention}", embed=embed_carrinho, view=view)
    await interaction.response.send_message(f"✅ Carrinho criado! {canal.mention}", ephemeral=True)

# ==========================================
# EVENTOS DE LOGS
# ==========================================

@bot.event
async def on_member_join(member):
    channel = get_log_channel(member.guild.id, "join")
    if not channel:
        return

    embed = discord.Embed(
        title="📥 Membro entrou",
        color=discord.Color.green(),
        timestamp=now()
    )

    embed.add_field(name="Usuário", value=member.mention)
    embed.add_field(name="Conta criada", value=f"<t:{int(member.created_at.timestamp())}:R>")

    await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = get_log_channel(member.guild.id, "leave")
    if not channel:
        return

    embed = discord.Embed(
        title="📤 Membro saiu",
        color=discord.Color.red(),
        timestamp=now()
    )

    embed.add_field(name="Usuário", value=str(member))

    await channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    channel = get_log_channel(guild.id, "ban")
    if not channel:
        return

    embed = discord.Embed(
        title="🔨 Usuário banido",
        color=discord.Color.dark_red(),
        timestamp=now()
    )

    embed.add_field(name="Usuário", value=str(user))

    await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel = get_log_channel(message.guild.id, "delete")
    if not channel:
        return

    embed = discord.Embed(
        title="🗑️ Mensagem apagada",
        color=discord.Color.orange(),
        timestamp=now()
    )

    embed.add_field(name="Autor", value=message.author.mention)
    embed.add_field(name="Canal", value=message.channel.mention)
    embed.add_field(name="Conteúdo", value=message.content or "Sem texto", inline=False)

    await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    channel = get_log_channel(before.guild.id, "edit")
    if not channel:
        return

    embed = discord.Embed(
        title="✏️ Mensagem editada",
        color=discord.Color.yellow(),
        timestamp=now()
    )

    embed.add_field(name="Autor", value=before.author.mention)
    embed.add_field(name="Antes", value=before.content or "Vazio", inline=False)
    embed.add_field(name="Depois", value=after.content or "Vazio", inline=False)

    await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    channel = get_log_channel(member.guild.id, "voice")
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(f"🔊 {member.mention} entrou em {after.channel.mention}")
    elif before.channel is not None and after.channel is None:
        await channel.send(f"🔇 {member.mention} saiu de {before.channel.mention}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Detectar comprovantes em carrinhos
    if message.channel.name.startswith('🛒') and message.attachments:
        owner = message.guild.owner
        admins = [m for m in message.guild.members if m.guild_permissions.administrator and not m.bot]
        
        mentions = f"{owner.mention}"
        if admins:
            mentions += " " + " ".join([m.mention for m in admins[:3]])
        
        await message.channel.send(f"📸 {mentions}, comprovante enviado por {message.author.mention}!")
    
    await bot.process_commands(message)

# ==========================================
# INICIAR BOT
# ==========================================

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERRO: Variável DISCORD_TOKEN não configurada!")
        print("💡 Configure no Railway: Settings > Variables > DISCORD_TOKEN")
    else:
        print("🚀 Iniciando VIREX STORE...")
        bot.run(TOKEN)