import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# 🔑 Credenciais Mercado Pago (produção)
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
TOKEN_MERCADOPAGO = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

# 🤖 Token do bot do Telegram
TOKEN_BOT = os.getenv("TELEGRAM_TOKEN")

# 👤 IDs e Links
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

def validar_config():
    """Valida se todas as variáveis de ambiente necessárias estão configuradas"""
    variaveis_necessarias = {
        "MERCADOPAGO_ACCESS_TOKEN": TOKEN_MERCADOPAGO,
        "TELEGRAM_TOKEN": TOKEN_BOT,
        "MY_CHAT_ID": MY_CHAT_ID,
        "GROUP_INVITE_LINK": GROUP_INVITE_LINK,
        "GROUP_CHAT_ID": GROUP_CHAT_ID
    }
    
    faltando = [nome for nome, valor in variaveis_necessarias.items() if not valor]
    
    if faltando:
        print("❌ ERRO: Variáveis de ambiente faltando:")
        for nome in faltando:
            print(f"   - {nome}")
        print("👉 Configure no Railway em: Variables")
        return False
    
    print("✅ Todas as variáveis de ambiente foram carregadas!")
    return True

# 🚨 Debug para não perder tempo se der erro
print("🔎 DEBUG ENV VARS:")
print(f"MERCADOPAGO_ACCESS_TOKEN: {bool(TOKEN_MERCADOPAGO)}")
print(f"TELEGRAM_TOKEN: {bool(TOKEN_BOT)}")
print(f"MY_CHAT_ID: {MY_CHAT_ID}")
print(f"GROUP_INVITE_LINK: {GROUP_INVITE_LINK}")
print(f"GROUP_CHAT_ID: {GROUP_CHAT_ID}")

# Converte IDs para int se possível
try:
    if MY_CHAT_ID:
        MY_CHAT_ID = int(MY_CHAT_ID)
    if GROUP_CHAT_ID:
        GROUP_CHAT_ID = int(GROUP_CHAT_ID)
    print("✅ IDs convertidos para inteiro com sucesso")
except (ValueError, TypeError) as e:
    print(f"⚠️ Aviso: Erro ao converter IDs para inteiro: {e}")
    print("   Verifique se MY_CHAT_ID e GROUP_CHAT_ID contêm apenas números")

# Validação final
if __name__ == "__main__":
    validar_config()
