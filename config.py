import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# 🔑 Credenciais Mercado Pago (produção)
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
TOKEN_MERCADOPAGO = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

# Debug do TOKEN_MERCADOPAGO
print("DEBUG TOKEN_MERCADOPAGO:", repr(TOKEN_MERCADOPAGO))

# 🤖 Token do bot do Telegram
TOKEN_BOT = os.getenv("TELEGRAM_TOKEN")

# 👤 IDs e Links
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

# Validação das variáveis de ambiente
def validar_config():
    """Valida se todas as variáveis de ambiente necessárias estão configuradas"""
    variaveis_necessarias = {
        "TOKEN_MERCADOPAGO": TOKEN_MERCADOPAGO,
        "TOKEN_BOT": TOKEN_BOT,
        "MY_CHAT_ID": MY_CHAT_ID,
        "GROUP_INVITE_LINK": GROUP_INVITE_LINK,
        "GROUP_CHAT_ID": GROUP_CHAT_ID
    }
    
    variaveis_faltando = []
    for nome, valor in variaveis_necessarias.items():
        if not valor:
            variaveis_faltando.append(nome)
    
    if variaveis_faltando:
        print("❌ ERRO: As seguintes variáveis de ambiente não estão configuradas:")
        for var in variaveis_faltando:
            print(f"   - {var}")
        print("\n📝 Configure estas variáveis no Railway ou no arquivo .env local")
        return False
    
    print("✅ Todas as variáveis de ambiente estão configuradas!")
    return True

# Converte IDs para inteiro se necessário
try:
    if MY_CHAT_ID:
        MY_CHAT_ID = int(MY_CHAT_ID)
    if GROUP_CHAT_ID:
        GROUP_CHAT_ID = int(GROUP_CHAT_ID)
except (ValueError, TypeError):
    print("⚠️ Aviso: Erro ao converter IDs para inteiro")
