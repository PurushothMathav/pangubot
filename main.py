#BOT_TOKEN = '8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew'

from telegram import Update, ChatMemberUpdated, MessageEntity
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
bad_words = ["fuck", "sex", "idiot", "stupid"]

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

# Detect bad words and auto-warn only if bot is mentioned
async def detect_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return  # No text to check

    bot_username = (await context.bot.get_me()).username.lower()

    # Check if the bot is mentioned in the message entities
    mentioned = False
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.MENTION:
                mention_text = message.text[entity.offset:entity.offset + entity.length].lower()
                if mention_text == f"@{bot_username}":
                    mentioned = True
                    break

    if not mentioned:
        # Bot not mentioned, don't reply
        return

    text = message.text.lower()
    if any(bad_word in text for bad_word in bad_words):
        user_id = message.from_user.id
        warnings[user_id] = warnings.get(user_id, 0) + 1
        count = warnings[user_id]

        await message.reply_text(f"🚫 Please avoid using bad language! Warning {count}/3")

        if count >= 3:
            await update.effective_chat.ban_member(user_id)
            await message.reply_text("User has been auto-banned after 3 warnings 🚫")
    else:
        await message.reply_text(f"You mentioned me and said: {message.text}")

# Welcome and Goodbye messages
async def welcome_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMemberUpdated = update.chat_member
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user

    if old_status in ("left", "kicked") and new_status == "member":
        await update.effective_chat.send_message(f"👋 Welcome {user.mention_html()}!", parse_mode='HTML')
    elif new_status in ("left", "kicked"):
        await update.effective_chat.send_message(f"👋 Goodbye {user.mention_html()}!", parse_mode='HTML')

def main():
    BOT_TOKEN = "8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))

    # Messages with potential bad words — only respond if bot is mentioned
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_bad_words))

    # Chat member status updates for welcome/goodbye
    app.add_handler(ChatMemberHandler(welcome_goodbye, ChatMemberHandler.CHAT_MEMBER))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()
