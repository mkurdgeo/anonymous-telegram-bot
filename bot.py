import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

waiting_users = []

def get_partner(user_id):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user2 FROM chats WHERE user1=? AND active=1", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_chat(user1, user2):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chats (user1, user2) VALUES (?, ?)", (user1, user2))
    cursor.execute("INSERT INTO chats (user1, user2) VALUES (?, ?)", (user2, user1))
    conn.commit()
    conn.close()

def end_chat(user_id):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE chats SET active=0 WHERE user1=? OR user2=?", (user_id, user_id))
    conn.commit()
    conn.close()

def is_blocked(user_id):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT blocked FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def block_user(user_id):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, blocked) VALUES (?, 1)", (user_id,))
    cursor.execute("UPDATE users SET blocked=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_blocked(user_id):
        await update.message.reply_text("⛔️ شما مسدود شده‌اید.")
        return

    partner = get_partner(user_id)
    if partner:
        await update.message.reply_text("⚠️ شما هم‌اکنون در حال چت هستید.")
        return

    for other_id in waiting_users:
        if not is_blocked(other_id):
            waiting_users.remove(other_id)
            set_chat(user_id, other_id)
            await context.bot.send_message(chat_id=user_id, text="🔗 شما به یک نفر متصل شدید!")
            await context.bot.send_message(chat_id=other_id, text="🔗 شما به یک نفر متصل شدید!")
            return

    waiting_users.append(user_id)
    await update.message.reply_text("⏳ منتظر اتصال به کاربر دیگر هستید...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner = get_partner(user_id)
    end_chat(user_id)
    if partner:
        await context.bot.send_message(chat_id=partner, text="❌ طرف مقابل چت را ترک کرد.")
    await update.message.reply_text("🚫 چت پایان یافت.")

async def next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await start(update, context)

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner = get_partner(user_id)

    if not partner:
        await update.message.reply_text("برای چت ابتدا از /start استفاده کنید.")
        return

    try:
        if update.message.text:
            await context.bot.send_message(chat_id=partner, text=update.message.text)
        elif update.message.voice:
            await context.bot.send_voice(chat_id=partner, voice=update.message.voice.file_id)
        elif update.message.photo:
            await context.bot.send_photo(chat_id=partner, photo=update.message.photo[-1].file_id)
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=partner, sticker=update.message.sticker.file_id)
        else:
            await update.message.reply_text("❗️این نوع پیام پشتیبانی نمی‌شود.")
    except:
        await update.message.reply_text("❌ ارسال پیام ناموفق بود.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner = get_partner(user_id)
    if partner:
        block_user(partner)
        end_chat(user_id)
        await update.message.reply_text("✅ گزارش شما ثبت شد. کاربر مسدود شد.")
        await context.bot.send_message(chat_id=partner, text="⛔️ شما به دلیل گزارش، مسدود شدید.")
    else:
        await update.message.reply_text("❗️در حال حاضر با کسی در چت نیستید.")

if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

    print("🤖 Bot is running...")
    app.run_polling()
