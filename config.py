import os
import sys
from dotenv import load_dotenv
import mercadopago

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# 🔧 Configuração de Debug
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
AMBIENTE = "desenvolvimento" if DEBUG else "produção"

# 🔑 Credenciais Mercado Pago (produção)
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
TOKEN_MERCADOPAGO = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

# 🤖 Token do bot do Telegram
TOKEN_BOT = os.getenv("TELEGRAM_TOKEN")

# 👤 IDs e Links
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

# Converte IDs para int silenciosamente
try:
    if MY_CHAT_ID:
        MY_CHAT_ID = int(MY_CHAT_ID)
    if GROUP_CHAT_ID:
        GROUP_CHAT_ID = int(GROUP_CHAT_ID)
except (ValueError, TypeError):
    pass  # Será tratado na validação

# 💰 SDK do Mercado Pago - Lazy Loading
_sdk = None
_mp_inicializado = False

def _inicializar_mercadopago():
    """Inicializa o SDK do Mercado Pago (uso interno)"""
    global _sdk, _mp_inicializado
    
    if _mp_inicializado:
        return True
    
    if not TOKEN_MERCADOPAGO:
        return False
    
    try:
        # Inicializa o SDK
        _sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
        
        # Testa a conexão fazendo uma chamada simples
        test_response = _sdk.payment_methods().list_all()
        
        if test_response.get("status") == 200:
            _mp_inicializado = True
            if DEBUG:
                print("✅ SDK Mercado Pago inicializado com sucesso (lazy loading)")
            return True
        else:
            _mp_inicializado = True  # SDK criado, mas resposta não confirmada
            return True
            
    except Exception as e:
        if DEBUG:
            print(f"❌ ERRO ao inicializar SDK Mercado Pago: {str(e)}")
        _mp_inicializado = False
        return False

def validar_config(silencioso=False):
    """
    Valida se todas as variáveis de ambiente necessárias estão configuradas
    
    Args:
        silencioso: Se True, não imprime mensagens de erro
    
    Returns:
        tuple: (config_ok, faltando, ids_invalidos)
    """
    variaveis_necessarias = {
        "MERCADOPAGO_ACCESS_TOKEN": TOKEN_MERCADOPAGO,
        "PUBLIC_KEY": PUBLIC_KEY,
        "TELEGRAM_TOKEN": TOKEN_BOT,
        "MY_CHAT_ID": MY_CHAT_ID,
        "GROUP_INVITE_LINK": GROUP_INVITE_LINK,
        "GROUP_CHAT_ID": GROUP_CHAT_ID
    }
    
    # Verifica também se os IDs são números válidos
    ids_invalidos = []
    if MY_CHAT_ID and not isinstance(MY_CHAT_ID, int):
        ids_invalidos.append("MY_CHAT_ID")
    if GROUP_CHAT_ID and not isinstance(GROUP_CHAT_ID, int):
        ids_invalidos.append("GROUP_CHAT_ID")
    
    faltando = [nome for nome, valor in variaveis_necessarias.items() if not valor]
    config_ok = len(faltando) == 0 and len(ids_invalidos) == 0
    
    # Em produção, imprime erro e para se não estiver OK (a menos que silencioso)
    if not DEBUG and not config_ok and not silencioso:
        erros = []
        if faltando:
            erros.append(f"Variáveis faltando: {', '.join(faltando)}")
        if ids_invalidos:
            erros.append(f"IDs inválidos: {', '.join(ids_invalidos)}")
        
        print(f"❌ ERRO CRÍTICO: Configuração inválida!")
        for erro in erros:
            print(f"   - {erro}")
        print("\n💡 Configure as variáveis no Railway ou arquivo .env")
        sys.exit(1)
    
    return config_ok, faltando, ids_invalidos

def get_mercadopago_sdk():
    """
    Retorna a instância do SDK do Mercado Pago
    Inicializa sob demanda (lazy loading) na primeira chamada
    
    Returns:
        mercadopago.SDK: Instância configurada do SDK
        
    Raises:
        Exception: Se não for possível inicializar o SDK
    """
    global _sdk, _mp_inicializado
    
    # Lazy loading - só inicializa quando realmente precisar
    if not _mp_inicializado:
        if not _inicializar_mercadopago():
            raise Exception(
                "SDK do Mercado Pago não pode ser inicializado! "
                "Verifique se MERCADOPAGO_ACCESS_TOKEN está configurado corretamente."
            )
    
    if not _sdk:
        raise Exception("SDK do Mercado Pago não está disponível!")
    
    return _sdk

def sdk_disponivel():
    """
    Verifica se o SDK pode ser inicializado sem realmente fazê-lo
    
    Returns:
        bool: True se as credenciais estão disponíveis
    """
    return bool(TOKEN_MERCADOPAGO)

def mascara_token(token, prefixo_visivel=3, sufixo_visivel=4):
    """
    Mascara um token mostrando apenas início e fim
    
    Args:
        token: Token a ser mascarado
        prefixo_visivel: Quantos caracteres mostrar no início
        sufixo_visivel: Quantos caracteres mostrar no fim
    
    Returns:
        str: Token mascarado ou None
    """
    if not token:
        return None
    
    if len(token) <= (prefixo_visivel + sufixo_visivel):
        return "***"
    
    return f"{token[:prefixo_visivel]}...{token[-sufixo_visivel:]}"

# 🎯 Validação inicial em produção (sem inicializar SDK)
if not DEBUG:
    # Apenas valida configuração, não inicializa SDK
    config_ok, _, _ = validar_config(silencioso=False)

# Exporta tudo que outros módulos precisam
__all__ = [
    'TOKEN_BOT',
    'TOKEN_MERCADOPAGO', 
    'PUBLIC_KEY',
    'MY_CHAT_ID',
    'GROUP_INVITE_LINK',
    'GROUP_CHAT_ID',
    'get_mercadopago_sdk',
    'sdk_disponivel',
    'validar_config',
    'DEBUG',
    'AMBIENTE'
]

# ============================================================
# ÁREA DE DEBUG E TESTES - Só roda quando executado diretamente
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print(f"🔧 TESTE DE CONFIGURAÇÃO - Ambiente: {AMBIENTE.upper()}")
    print("="*60)
    
    # Validação detalhada
    config_ok, faltando, ids_invalidos = validar_config(silencioso=True)
    
    print("\n📋 STATUS DAS VARIÁVEIS:")
    print(f"✓ MERCADOPAGO_ACCESS_TOKEN: {'✅ Configurado' if TOKEN_MERCADOPAGO else '❌ Faltando'}")
    print(f"✓ PUBLIC_KEY: {'✅ Configurado' if PUBLIC_KEY else '❌ Faltando'}")
    print(f"✓ TELEGRAM_TOKEN: {'✅ Configurado' if TOKEN_BOT else '❌ Faltando'}")
    print(f"✓ MY_CHAT_ID: {MY_CHAT_ID if MY_CHAT_ID else '❌ Faltando'}")
    print(f"✓ GROUP_INVITE_LINK: {'✅ Configurado' if GROUP_INVITE_LINK else '⚠️ Parcial'}")
    print(f"✓ GROUP_CHAT_ID: {GROUP_CHAT_ID if GROUP_CHAT_ID else '❌ Faltando'}")
    
    # Mostra tokens mascarados apenas em DEBUG
    if DEBUG:
        print("\n🔐 INFORMAÇÕES SENSÍVEIS (MODO DEBUG):")
        if TOKEN_MERCADOPAGO:
            # Mostra apenas últimos 10 caracteres do token MP
            print(f"   Token MP: ***{TOKEN_MERCADOPAGO[-10:]}")
        if PUBLIC_KEY:
            # Mostra public key mascarada
            print(f"   Public Key: {mascara_token(PUBLIC_KEY, 8, 4)}")
        if TOKEN_BOT:
            # Mostra token do bot mascarado
            print(f"   Bot Token: {mascara_token(TOKEN_BOT, 5, 6)}")
    
    if not config_ok:
        print("\n❌ PROBLEMAS ENCONTRADOS:")
        if faltando:
            print(f"   - Variáveis faltando: {', '.join(faltando)}")
        if ids_invalidos:
            print(f"   - IDs com formato inválido: {', '.join(ids_invalidos)}")
        print("\n💡 Solução: Configure as variáveis no arquivo .env")
        sys.exit(1)
    
    print("\n✅ Configuração válida!")
    
    # Teste do SDK disponível
    if sdk_disponivel():
        print("✅ Credenciais do Mercado Pago disponíveis")
        
        # Pergunta se quer testar inicialização
        if DEBUG:
            print("\n🔄 Testando inicialização do SDK (lazy loading)...")
            try:
                sdk_test = get_mercadopago_sdk()
                print("✅ SDK inicializado com sucesso sob demanda!")
                print(f"   Tipo do SDK: {type(sdk_test).__name__}")
                
                # Identifica ambiente do Mercado Pago
                if TOKEN_MERCADOPAGO:
                    if 'APP_USR' in TOKEN_MERCADOPAGO:
                        print("   Ambiente MP: Produção")
                    elif 'TEST' in TOKEN_MERCADOPAGO:
                        print("   Ambiente MP: Teste")
                    else:
                        print("   Ambiente MP: Não identificado")
                
                # Teste adicional - lista métodos de pagamento
                print("\n📝 Testando conexão com API...")
                response = sdk_test.payment_methods().list_all()
                if response.get("status") == 200:
                    metodos = response.get("response", [])
                    print(f"✅ API respondendo! {len(metodos)} métodos de pagamento disponíveis")
                    
                    # Em DEBUG, mostra alguns métodos
                    if metodos and len(metodos) > 0:
                        primeiros = metodos[:3]
                        print("   Exemplos:", ", ".join([m.get("id", "?") for m in primeiros]))
                else:
                    print(f"⚠️ API respondeu com status: {response.get('status')}")
                    
            except Exception as e:
                print(f"❌ Erro ao testar SDK: {e}")
                sys.exit(1)
        else:
            print("ℹ️ SDK não foi inicializado (lazy loading ativo)")
            print("   Será inicializado apenas quando get_mercadopago_sdk() for chamado")
    else:
        print("⚠️ Credenciais do Mercado Pago não encontradas")
        print("   O SDK não poderá ser usado")
    
    print("\n" + "="*60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print(f"   Ambiente: {AMBIENTE}")
    print(f"   Configuração: OK")
    print(f"   SDK MP: {'Disponível (não inicializado)' if sdk_disponivel() else 'Não disponível'}")
    print(f"   Bot Telegram: {'Configurado' if TOKEN_BOT else 'Não configurado'}")
    print(f"   Grupo VIP: {GROUP_CHAT_ID if GROUP_CHAT_ID else 'Não configurado'}")
    print("="*60)
