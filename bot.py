import time
import requests
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# CONFIGURAÇÕES
TELEGRAM_TOKEN = "8401280909:AAEKpzYXA5iGtKVGiNG7f6JYBD45JEWbFz8"
CHAT_ID = "879825872"
URL = "https://betesporte.bet.br/api/PreMatch/GetEvents?sportId=999&tournamentId=4200000001"

odds_anteriores = {}  # guarda odds antigas e eventos já vistos

# Função para buscar eventos no JSON da Betesporte
def buscar_eventos():
    r = requests.get(URL)
    data = r.json()
    eventos = []

    for country in data["data"]["countries"]:
        for tournament in country["tournaments"]:
            for event in tournament["events"]:
                nome_evento = event["homeTeamName"]
                data_evento_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                data_brasilia = data_evento_utc - timedelta(hours=3)
                data_formatada = data_brasilia.strftime("%d/%m %H:%M")

                for market in event["markets"]:
                    nome_mercado = market["name"]
                    for option in market["options"]:
                        odd = option["odd"]
                        eventos.append({
                            "evento": nome_evento,
                            "mercado": nome_mercado,
                            "odd": odd,
                            "data": data_formatada
                        })
    return eventos

# Verifica novas apostas ou odds atualizadas
def verificar_alteracoes(bot: Bot):
    global odds_anteriores
    eventos = buscar_eventos()

    for e in eventos:
        chave = e["evento"]
        odd_atual = e["odd"]

        # Nova aposta
        if chave not in odds_anteriores:
            msg = (
                "🏠 Betesporte - Nova Aposta\n"
                f"⚽️ Evento: {e['evento']}\n"
                f"🔢 Odd: {e['odd']}\n"
                f"📅 {e['data']}"
            )
            bot.send_message(chat_id=CHAT_ID, text=msg)
            odds_anteriores[chave] = odd_atual
            continue

        # Odd atualizada
        odd_antiga = odds_anteriores[chave]
        if odd_antiga != odd_atual:
            msg = (
                "🏠 Betesporte - Odd Atualizada\n"
                f"⚽️ Evento: {e['evento']}\n"
                f"🔄 Odd Atualizada: {e['odd']}\n"
                f"📅 {e['data']}"
            )
            bot.send_message(chat_id=CHAT_ID, text=msg)
            odds_anteriores[chave] = odd_atual

# Função chamada quando alguém envia /odds
def comando_odds(update: Update, context: CallbackContext):
    eventos = buscar_eventos()
    if not eventos:
        update.message.reply_text("Nenhuma aposta disponível no momento.")
        return

    msg = "🏠 Betesporte - Odds Disponíveis:\n\n"
    for e in eventos:
        msg += f"⚽️ {e['evento']}\n"
        msg += f"🔢 Odd: {e['odd']}\n"
        msg += f"📅 {e['data']}\n\n"
    update.message.reply_text(msg)

# Função principal
def main():
    print("Bot da Betesporte iniciado ✅")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Comando /odds
    dispatcher.add_handler(CommandHandler("odds", comando_odds))

    # Inicia o bot
    updater.start_polling()

    # Loop de monitoramento de novas apostas / odds
    while True:
        try:
            verificar_alteracoes(updater.bot)
        except Exception as e:
            print("⚠️ Erro:", e)
        time.sleep(20)  # checa a cada 20 segundos

if __name__ == "__main__":
    main()
