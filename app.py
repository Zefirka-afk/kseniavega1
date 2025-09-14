import os
import random
from flask import Flask, request
import telebot

# ============ CONFIG ============
TOKEN = "8183205134:AAEJ95MtbBfYQXOej4ZBxb3GRyS1oz56qlY"   # твой токен
REGISTER_LINK = "http://bit.ly/3WPN2s5"                   # партнёрская ссылка
WEBHOOK_URL = "https://your-app.onrender.com/" + TOKEN    # здесь будет твой Render-адрес + токен

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# сохраняем предпочитаемый язык юзеров
user_languages = {}  # {chat_id: "ru"|"en"}

# ======= TELEGRAM BOT HANDLERS ========

@bot.message_handler(commands=['start'])
def start_message(message):
    lang = "ru" if (message.from_user.language_code or "").startswith("ru") else "en"
    user_languages[message.chat.id] = lang

    if lang == "ru":
        greet = "Привет 👋 Я бот для трейдинга от Daniel Parker!\n\nТвоя персональная ссылка для регистрации:"
        explain = "Перейди по ссылке и зарегистрируйся, я буду присылать уведомления автоматически!"
        btn_signals = "📈 Получить сигналы"
    else:
        greet = "Hello 👋 I am a trading bot from Daniel Parker!\n\nHere is your personal registration link:"
        explain = "Follow the link and register, I'll send you updates automatically!"
        btn_signals = "📈 Get signals"

    ref_link = f"{REGISTER_LINK}?subid={message.chat.id}"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(btn_signals, callback_data=f"signals_{lang}"))

    bot.send_message(message.chat.id, f"{greet}\n\n<b>{ref_link}</b>\n\n{explain}", reply_markup=markup)

@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.send_message(message.chat.id, f"✅ Твой Telegram ID: <b>{message.chat.id}</b>")

# === СИГНАЛЫ ===
def send_random_signal(chat_id, lang):
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "CHF/JPY",
             "NZD/USD", "EUR/JPY", "CAD/CHF", "AUD/JPY", "BTC/USD"]
    pair = random.choice(pairs)
    direction = random.choice(["Вверх ⬆️", "Вниз ⬇️"]) if lang == "ru" else random.choice(["Up ⬆️", "Down ⬇️"])
    expire = random.choice([1, 3, 5])

    if lang == "ru":
        msg = f"🎯 Сигнал:\n{pair}\nНаправление: {direction}\nЭкспирация: {expire} мин."
    else:
        msg = f"🎯 Signal:\n{pair}\nDirection: {direction}\nExpiration: {expire} min."

    bot.send_message(chat_id, msg)

@bot.callback_query_handler(func=lambda c: c.data.startswith("signals_"))
def signals_handler(callback):
    lang = callback.data.split("_")[1]
    chat_id = callback.message.chat.id

    if lang == "ru":
        text = "⏳ У тебя будет 30 секунд, чтобы подготовиться!\nЯ пришлю валютную пару, время экспирации и направление.\n\nГотов?"
        btn_ready = "Готов ✅"
    else:
        text = "⏳ You will have 30 seconds to prepare!\nI will send currency pair, expiration and direction.\n\nReady?"
        btn_ready = "Ready ✅"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(btn_ready, callback_data=f"ready_{lang}"))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ready_"))
def ready_handler(callback):
    lang = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    if lang == "ru":
        bot.send_message(chat_id, "🔍 Я в поиске сигнала...\nПодготовься, зайди на платформу!")
    else:
        bot.send_message(chat_id, "🔍 Searching for signal...\nPrepare and open the platform!")

    send_random_signal(chat_id, lang)


# ======= FLASK API ========

# Вебхук от Telegram -> обновления в бот
@app.route("/" + TOKEN, methods=['POST'])
def telegram_webhook():
    json_str = request.stream.read().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def webhook_setup():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return "✅ Webhook set", 200


# Постбек от партнерки
@app.route("/postback", methods=["GET", "POST"])
def partner_postback():
    event = request.args.get("event")
    subid = request.args.get("subid")      # Telegram ID (мы подставляли в ref link)
    trader_id = request.args.get("trader_id")
    sumdep = request.args.get("sumdep", "0")

    if not subid:
        return "No subid"
    try:
        chat_id = int(subid)
    except:
        return "Invalid subid"

    lang = user_languages.get(chat_id, "en")

    if event == "reg":
        msg = "✅ Ты успешно зарегистрировался!\nID: {tid}" if lang == "ru" else "✅ You registered!\nTrader ID: {tid}"
        bot.send_message(chat_id, msg.format(tid=trader_id))

    elif event == "FTD":
        msg = "💰 Первый депозит ${dep}! Трейдер ID: {tid}" if lang == "ru" else \
              "💰 First Deposit ${dep}! Trader ID: {tid}"
        bot.send_message(chat_id, msg.format(dep=sumdep, tid=trader_id))
        send_random_signal(chat_id, lang)

    elif event == "dep":
        msg = "➕ Пополнение депозита на ${dep}" if lang == "ru" else "➕ Deposit replenished: ${dep}"
        bot.send_message(chat_id, msg.format(dep=sumdep))

    elif event == "wdr":
        msg = "💵 Запрос на вывод: ${dep}" if lang == "ru" else "💵 Withdrawal request: ${dep}"
        bot.send_message(chat_id, msg.format(dep=sumdep))

    else:
        msg = "📢 Событие: {e}, ID: {tid}, сумма: {dep}" if lang == "ru" else \
              "📢 Event: {e}, Trader: {tid}, Sum: {dep}"
        bot.send_message(chat_id, msg.format(e=event, tid=trader_id, dep=sumdep))

    return "OK"


# ======= MAIN ========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)