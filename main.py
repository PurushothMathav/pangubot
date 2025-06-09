import logging
import os
import time
import json
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, ChatMemberHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Configuration ---
# IMPORTANT: Replace "YOUR_BOT_TOKEN" with the token you get from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN") 
MAX_WARNINGS = 3  # Number of warnings before a user is banned
BAD_WORDS = ["damn", "hell", "crap", "bloody","shit", "ass", "bitch", "piss", "dick","fuck", "fucking", "fucker", "motherfucker", "cocksucker", "cunt","nigger", "faggot", "retard","wtf"] # Add words you want to filter

# --- Data Persistence ---
# Using a simple JSON file for data persistence.
# In a production environment, consider using a database like SQLite.
DB_FILE = "bot_database.json"

def load_data():
    """Loads data from the JSON file."""
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default structure if file doesn't exist or is empty
        return {"warnings": {}, "stats": {}}

def save_data(data):
    """Saves data to the JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data at startup
bot_data = load_data()


# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- Helper Functions ---
async def is_user_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if a user is an administrator in a given chat."""
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status for user {user_id} in chat {chat_id}: {e}")
        return False
        
# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am a full-featured group management bot. "
        "Add me to a group and make me an admin to see my powers!",
    )

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kicks a user from the group."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("This command only works in groups.")
        return

    if not await is_user_admin(chat.id, user.id, context):
        await update.message.reply_text("You must be an admin to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user's message to kick them.")
        return

    user_to_kick = update.message.reply_to_message.from_user
    
    try:
        await context.bot.kick_chat_member(chat_id=chat.id, user_id=user_to_kick.id)
        await update.message.reply_text(f"Successfully kicked {user_to_kick.mention_html()}.", parse_mode=ParseMode.HTML)
        logger.info(f"Admin {user.id} kicked {user_to_kick.id} from chat {chat.id}")
    except Exception as e:
        await update.message.reply_text(f"Failed to kick user. Reason: {e}")
        logger.error(f"Failed to kick user {user_to_kick.id} in chat {chat.id}: {e}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bans a user from the group."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("This command only works in groups.")
        return

    if not await is_user_admin(chat.id, user.id, context):
        await update.message.reply_text("You must be an admin to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user's message to ban them.")
        return

    user_to_ban = update.message.reply_to_message.from_user
    
    try:
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_to_ban.id)
        await update.message.reply_text(f"Successfully banned {user_to_ban.mention_html()}.", parse_mode=ParseMode.HTML)
        logger.info(f"Admin {user.id} banned {user_to_ban.id} from chat {chat.id}")
    except Exception as e:
        await update.message.reply_text(f"Failed to ban user. Reason: {e}")
        logger.error(f"Failed to ban user {user_to_ban.id} in chat {chat.id}: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unbans a user from the group."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("This command only works in groups.")
        return

    if not await is_user_admin(chat.id, user.id, context):
        await update.message.reply_text("You must be an admin to use this command.")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return

    try:
        user_id_to_unban = int(context.args[0])
        await context.bot.unban_chat_member(chat_id=chat.id, user_id=user_id_to_unban)
        await update.message.reply_text(f"Successfully unbanned user {user_id_to_unban}.")
        logger.info(f"Admin {user.id} unbanned {user_id_to_unban} from chat {chat.id}")
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid User ID.")
    except Exception as e:
        await update.message.reply_text(f"Failed to unban user. Reason: {e}")
        logger.error(f"Failed to unban user in chat {chat.id}: {e}")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Warns a user. If warnings exceed MAX_WARNINGS, the user is banned."""
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == 'private':
        await update.message.reply_text("This command only works in groups.")
        return

    if not await is_user_admin(chat.id, user.id, context):
        await update.message.reply_text("You must be an admin to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user's message to warn them.")
        return
    
    user_to_warn = update.message.reply_to_message.from_user
    chat_id_str = str(chat.id)
    user_id_str = str(user_to_warn.id)

    # Initialize warnings if not present
    if chat_id_str not in bot_data["warnings"]:
        bot_data["warnings"][chat_id_str] = {}
    if user_id_str not in bot_data["warnings"][chat_id_str]:
        bot_data["warnings"][chat_id_str][user_id_str] = 0

    # Increment warning count
    bot_data["warnings"][chat_id_str][user_id_str] += 1
    save_data(bot_data)
    
    current_warnings = bot_data["warnings"][chat_id_str][user_id_str]

    if current_warnings >= MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_to_warn.id)
            await update.message.reply_text(
                f"{user_to_warn.mention_html()} has reached {current_warnings}/{MAX_WARNINGS} warnings and has been banned.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Banned {user_to_warn.id} from {chat.id} due to max warnings.")
            # Reset warnings after ban
            bot_data["warnings"][chat_id_str][user_id_str] = 0
            save_data(bot_data)
        except Exception as e:
            await update.message.reply_text(f"Could not ban user. Reason: {e}")
            logger.error(f"Failed to auto-ban user {user_to_warn.id} in chat {chat.id}: {e}")
    else:
        await update.message.reply_text(
            f"{user_to_warn.mention_html()} has been warned. "
            f"This is warning {current_warnings}/{MAX_WARNINGS}.",
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Admin {user.id} warned {user_to_warn.id} in chat {chat.id}.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays group statistics."""
    chat = update.effective_chat
    chat_id_str = str(chat.id)
    
    if chat.type == 'private':
        await update.message.reply_text("This command only works in groups.")
        return

    try:
        member_count = await context.bot.get_chat_member_count(chat.id)
        
        stats_text = f"<b>📊 Group Statistics for {chat.title}</b>\n\n"
        stats_text += f"Total Members: {member_count}\n"

        if chat_id_str in bot_data.get("stats", {}):
            chat_stats = bot_data["stats"][chat_id_str]
            stats_text += f"New Members Today: {chat_stats.get('joins_today', 0)}\n"
            stats_text += f"Members Left Today: {chat_stats.get('leaves_today', 0)}\n"

        await update.message.reply_html(stats_text)

    except Exception as e:
        await update.message.reply_text(f"Could not retrieve stats. Reason: {e}")
        logger.error(f"Failed to get stats for chat {chat.id}: {e}")

# --- Message Handlers ---

async def content_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Filters messages for links and bad words."""
    message = update.message
    text = message.text.lower() if message.text else ""

    # Filter for links
    if 'http' in text or 't.me' in text or 'www' in text:
        try:
            await message.delete()
            await message.reply_text(
                f"{message.from_user.mention_html()}, sending links is not allowed here.",
                parse_mode=ParseMode.HTML,
            )
            logger.info(f"Deleted a message with a link from {message.from_user.id} in chat {message.chat.id}")
        except Exception as e:
            logger.error(f"Failed to delete link message in chat {message.chat.id}: {e}")
        return # Stop processing if a link is found

    # Filter for bad words
    if any(word in text for word in BAD_WORDS):
        try:
            await message.delete()
            await message.reply_text(
                f"{message.from_user.mention_html()}, please watch your language.",
                parse_mode=ParseMode.HTML,
            )
            logger.info(f"Deleted a message with a bad word from {message.from_user.id} in chat {message.chat.id}")
        except Exception as e:
            logger.error(f"Failed to delete bad word message in chat {message.chat.id}: {e}")

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles direct messages to the bot for AI conversation."""
    user_input = update.message.text
    
    # Placeholder for a real AI API call
    # In a real implementation, you would send user_input to an AI service (like OpenAI, Gemini, etc.)
    # and get a response.
    ai_response = f"You said: '{user_input}'. I'm still learning to have conversations!"
    
    await update.message.reply_text(ai_response)
    logger.info(f"Replied to a direct message from {update.effective_user.id}")


# --- Member Update Handlers ---

def extract_status_change(chat_member_update: ChatMemberUpdated):
    """Extracts member status changes."""
    status_change = chat_member_update.difference().get("status")
    if status_change is None:
        return None
    old_status, new_status = status_change
    was_member = old_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    is_member = new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    return was_member, is_member

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks when the bot is added to or removed from a chat."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result
    chat = update.effective_chat
    if not was_member and is_member:
        logger.info(f"Bot was added to chat {chat.title} ({chat.id})")
    elif was_member and not is_member:
        logger.info(f"Bot was removed from chat {chat.title} ({chat.id})")

async def welcome_and_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new members and says goodbye to those who leave, also updates stats."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    member_name = update.chat_member.new_chat_member.user.mention_html()
    chat = update.chat_member.chat
    chat_id_str = str(chat.id)

    # Initialize stats if not present
    if chat_id_str not in bot_data["stats"]:
        bot_data["stats"][chat_id_str] = {"joins_today": 0, "leaves_today": 0}
        
    # Welcome Message and Stats Update
    if not was_member and is_member:
        bot_data["stats"][chat_id_str]["joins_today"] = bot_data["stats"][chat_id_str].get("joins_today", 0) + 1
        await context.bot.send_message(
            chat.id,
            f"Welcome {member_name} to <b>{chat.title}</b>! We're glad you're here.",
            parse_mode=ParseMode.HTML,
        )
        logger.info(f"{member_name} joined chat {chat.title} ({chat.id})")
        
    # Goodbye Message and Stats Update
    elif was_member and not is_member:
        bot_data["stats"][chat_id_str]["leaves_today"] = bot_data["stats"][chat_id_str].get("leaves_today", 0) + 1
        await context.bot.send_message(
            chat.id,
            f"Goodbye {member_name}. We're sad to see you go.",
            parse_mode=ParseMode.HTML,
        )
        logger.info(f"{member_name} left or was removed from chat {chat.title} ({chat.id})")
        
    save_data(bot_data)

# --- Main Bot Logic ---

def main() -> None:
    """Start the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("FATAL ERROR: Please replace 'YOUR_BOT_TOKEN' in the script with your bot token.")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Registering Handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("warn", warn_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Member update handlers
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(welcome_and_goodbye, ChatMemberHandler.CHAT_MEMBER))

    # Message handlers
    # Filters for links or bad words in group chats
    application.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND) & filters.ChatType.GROUPS,
        content_filter_handler
    ))
    # Filter for AI chat in private messages
    application.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND) & filters.ChatType.PRIVATE,
        ai_chat_handler
    ))
    
    # Start the Bot
    print("Full-featured bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
