import datetime
import mercadopago
import telebot
import time
import threading
import traceback
import json
import os
import logging
import config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# 🔑 Credenciais importadas do config.py
TOKEN_MERCADOPAGO = config.TOKEN_MERCADOPAGO
TOKEN_BOT = config.TOKEN_BOT
MY_CHAT_ID = config.MY_CHAT_ID
GROUP_INVITE_LINK = config.GROUP_INVITE_LINK
GROUP_CHAT_ID = config.GROUP_CHAT_ID

# Arquivo para persistir pagamentos pendentes
ARQUIVO_PENDENTES = "pendentes.json"

# Inicializa SDK e Bot
sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
bot = telebot.TeleBot(TOKEN_BOT)

# Dicionário para armazenar pagamentos pendentes
pagamentos_pendentes = {}

def salvar_pendentes():
    """Salva pagamentos pendentes em arquivo JSON"""
    try:
        with open(ARQUIVO_PENDENTES, "w") as f:
            json.dump(pagamentos_pendentes, f, default=str)
        logging.info(f"Pagamentos pendentes salvos: {len(pagamentos_pendentes)} registros")
    except Exception as e:
        logging.error(f"Erro ao salvar pendentes: {e}")

def carregar_pendentes():
    """Carrega pagamentos pendentes do arquivo JSON"""
    global pagamentos_pendentes
    try:
        if os.path.exists(ARQUIVO_PENDENTES):
            with open(ARQUIVO_PENDENTES, "r") as f:
                pagamentos_pendentes = json.load(f)
            logging.info(f"Carregados {len(pagamentos_pendentes)} pagamentos pendentes")
        else:
            pagamentos_pendentes = {}
            logging.info("Nenhum arquivo de pendentes encontrado, iniciando vazio")
    except Exception as e:
        logging.error(f"Erro ao carregar pendentes: {e}")
        pagamentos_pendentes = {}

def create_payment(value, user_id):
    """Cria um pagamento PIX no Mercado Pago"""
    expire = datetime.datetime.now() + datetime.timedelta(days=1)
    expire = expire.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")

    payment_data = {
        "transaction_amount": int(value),
        "payment_method_id": 'pix',
        "installments": 1,
        "description": f'Acesso ao Grupo - User {user_id}',
        "date_of_expiration": f"{expire}",
        "payer": {
            "email": f"user{user_id}@example.com"
        }
    }

    logging.info(f"Criando pagamento para usuário {user_id}, valor: R$ {value}")
    result = sdk.payment().create(payment_data)
    return result

def verificar_pagamento(payment_id, user_id, chat_id):
    """Verifica o status do pagamento a cada 10 segundos por 10 minutos"""
    tentativas = 0
    max_tentativas = 60  # 10 minutos (60 x 10 segundos)

    logging.info(f"Iniciando verificação do pagamento {payment_id} para usuário {user_id}")

    while tentativas < max_tentativas:
        try:
            # Consulta o status do pagamento
            payment_info = sdk.payment().get(payment_id)

            # Verifica se a resposta é válida
            if not payment_info or 'response' not in payment_info:
                logging.warning(f"Resposta inválida ao verificar pagamento {payment_id}")
                time.sleep(10)
                tentativas += 1
                continue

            status = payment_info['response'].get('status')
            logging.debug(f"Status do pagamento {payment_id}: {status}")

            if status == 'approved':
                # Pagamento aprovado!
                logging.info(f"✅ Pagamento {payment_id} APROVADO para usuário {user_id}")
                bot.send_message(chat_id, "✅ Pagamento aprovado com sucesso!")

                # Tenta aprovar a solicitação no grupo (se o bot for admin)
                try:
                    bot.approve_chat_join_request(GROUP_CHAT_ID, user_id)
                    bot.send_message(chat_id, "🎉 Você foi adicionado ao grupo automaticamente!")
                    logging.info(f"Usuário {user_id} adicionado ao grupo automaticamente")
                except Exception as e:
                    logging.warning(f"Não foi possível aprovar automaticamente usuário {user_id}: {e}")
                    # Se não conseguir aprovar automaticamente, envia o link
                    bot.send_message(chat_id, f"🔗 Acesse o grupo através deste link:\n{GROUP_INVITE_LINK}")

                # Remove dos pendentes e salva
                if payment_id in pagamentos_pendentes:
                    del pagamentos_pendentes[payment_id]
                    salvar_pendentes()
                break

            elif status in ['rejected', 'cancelled']:
                # Pagamento rejeitado ou cancelado
                logging.warning(f"❌ Pagamento {payment_id} foi {status}")
                bot.send_message(chat_id, "❌ Pagamento não foi aprovado. Tente novamente com /pagar")
                if payment_id in pagamentos_pendentes:
                    del pagamentos_pendentes[payment_id]
                    salvar_pendentes()
                break

            # Aguarda 10 segundos antes de verificar novamente
            time.sleep(10)
            tentativas += 1

        except Exception as e:
            logging.error(f"Erro ao verificar pagamento {payment_id}", exc_info=True)
            time.sleep(10)
            tentativas += 1

    # Se expirou o tempo
    if tentativas >= max_tentativas:
        logging.warning(f"⏰ Tempo expirado para pagamento {payment_id}")
        bot.send_message(chat_id, "⏰ Tempo de verificação expirou. Se você pagou, entre em contato com o suporte.")
        if payment_id in pagamentos_pendentes:
            del pagamentos_pendentes[payment_id]
            salvar_pendentes()

@bot.message_handler(commands=['start'])
def cmd_start(message):
    logging.info(f"Comando /start recebido de {message.from_user.id} ({message.from_user.username})")
    welcome_msg = """
🤖 Bem-vindo ao Bot de Pagamentos!

Use /pagar para gerar um PIX de R$ 25 e ter acesso ao grupo VIP.

Após o pagamento, você será adicionado automaticamente!
"""
    bot.send_message(message.from_user.id, welcome_msg)

@bot.message_handler(commands=['pagar'])
def cmd_pagar(message):
    logging.info(f"Comando /pagar recebido de {message.from_user.id} ({message.from_user.username})")

    try:
        # Cria o pagamento
        payment = create_payment(25, message.from_user.id)

        # DEBUG: Mostra a resposta completa do Mercado Pago
        print("DEBUG >>> Resposta bruta do Mercado Pago:", json.dumps(payment, indent=2, ensure_ascii=False))

        # Debug: mostra a resposta completa no console
        logging.debug(f"Resposta do Mercado Pago: {payment}")

        # Validação mais robusta da resposta
        if not payment:
            raise Exception("Resposta vazia do Mercado Pago")

        if 'response' not in payment:
            # Se não há 'response', pode haver erro
            if 'error' in payment:
                raise Exception(f"Erro da API: {payment['error']}")
            else:
                raise Exception(f"Formato de resposta inesperado: {payment}")

        if not payment['response']:
            raise Exception("Response está vazio")

        # Extrai dados do pagamento
        payment_id = payment['response'].get('id')
        if not payment_id:
            raise Exception("ID do pagamento não encontrado na resposta")

        # Verifica se há dados do PIX
        point_of_interaction = payment['response'].get('point_of_interaction')
        if not point_of_interaction:
            raise Exception("Dados do PIX não encontrados")

        transaction_data = point_of_interaction.get('transaction_data')
        if not transaction_data:
            raise Exception("Dados da transação PIX não encontrados")

        pix_copia_cola = transaction_data.get('qr_code')
        if not pix_copia_cola:
            raise Exception("Código PIX copia-cola não gerado")

        # Armazena o pagamento pendente
        pagamentos_pendentes[payment_id] = {
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'timestamp': str(datetime.datetime.now())  # Convertido para string para JSON
        }
        salvar_pendentes()  # Salva imediatamente

        logging.info(f"✅ Pagamento {payment_id} criado com sucesso para usuário {message.from_user.id}")

        # Envia o código PIX
        bot.send_message(message.from_user.id, 
                        "💰 <b>PIX gerado com sucesso!</b>\n\n"
                        "Valor: R$ 25,00\n"
                        "Validade: 24 horas\n\n"
                        "📱 Copie o código abaixo e cole no seu app de pagamento:",
                        parse_mode='HTML')

        bot.send_message(message.from_user.id, 
                        f'<code>{pix_copia_cola}</code>',
                        parse_mode='HTML')

        bot.send_message(message.from_user.id,
                        "⏳ Aguardando confirmação do pagamento...\n"
                        "Assim que o pagamento for confirmado, você será adicionado ao grupo automaticamente!")

        # Inicia verificação em thread separada
        thread = threading.Thread(target=verificar_pagamento, 
                                 args=(payment_id, message.from_user.id, message.chat.id))
        thread.daemon = True
        thread.start()

    except Exception as e:
        import traceback
        erro = traceback.format_exc()
        logging.error(f"Erro detalhado ao criar pagamento para usuário {message.from_user.id}:\n{erro}")
        bot.send_message(message.from_user.id, "❌ Erro interno ao gerar PIX. Verifique os logs.")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Comando para verificar se há pagamento pendente"""
    logging.info(f"Comando /status recebido de {message.from_user.id}")

    user_pendente = False
    for payment_id, info in pagamentos_pendentes.items():
        if info['user_id'] == message.from_user.id:
            user_pendente = True
            break

    if user_pendente:
        bot.send_message(message.from_user.id, "⏳ Você tem um pagamento pendente sendo verificado...")
    else:
        bot.send_message(message.from_user.id, "✅ Você não tem pagamentos pendentes.")

# Comando admin para debug (opcional)
@bot.message_handler(commands=['debug'])
def cmd_debug(message):
    """Comando de debug - apenas para admin"""
    if str(message.from_user.id) == str(MY_CHAT_ID):
        logging.info(f"Comando /debug executado pelo admin")
        info = f"""
🔧 DEBUG INFO:
- Pagamentos pendentes: {len(pagamentos_pendentes)}
- Token MP: {'✅' if TOKEN_MERCADOPAGO else '❌'}
- Token Bot: {'✅' if TOKEN_BOT else '❌'}
- Group ID: {GROUP_CHAT_ID}
- Admin ID: {MY_CHAT_ID}
- Arquivo pendentes: {'✅ Existe' if os.path.exists(ARQUIVO_PENDENTES) else '❌ Não existe'}
"""
        bot.send_message(message.from_user.id, info)
    else:
        logging.warning(f"Tentativa de /debug por usuário não autorizado: {message.from_user.id}")

# Comando para limpar pendentes antigos (admin)
@bot.message_handler(commands=['limpar_pendentes'])
def cmd_limpar_pendentes(message):
    """Remove pagamentos pendentes com mais de 24h"""
    if str(message.from_user.id) == str(MY_CHAT_ID):
        removidos = 0
        agora = datetime.datetime.now()

        # Cria cópia para iterar
        pendentes_copy = list(pagamentos_pendentes.items())

        for payment_id, info in pendentes_copy:
            try:
                # Converte string de volta para datetime
                timestamp = datetime.datetime.fromisoformat(info['timestamp'].split('.')[0])
                diferenca = agora - timestamp

                if diferenca.total_seconds() > 86400:  # 24 horas
                    del pagamentos_pendentes[payment_id]
                    removidos += 1
                    logging.info(f"Removido pagamento antigo: {payment_id}")
            except Exception as e:
                logging.error(f"Erro ao processar pendente {payment_id}: {e}")

        salvar_pendentes()

        msg = f"🧹 Limpeza concluída!\n"
        msg += f"Removidos: {removidos} pagamentos antigos\n"
        msg += f"Restantes: {len(pagamentos_pendentes)} pagamentos"

        bot.send_message(message.from_user.id, msg)
        logging.info(f"Limpeza de pendentes: {removidos} removidos")

if __name__ == "__main__":
    logging.info("="*50)
    logging.info("🤖 Bot iniciado!")
    logging.info(f"📱 Chat ID do Admin: {MY_CHAT_ID}")
    logging.info(f"👥 Grupo ID: {GROUP_CHAT_ID}")
    logging.info(f"🔑 Token MP: {'Configurado' if TOKEN_MERCADOPAGO else 'NÃO CONFIGURADO!'}")
    logging.info("="*50)

    # Carrega pagamentos pendentes salvos
    carregar_pendentes()

    # Verifica se há pagamentos pendentes para retomar
    if pagamentos_pendentes:
        logging.info(f"⚠️ Retomando verificação de {len(pagamentos_pendentes)} pagamentos pendentes")
        for payment_id, info in pagamentos_pendentes.items():
            thread = threading.Thread(
                target=verificar_pagamento, 
                args=(payment_id, info['user_id'], info['chat_id'])
            )
            thread.daemon = True
            thread.start()

    try:
        logging.info("🚀 Bot rodando... (CTRL+C para parar)")
        bot.infinity_polling(timeout=30, long_polling_timeout=20, none_stop=True, interval=1)
    except Exception as e:
        logging.error("Erro crítico no bot", exc_info=True)
