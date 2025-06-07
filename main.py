#BOT_TOKEN = '8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew'

from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler
)

# In-memory warning counter (use a database for production)
warnings = {}

# List of bad words (add more as needed)
bad_words = ["badword1", "badword2", "idiot", "stupid"]

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot 🤖")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands:\n/start\n/help\n/warn\n/ban\n/unban")

# Warn a user (custom counter)
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        warnings[user_id] = warnings.get(user_id, 0) + 1
        count = warnings[user_id]
        await update.message.reply_text(f"User warned ⚠️ Total warnings: {count}")

        # Auto-ban after 3 warnings
        if count >= 3:
            await update.effective_chat.ban_member(user_id)
            await update.message.reply_text("User has been auto-banned after 3 warnings 🚫")
    else:
        await update.message.reply_text("Reply to a user's message to warn them.")

# Ban a user
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        await update.effective_chat.ban_member(user_id)
        await update.message.reply_text("User has been banned 🚫")
    else:
        await update.message.reply_text("Reply to a user's message to ban them.")

# Unban a user
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        await update.effective_chat.unban_member(user_id)
        await update.message.reply_text("User has been unbanned ✅")
    else:
        await update.message.reply_text("Reply to a user's message to unban them.")

# Detect bad words
async def detect_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(bad_word in text for bad_word in bad_words):
        await update.message.reply_text("🚫 Please avoid using bad language!")
    else:
        await update.message.reply_text(f"You said: {update.message.text}")

# Welcome and Goodbye messages
async def welcome_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user

    if old_status in ("left", "kicked") and new_status == "member":
        await update.effective_chat.send_message(f"👋 Welcome {user.mention_html()}!", parse_mode='HTML')
    elif new_status in ("left", "kicked"):
        await update.effective_chat.send_message(f"👋 Goodbye {user.mention_html()}!", parse_mode='HTML')

# Main function
def main():
    BOT_TOKEN = "8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_bad_words))
    app.add_handler(ChatMemberHandler(welcome_goodbye, ChatMemberHandler.CHAT_MEMBER))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()
