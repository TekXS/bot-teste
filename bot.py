import time
import requests
from datetime import datetime, timedelta
from telegram import Bot

# CONFIGURAÇÕES
TELEGRAM_TOKEN = "8401280909:AAEKpzYXA5iGtKVGiNG7f6JYBD45JEWbFz8"
CHAT_ID = "879825872"
URL = "https://betesporte.bet.br/api/PreMatch/GetEvents?sportId=999&tournamentId=4200000001"

bot = Bot(token=TELEGRAM_TOKEN)
odds_anteriores = {}  # guarda odds antigas e eventos já vistos
ultimo_heartbeat = None
INTERVALO_HEARTBEAT = 2 * 60 * 60  # 2 horas em segundos

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

def verificar_alteracoes():
    global odds_anteriores
    eventos = buscar_eventos()

    for e in eventos:
        chave = e["evento"]
        odd_atual = e["odd"]

        #1️⃣ Nova aposta
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

        # 2️⃣ Odd atualizada
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

def enviar_heartbeat():
    global ultimo_heartbeat
    agora = datetime.now()
    if not ultimo_heartbeat or (agora - ultimo_heartbeat).total_seconds() > INTERVALO_HEARTBEAT:
        msg = (
            "🏠 Betesporte - Bot Ativo\n"
            f"⏰ Última verificação: {agora.strftime('%d/%m %H:%M')}"
        )
        bot.send_message(chat_id=CHAT_ID, text=msg)
        ultimo_heartbeat = agora

def main():
    print("Bot da Betesporte iniciado ✅")
    while True:
        try:
            verificar_alteracoes()
            enviar_heartbeat()
        except Exception as err:
            print("⚠️ Erro:", err)
        time.sleep(20)  # checa a cada 20 segundos

if __name__ == "__main__":
    main()
