import os
import sqlite3
from flask import Flask, request
import telebot
import threading

# Конфиги
TOKEN = "8183205134:AAEJ95MtbBfYQXOej4ZBxb3GRyS1oz56qlY"
REGISTER_LINK = "https://u3.shortink.io/register?utm_campaign=825192&utm_source=affiliate&utm_medium=sr&a=PDSrNY9vG5LpeF&ac=1d&code=50START"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# статус 
user_data = {}  

# ДБ
def init_db():
    conn = sqlite3.connect("postbacks.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS postbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT,
                    subid TEXT,
                    trader_id TEXT,
                    sumdep REAL,
                    wdr_sum REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()
    conn.close()

def save_postback(event, subid, trader_id, sumdep=None, wdr_sum=None, status=None):
    conn = sqlite3.connect("postbacks.db")
    c = conn.cursor()
    c.execute("""INSERT INTO postbacks (event, subid, trader_id, sumdep, wdr_sum, status)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (event, subid, trader_id, sumdep, wdr_sum, status))
    conn.commit()
    conn.close()

# Основная логика
@bot.message_handler(commands=['start'])
def start_message(message):
    lang = "ru" if (message.from_user.language_code or "").startswith("ru") else "en"
    user_data[message.chat.id] = {"lang": lang, "registered": False}

    if lang == "ru":
        greet = "Привет 👋 Я бот для трейдинга от Daniel Parker!\n\nВот твоя персональная ссылка для регистрации:"
        explain = "Перейди по ссылке и зарегистрируйся.\n➡️ После подтверждения регистрации я пришлю твой ID и депозит!"
    else:
        greet = "Hello 👋 I am a trading bot from Daniel Parker!\n\nHere is your personal registration link:"
        explain = "Follow the link to register.\n➡️ After confirmation, I'll send you your ID and deposit!"

    ref_link = f"{REGISTER_LINK}&sub_id1={message.chat.id}"
    bot.send_message(message.chat.id, f"{greet}\n\n<b>{ref_link}</b>\n\n{explain}")

@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.send_message(message.chat.id, f"Твой Telegram ID: <b>{message.chat.id}</b>")

#FLASK POSTBACK
@app.route("/postback", methods=["GET", "POST"])
def partner_postback():
    event = request.args.get("event")
    subid = request.args.get("subid")
    trader_id = request.args.get("trader_id")
    sumdep = request.args.get("sumdep")
    wdr_sum = request.args.get("wdr_sum")
    status = request.args.get("status")

    if not subid:
        return "No subid"

    try:
        chat_id = int(subid)
    except:
        return "Invalid subid"
    save_postback(event, subid, trader_id, sumdep, wdr_sum, status)

    userdata = user_data.get(chat_id, {"lang": "en", "registered": False})
    lang = userdata["lang"]

    if event == "reg":
        userdata["registered"] = True
        user_data[chat_id] = userdata
        msg = "✅ Регистрация подтверждена!\nTrader ID: {tid}" if lang == "ru" else "✅ Registration confirmed!\nTrader ID: {tid}"
        bot.send_message(chat_id, msg.format(tid=trader_id))

    elif event == "FTD":
        userdata["registered"] = True
        user_data[chat_id] = userdata
        msg = "💰 Первый депозит ${dep}! Trader ID: {tid}" if lang == "ru" else "💰 First Deposit ${dep}! Trader ID: {tid}"
        bot.send_message(chat_id, msg.format(dep=sumdep, tid=trader_id))

        btn_text = "📊 Личный кабинет" if lang == "ru" else "📊 Personal account"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(btn_text, url=REGISTER_LINK))
        follow_msg = "Перейди в личный кабинет для управления счётом 👇" if lang == "ru" else "Go to your personal account to manage your account 👇"
        bot.send_message(chat_id, follow_msg, reply_markup=markup)

    elif event == "dep":
        msg = "➕ Пополнение депозита на ${dep}" if lang == "ru" else "➕ Deposit replenished: ${dep}"
        bot.send_message(chat_id, msg.format(dep=sumdep))

    elif event == "wdr":
        msg = "💵 Запрос на вывод: ${dep}" if lang == "ru" else "💵 Withdrawal request: ${dep}"
        bot.send_message(chat_id, msg.format(dep=wdr_sum))

    else:
        msg = "📢 Событие: {e}, Trader: {tid}, сумма: {dep}" if lang == "ru" else "📢 Event: {e}, Trader: {tid}, Sum: {dep}"
        bot.send_message(chat_id, msg.format(e=event, tid=trader_id, dep=sumdep))

    return "OK"

# Запуск
if __name__ == "__main__":
    init_db()

    def run_bot():
        bot.infinity_polling()

    threading.Thread(target=run_bot).start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)