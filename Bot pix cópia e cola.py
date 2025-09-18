import datetime
import mercadopago
import telebot
import time
import threading
import config

# 🔑 Credenciais importadas do config.py
TOKEN_MERCADOPAGO = config.TOKEN_MERCADOPAGO
TOKEN_BOT = config.TOKEN_BOT
MY_CHAT_ID = config.MY_CHAT_ID
GROUP_INVITE_LINK = config.GROUP_INVITE_LINK
GROUP_CHAT_ID = config.GROUP_CHAT_ID

# Inicializa SDK e Bot
sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
bot = telebot.TeleBot(TOKEN_BOT)

# Dicionário para armazenar pagamentos pendentes
pagamentos_pendentes = {}

def create_payment(value, user_id):
    expire = datetime.datetime.now() + datetime.timedelta(days=1)
    expire = expire.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")

    payment_data = {
        "transaction_amount": int(value),
        "payment_method_id": 'pix',
        "installments": 1,
        "description": f'Acesso ao Grupo - User {user_id}',
        "date_of_expiration": f"{expire}",
        "payer": {
            "email": 'email@dominio.xpto'
        }
    }
    result = sdk.payment().create(payment_data)
    return result

def verificar_pagamento(payment_id, user_id, chat_id):
    """Verifica o status do pagamento a cada 10 segundos por 10 minutos"""
    tentativas = 0
    max_tentativas = 60  # 10 minutos (60 x 10 segundos)
    
    while tentativas < max_tentativas:
        try:
            # Consulta o status do pagamento
            payment_info = sdk.payment().get(payment_id)
            status = payment_info['response']['status']
            
            if status == 'approved':
                # Pagamento aprovado!
                bot.send_message(chat_id, "✅ Pagamento aprovado com sucesso!")
                
                # Tenta aprovar a solicitação no grupo (se o bot for admin)
                try:
                    bot.approve_chat_join_request(GROUP_CHAT_ID, user_id)
                    bot.send_message(chat_id, "🎉 Você foi adicionado ao grupo automaticamente!")
                except:
                    # Se não conseguir aprovar automaticamente, envia o link
                    bot.send_message(chat_id, f"🔗 Acesse o grupo através deste link:\n{GROUP_INVITE_LINK}")
                
                # Remove dos pendentes
                if payment_id in pagamentos_pendentes:
                    del pagamentos_pendentes[payment_id]
                break
                
            elif status in ['rejected', 'cancelled']:
                # Pagamento rejeitado ou cancelado
                bot.send_message(chat_id, "❌ Pagamento não foi aprovado. Tente novamente com /pagar")
                if payment_id in pagamentos_pendentes:
                    del pagamentos_pendentes[payment_id]
                break
            
            # Aguarda 10 segundos antes de verificar novamente
            time.sleep(10)
            tentativas += 1
            
        except Exception as e:
            print(f"Erro ao verificar pagamento: {e}")
            time.sleep(10)
            tentativas += 1
    
    # Se expirou o tempo
    if tentativas >= max_tentativas:
        bot.send_message(chat_id, "⏰ Tempo de verificação expirou. Se você pagou, entre em contato com o suporte.")
        if payment_id in pagamentos_pendentes:
            del pagamentos_pendentes[payment_id]

@bot.message_handler(commands=['start'])
def cmd_start(message):
    welcome_msg = """
🤖 Bem-vindo ao Bot de Pagamentos!

Use /pagar para gerar um PIX de R$ 25 e ter acesso ao grupo VIP.

Após o pagamento, você será adicionado automaticamente!
"""
    bot.send_message(message.from_user.id, welcome_msg)

@bot.message_handler(commands=['pagar'])
def cmd_pagar(message):
    try:
        # Cria o pagamento
        payment = create_payment(25, message.from_user.id)
        
        if 'response' in payment and payment['response']:
            payment_id = payment['response']['id']
            pix_copia_cola = payment['response']['point_of_interaction']['transaction_data']['qr_code']
            
            # Armazena o pagamento pendente
            pagamentos_pendentes[payment_id] = {
                'user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'timestamp': datetime.datetime.now()
            }
            
            # Envia o código PIX
            bot.send_message(message.from_user.id, 
                "💰 <b>PIX gerado com sucesso!</b>\n\n"
                "Valor: R$ 25,00\n"
                "Validade: 24 horas\n\n"
                "📱 Copie o código abaixo e cole no seu app de pagamento:",
                parse_mode='HTML')
            
            bot.send_message(message.from_user.id, f'<code>{pix_copia_cola}</code>', parse_mode='HTML')
            
            bot.send_message(message.from_user.id, 
                "⏳ Aguardando confirmação do pagamento...\n"
                "Assim que o pagamento for confirmado, você será adicionado ao grupo automaticamente!")
            
            # Inicia verificação em thread separada
            thread = threading.Thread(target=verificar_pagamento, 
                                    args=(payment_id, message.from_user.id, message.chat.id))
            thread.daemon = True
            thread.start()
            
        else:
            bot.send_message(message.from_user.id, "❌ Erro ao gerar o PIX. Tente novamente.")
            
    except Exception as e:
        print(f"Erro: {e}")
        bot.send_message(message.from_user.id, "❌ Ocorreu um erro. Tente novamente mais tarde.")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Comando para verificar se há pagamento pendente"""
    user_pendente = False
    for payment_id, info in pagamentos_pendentes.items():
        if info['user_id'] == message.from_user.id:
            user_pendente = True
            break
    
    if user_pendente:
        bot.send_message(message.from_user.id, "⏳ Você tem um pagamento pendente sendo verificado...")
    else:
        bot.send_message(message.from_user.id, "✅ Você não tem pagamentos pendentes.")

if __name__ == "__main__":
    print("🤖 Bot iniciado!")
    print(f"📱 Chat ID do Admin: {MY_CHAT_ID}")
    print(f"👥 Grupo ID: {GROUP_CHAT_ID}")
    bot.infinity_polling()
