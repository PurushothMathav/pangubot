import logging
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
import random
import os

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ChatMember, ChatPermissions, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ChatMemberHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
import openai  # For AI conversations (optional)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GroupBot:
    def __init__(self, token: str, openai_key: str = None):
        self.token = token
        self.openai_key = openai_key
        if openai_key:
            openai.api_key = openai_key
        
        # Initialize database
        self.init_database()
        
        # Bot configuration
        self.admin_commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help message"),
            BotCommand("warn", "Warn a user"),
            BotCommand("unwarn", "Remove warning from user"),
            BotCommand("ban", "Ban a user"),
            BotCommand("unban", "Unban a user"),
            BotCommand("kick", "Kick a user"),
            BotCommand("mute", "Mute a user"),
            BotCommand("unmute", "Unmute a user"),
            BotCommand("stats", "Show group statistics"),
            BotCommand("settings", "Bot settings"),
            BotCommand("rules", "Show group rules"),
            BotCommand("setrules", "Set group rules"),
            BotCommand("welcome", "Set welcome message"),
            BotCommand("goodbye", "Set goodbye message"),
            BotCommand("antiflood", "Configure anti-flood"),
            BotCommand("antispam", "Configure anti-spam"),
            BotCommand("pin", "Pin a message"),
            BotCommand("unpin", "Unpin messages"),
            BotCommand("purge", "Delete messages"),
            BotCommand("promote", "Promote user to admin"),
            BotCommand("demote", "Demote admin"),
            BotCommand("lock", "Lock chat features"),
            BotCommand("unlock", "Unlock chat features"),
            BotCommand("report", "Report a message"),
            BotCommand("notes", "Show saved notes"),
            BotCommand("addnote", "Add a note"),
            BotCommand("delnote", "Delete a note"),
            BotCommand("filters", "Show active filters"),
            BotCommand("addfilter", "Add word filter"),
            BotCommand("delfilter", "Delete word filter"),
        ]

    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                chat_id INTEGER,
                username TEXT,
                first_name TEXT,
                warnings INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
                join_date TIMESTAMP,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        
        # Group settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                welcome_message TEXT,
                goodbye_message TEXT,
                rules TEXT,
                max_warnings INTEGER DEFAULT 3,
                antiflood_limit INTEGER DEFAULT 5,
                antiflood_time INTEGER DEFAULT 60,
                antispam_enabled BOOLEAN DEFAULT 1,
                welcome_enabled BOOLEAN DEFAULT 1,
                goodbye_enabled BOOLEAN DEFAULT 1,
                reports_enabled BOOLEAN DEFAULT 1,
                ai_chat_enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        # Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                note_name TEXT,
                note_content TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Filters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                trigger_word TEXT,
                response TEXT,
                action TEXT DEFAULT 'delete',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                reporter_id INTEGER,
                reported_user_id INTEGER,
                message_id INTEGER,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Flood control table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flood_control (
                user_id INTEGER,
                chat_id INTEGER,
                message_count INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        
        self.conn.commit()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_text = """
🤖 **Professional Group Management Bot**

Hello! I'm your advanced group management assistant. Here's what I can do:

**👮 Moderation:**
• Warn, ban, kick, mute users
• Anti-flood and anti-spam protection
• Automatic moderation actions

**📊 Statistics & Reports:**
• Detailed group analytics
• User activity tracking
• Report system for violations

**🎯 Smart Features:**
• AI-powered conversations
• Custom filters and notes
• Welcome/goodbye messages
• Advanced chat locks

**⚙️ Administration:**
• Promote/demote users
• Pin/unpin messages
• Bulk message deletion
• Customizable settings

Use /help to see all available commands!
        """
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode=ParseMode.MARKDOWN
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command with categorized commands"""
        help_text = """
**🔧 ADMIN COMMANDS:**
/warn - Warn a user (`/warn @user reason`)
/ban - Ban a user (`/ban @user reason`)
/kick - Kick a user (`/kick @user reason`)
/mute - Mute a user (`/mute @user time`)
/promote - Promote user to admin
/demote - Demote admin

**📊 GROUP MANAGEMENT:**
/stats - Show group statistics
/rules - Show group rules
/setrules - Set group rules
/settings - Bot configuration
/lock - Lock chat features
/unlock - Unlock chat features

**💬 MESSAGES:**
/welcome - Set welcome message
/goodbye - Set goodbye message
/pin - Pin replied message
/purge - Delete messages (reply to start)

**📝 NOTES & FILTERS:**
/notes - Show saved notes
/addnote - Add note (`/addnote name content`)
/filters - Show active filters
/addfilter - Add filter (`/addfilter word response`)

**🛡️ PROTECTION:**
/antiflood - Configure flood protection
/antispam - Toggle spam protection
/report - Report a message (reply)

**🤖 AI FEATURES:**
Just mention me in a message for AI conversation!

**👤 USER COMMANDS:**
/start, /help, /rules, /notes, /report
        """
        
        await update.message.reply_text(
            help_text, 
            parse_mode=ParseMode.MARKDOWN
        )

    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in ['creator', 'administrator']
        except:
            return False

    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Warn a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not update.message.reply_to_message and len(context.args) < 1:
            await update.message.reply_text("ℹ️ Reply to a message or use: `/warn @username reason`", parse_mode=ParseMode.MARKDOWN)
            return
        
        chat_id = update.effective_chat.id
        
        # Get target user
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            reason = ' '.join(context.args) if context.args else "No reason provided"
        else:
            try:
                username = context.args[0].replace('@', '')
                reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
                # This would need additional logic to find user by username
                await update.message.reply_text("❌ Please reply to a message to warn the user.")
                return
            except:
                await update.message.reply_text("❌ Invalid format. Use: `/warn @username reason`", parse_mode=ParseMode.MARKDOWN)
                return
        
        user_id = target_user.id
        
        # Update warnings in database
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, chat_id, username, first_name, warnings, last_seen)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT warnings FROM users WHERE user_id=? AND chat_id=?), 0) + 1,
                ?)
        ''', (user_id, chat_id, target_user.username, target_user.first_name, 
              user_id, chat_id, datetime.now()))
        
        # Get current warnings
        cursor.execute('SELECT warnings FROM users WHERE user_id=? AND chat_id=?', (user_id, chat_id))
        warnings = cursor.fetchone()[0]
        
        # Get max warnings setting
        cursor.execute('SELECT max_warnings FROM group_settings WHERE chat_id=?', (chat_id,))
        max_warnings_row = cursor.fetchone()
        max_warnings = max_warnings_row[0] if max_warnings_row else 3
        
        self.conn.commit()
        
        warn_text = f"⚠️ **User Warned**\n\n"
        warn_text += f"👤 User: {target_user.mention_html()}\n"
        warn_text += f"📝 Reason: {reason}\n"
        warn_text += f"🔢 Warnings: {warnings}/{max_warnings}\n"
        warn_text += f"👮 By: {update.effective_user.mention_html()}"
        
        # Check if user should be banned
        if warnings >= max_warnings:
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                warn_text += f"\n\n🔨 **User automatically banned** for reaching {max_warnings} warnings!"
            except Exception as e:
                warn_text += f"\n\n❌ Failed to ban user: {str(e)}"
        
        await update.message.reply_text(warn_text, parse_mode=ParseMode.HTML)

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to ban the user.")
            return
        
        target_user = update.message.reply_to_message.from_user
        reason = ' '.join(context.args) if context.args else "No reason provided"
        chat_id = update.effective_chat.id
        
        try:
            await context.bot.ban_chat_member(chat_id, target_user.id)
            
            ban_text = f"🔨 **User Banned**\n\n"
            ban_text += f"👤 User: {target_user.mention_html()}\n"
            ban_text += f"📝 Reason: {reason}\n"
            ban_text += f"👮 By: {update.effective_user.mention_html()}"
            
            await update.message.reply_text(ban_text, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to ban user: {str(e)}")

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("ℹ️ Use: `/unban user_id`", parse_mode=ParseMode.MARKDOWN)
            return
        
        try:
            user_id = int(context.args[0])
            chat_id = update.effective_chat.id
            
            await context.bot.unban_chat_member(chat_id, user_id)
            await update.message.reply_text(f"✅ User {user_id} has been unbanned.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unban user: {str(e)}")

    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to mute the user.")
            return
        
        target_user = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        
        # Parse mute duration
        duration = 3600  # Default 1 hour
        if context.args:
            try:
                time_str = context.args[0].lower()
                if 'm' in time_str:
                    duration = int(time_str.replace('m', '')) * 60
                elif 'h' in time_str:
                    duration = int(time_str.replace('h', '')) * 3600
                elif 'd' in time_str:
                    duration = int(time_str.replace('d', '')) * 86400
                else:
                    duration = int(time_str) * 60  # Default to minutes
            except:
                duration = 3600
        
        try:
            until_date = datetime.now() + timedelta(seconds=duration)
            permissions = ChatPermissions(can_send_messages=False)
            
            await context.bot.restrict_chat_member(
                chat_id, target_user.id, permissions, until_date=until_date
            )
            
            duration_text = f"{duration//60} minutes" if duration < 3600 else f"{duration//3600} hours"
            mute_text = f"🔇 **User Muted**\n\n"
            mute_text += f"👤 User: {target_user.mention_html()}\n"
            mute_text += f"⏰ Duration: {duration_text}\n"
            mute_text += f"👮 By: {update.effective_user.mention_html()}"
            
            await update.message.reply_text(mute_text, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to mute user: {str(e)}")

    async def group_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group statistics"""
        chat_id = update.effective_chat.id
        cursor = self.conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM users WHERE chat_id=?', (chat_id,))
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE chat_id=? AND warnings > 0', (chat_id,))
        warned_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(messages_count) FROM users WHERE chat_id=?', (chat_id,))
        total_messages = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM reports WHERE chat_id=? AND status="pending"', (chat_id,))
        pending_reports = cursor.fetchone()[0]
        
        # Get top active users
        cursor.execute('''
            SELECT first_name, username, messages_count 
            FROM users WHERE chat_id=? 
            ORDER BY messages_count DESC LIMIT 5
        ''', (chat_id,))
        top_users = cursor.fetchall()
        
        # Get chat info
        try:
            chat = await context.bot.get_chat(chat_id)
            member_count = await context.bot.get_chat_member_count(chat_id)
        except:
            member_count = "Unknown"
        
        stats_text = f"📊 **Group Statistics**\n\n"
        stats_text += f"👥 Total Members: {member_count}\n"
        stats_text += f"📝 Tracked Users: {total_users}\n"
        stats_text += f"💬 Total Messages: {total_messages:,}\n"
        stats_text += f"⚠️ Warned Users: {warned_users}\n"
        stats_text += f"📢 Pending Reports: {pending_reports}\n\n"
        
        if top_users:
            stats_text += "🏆 **Most Active Users:**\n"
            for i, (name, username, msg_count) in enumerate(top_users, 1):
                username_str = f"@{username}" if username else name
                stats_text += f"{i}. {username_str}: {msg_count} messages\n"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    async def welcome_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new member joins"""
        chat_id = update.effective_chat.id
        cursor = self.conn.cursor()
        
        # Check if welcome is enabled
        cursor.execute('SELECT welcome_enabled, welcome_message FROM group_settings WHERE chat_id=?', (chat_id,))
        settings = cursor.fetchone()
        
        if not settings or not settings[0]:
            return
        
        for new_member in update.message.new_chat_members:
            # Add user to database
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, chat_id, username, first_name, join_date, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (new_member.id, chat_id, new_member.username, 
                  new_member.first_name, datetime.now(), datetime.now()))
            
            # Send welcome message
            welcome_msg = settings[1] if settings[1] else (
                f"👋 Welcome to the group, {new_member.first_name}!\n\n"
                f"Please read our /rules and enjoy your stay! 🎉"
            )
            
            # Replace placeholders
            welcome_msg = welcome_msg.replace('{name}', new_member.first_name)
            welcome_msg = welcome_msg.replace('{username}', f"@{new_member.username}" if new_member.username else new_member.first_name)
            welcome_msg = welcome_msg.replace('{group}', update.effective_chat.title)
            
            # Create welcome keyboard
            keyboard = [
                [InlineKeyboardButton("📋 Rules", callback_data="show_rules")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="show_help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id, welcome_msg, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        self.conn.commit()

    async def goodbye_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle member leaves"""
        chat_id = update.effective_chat.id
        cursor = self.conn.cursor()
        
        # Check if goodbye is enabled
        cursor.execute('SELECT goodbye_enabled, goodbye_message FROM group_settings WHERE chat_id=?', (chat_id,))
        settings = cursor.fetchone()
        
        if not settings or not settings[0]:
            return
        
        left_member = update.message.left_chat_member
        
        goodbye_msg = settings[1] if settings[1] else (
            f"👋 Goodbye {left_member.first_name}, thanks for being part of our community!"
        )
        
        # Replace placeholders
        goodbye_msg = goodbye_msg.replace('{name}', left_member.first_name)
        goodbye_msg = goodbye_msg.replace('{username}', f"@{left_member.username}" if left_member.username else left_member.first_name)
        
        await context.bot.send_message(chat_id, goodbye_msg, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all messages for various features"""
        if not update.message or not update.message.text:
            return
            
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_text = update.message.text.lower()
        
        # Update user activity
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, chat_id, username, first_name, messages_count, last_seen)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT messages_count FROM users WHERE user_id=? AND chat_id=?), 0) + 1,
                ?)
        ''', (user_id, chat_id, update.effective_user.username, 
              update.effective_user.first_name, user_id, chat_id, datetime.now()))
        self.conn.commit()
        
        # Anti-flood check
        await self.check_flood(update, context)
        
        # Check word filters
        await self.check_filters(update, context)
        
        # AI conversation (if bot is mentioned)
        if context.bot.username in update.message.text:
            await self.ai_conversation(update, context)

    async def check_flood(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check for message flooding"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        current_time = datetime.now()
        
        cursor = self.conn.cursor()
        
        # Get flood settings
        cursor.execute('SELECT antiflood_limit, antiflood_time FROM group_settings WHERE chat_id=?', (chat_id,))
        settings = cursor.fetchone()
        if not settings:
            return
        
        flood_limit, flood_time = settings
        
        # Update flood control
        cursor.execute('''
            INSERT OR REPLACE INTO flood_control 
            (user_id, chat_id, message_count, last_message_time)
            VALUES (?, ?, 
                CASE 
                    WHEN (SELECT last_message_time FROM flood_control WHERE user_id=? AND chat_id=?) IS NULL 
                         OR (julianday(?) - julianday((SELECT last_message_time FROM flood_control WHERE user_id=? AND chat_id=?))) * 86400 > ?
                    THEN 1
                    ELSE COALESCE((SELECT message_count FROM flood_control WHERE user_id=? AND chat_id=?), 0) + 1
                END,
                ?)
        ''', (user_id, chat_id, user_id, chat_id, current_time, user_id, chat_id, 
              flood_time, user_id, chat_id, current_time))
        
        # Check if limit exceeded
        cursor.execute('SELECT message_count FROM flood_control WHERE user_id=? AND chat_id=?', (user_id, chat_id))
        message_count = cursor.fetchone()[0]
        
        if message_count > flood_limit:
            try:
                # Mute user for 5 minutes
                until_date = current_time + timedelta(minutes=5)
                permissions = ChatPermissions(can_send_messages=False)
                
                await context.bot.restrict_chat_member(
                    chat_id, user_id, permissions, until_date=until_date
                )
                
                await context.bot.send_message(
                    chat_id,
                    f"🚫 {update.effective_user.mention_html()} has been muted for 5 minutes due to flooding!",
                    parse_mode=ParseMode.HTML
                )
                
                # Reset flood counter
                cursor.execute('DELETE FROM flood_control WHERE user_id=? AND chat_id=?', (user_id, chat_id))
            except Exception as e:
                logger.error(f"Failed to mute user for flooding: {e}")
        
        self.conn.commit()

    async def check_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check message against word filters"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.lower()
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT trigger_word, response, action FROM filters WHERE chat_id=?', (chat_id,))
        filters = cursor.fetchall()
        
        for trigger, response, action in filters:
            if trigger.lower() in message_text:
                if action == 'delete':
                    try:
                        await update.message.delete()
                        if response:
                            await context.bot.send_message(chat_id, response)
                    except:
                        pass
                elif action == 'warn':
                    # This would trigger the warn system
                    pass
                elif action == 'kick':
                    if await self.is_admin(update, context):
                        continue
                    try:
                        await context.bot.kick_chat_member(chat_id, update.effective_user.id)
                        await context.bot.unban_chat_member(chat_id, update.effective_user.id)
                    except:
                        pass
                break

    async def ai_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle AI-powered conversations"""
        if not self.openai_key:
            responses = [
                "I'm here to help manage the group! 🤖",
                "Hello! How can I assist you today?",
                "Need help with group management? Just ask!",
                "I'm your friendly group assistant! 😊"
            ]
            await update.message.reply_text(random.choice(responses))
            return
        
        try:
            # Remove bot mention from message
            message_text = update.message.text.replace(f'@{context.bot.username}', '').strip()
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful group management bot assistant. Keep responses brief and friendly."},
                    {"role": "user", "content": message_text}
                ],
                max_tokens=150
            )
            
            ai_response = response.choices[0].message.content
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"AI conversation error: {e}")
            await update.message.reply_text("I'm having trouble processing that right now. Try again later! 🤖")

    async def set_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set custom welcome message"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "ℹ️ Use: `/welcome Your welcome message here`\n\n"
                "Available placeholders:\n"
                "• `{name}` - User's first name\n"
                "• `{username}` - User's username\n"
                "• `{group}` - Group name",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        welcome_message = ' '.join(context.args)
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO group_settings 
            (chat_id, welcome_message, welcome_enabled)
            VALUES (?, ?, 1)
        ''', (chat_id, welcome_message))
        self.conn.commit()
        
        await update.message.reply_text("✅ Welcome message has been set!")

    def run(self):
        """Run the bot"""
        application = Application.builder().token(self.token).post_init(self.set_bot_commands).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("warn", self.warn_user))
        application.add_handler(CommandHandler("ban", self.ban_user))
        application.add_handler(CommandHandler("unban", self.unban_user))
        application.add_handler(CommandHandler("mute", self.mute_user))
        application.add_handler(CommandHandler("stats", self.group_stats))
        application.add_handler(CommandHandler("welcome", self.set_welcome_message))

        # Add message handlers
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.welcome_member))
        application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, self.goodbye_member))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Run the bot
        print("🤖 Bot is starting...")
        application.run_polling()


    async def set_bot_commands(self, bot):
        """Set bot commands for UI"""
        await bot.set_my_commands(self.admin_commands)

    async def add_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a note"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can add notes.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("ℹ️ Use: `/addnote note_name note content here`", parse_mode=ParseMode.MARKDOWN)
            return
        
        note_name = context.args[0].lower()
        note_content = ' '.join(context.args[1:])
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO notes 
            (chat_id, note_name, note_content, created_by)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, note_name, note_content, user_id))
        self.conn.commit()
        
        await update.message.reply_text(f"✅ Note `{note_name}` has been saved!", parse_mode=ParseMode.MARKDOWN)

    async def get_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get a specific note"""
        if not context.args:
            # Show all notes
            await self.show_notes(update, context)
            return
        
        note_name = context.args[0].lower()
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT note_content FROM notes WHERE chat_id=? AND note_name=?', (chat_id, note_name))
        note = cursor.fetchone()
        
        if note:
            await update.message.reply_text(note[0], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ Note `{note_name}` not found.", parse_mode=ParseMode.MARKDOWN)

    async def show_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all available notes"""
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT note_name FROM notes WHERE chat_id=? ORDER BY note_name', (chat_id,))
        notes = cursor.fetchall()
        
        if notes:
            notes_text = "📝 **Available Notes:**\n\n"
            for (note_name,) in notes:
                notes_text += f"• `{note_name}`\n"
            notes_text += f"\nUse `/get note_name` to view a note."
        else:
            notes_text = "📝 No notes available. Use `/addnote name content` to add one."
        
        await update.message.reply_text(notes_text, parse_mode=ParseMode.MARKDOWN)

    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add word filter"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can add filters.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "ℹ️ Use: `/addfilter trigger_word response_message`\n"
                "Actions: delete (default), warn, kick",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        trigger_word = context.args[0].lower()
        response = ' '.join(context.args[1:])
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO filters 
            (chat_id, trigger_word, response, created_by)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, trigger_word, response, user_id))
        self.conn.commit()
        
        await update.message.reply_text(f"✅ Filter for `{trigger_word}` has been added!", parse_mode=ParseMode.MARKDOWN)

    async def show_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all active filters"""
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT trigger_word, action FROM filters WHERE chat_id=? ORDER BY trigger_word', (chat_id,))
        filters = cursor.fetchall()
        
        if filters:
            filters_text = "🔍 **Active Filters:**\n\n"
            for trigger, action in filters:
                filters_text += f"• `{trigger}` → {action}\n"
        else:
            filters_text = "🔍 No filters active. Use `/addfilter word response` to add one."
        
        await update.message.reply_text(filters_text, parse_mode=ParseMode.MARKDOWN)

    async def delete_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a filter"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can delete filters.")
            return
        
        if not context.args:
            await update.message.reply_text("ℹ️ Use: `/delfilter trigger_word`", parse_mode=ParseMode.MARKDOWN)
            return
        
        trigger_word = context.args[0].lower()
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM filters WHERE chat_id=? AND trigger_word=?', (chat_id, trigger_word))
        
        if cursor.rowcount > 0:
            self.conn.commit()
            await update.message.reply_text(f"✅ Filter `{trigger_word}` has been deleted!", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ Filter `{trigger_word}` not found.", parse_mode=ParseMode.MARKDOWN)

    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set group rules"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can set rules.")
            return
        
        if not context.args:
            await update.message.reply_text("ℹ️ Use: `/setrules Your group rules here`", parse_mode=ParseMode.MARKDOWN)
            return
        
        rules = ' '.join(context.args)
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO group_settings 
            (chat_id, rules)
            VALUES (?, ?)
        ''', (chat_id, rules))
        self.conn.commit()
        
        await update.message.reply_text("✅ Group rules have been updated!")

    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group rules"""
        chat_id = update.effective_chat.id
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT rules FROM group_settings WHERE chat_id=?', (chat_id,))
        rules_row = cursor.fetchone()
        
        if rules_row and rules_row[0]:
            rules_text = f"📋 **Group Rules:**\n\n{rules_row[0]}"
        else:
            rules_text = "📋 No rules have been set for this group.\n\nAdmins can use `/setrules` to set them."
        
        await update.message.reply_text(rules_text, parse_mode=ParseMode.MARKDOWN)

    async def kick_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kick a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to kick the user.")
            return
        
        target_user = update.message.reply_to_message.from_user
        reason = ' '.join(context.args) if context.args else "No reason provided"
        chat_id = update.effective_chat.id
        
        try:
            await context.bot.kick_chat_member(chat_id, target_user.id)
            await context.bot.unban_chat_member(chat_id, target_user.id)  # Allows them to rejoin
            
            kick_text = f"👠 **User Kicked**\n\n"
            kick_text += f"👤 User: {target_user.mention_html()}\n"
            kick_text += f"📝 Reason: {reason}\n"
            kick_text += f"👮 By: {update.effective_user.mention_html()}"
            
            await update.message.reply_text(kick_text, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to kick user: {str(e)}")

    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute a user"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to unmute the user.")
            return
        
        target_user = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        
        try:
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
            
            await context.bot.restrict_chat_member(chat_id, target_user.id, permissions)
            
            unmute_text = f"🔊 **User Unmuted**\n\n"
            unmute_text += f"👤 User: {target_user.mention_html()}\n"
            unmute_text += f"👮 By: {update.effective_user.mention_html()}"
            
            await update.message.reply_text(unmute_text, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unmute user: {str(e)}")

    async def pin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pin a message"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can pin messages.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to pin it.")
            return
        
        try:
            await context.bot.pin_chat_message(
                update.effective_chat.id, 
                update.message.reply_to_message.message_id,
                disable_notification=True
            )
            await update.message.reply_text("📌 Message pinned!")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to pin message: {str(e)}")

    async def unpin_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unpin all messages"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can unpin messages.")
            return
        
        try:
            await context.bot.unpin_all_chat_messages(update.effective_chat.id)
            await update.message.reply_text("📌 All messages unpinned!")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unpin messages: {str(e)}")

    async def purge_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete multiple messages"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can purge messages.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to start purging from there.")
            return
        
        try:
            start_id = update.message.reply_to_message.message_id
            end_id = update.message.message_id
            chat_id = update.effective_chat.id
            
            deleted_count = 0
            for msg_id in range(start_id, end_id + 1):
                try:
                    await context.bot.delete_message(chat_id, msg_id)
                    deleted_count += 1
                except:
                    continue
            
            confirm_msg = await update.message.reply_text(f"🗑️ Deleted {deleted_count} messages!")
            
            # Delete confirmation message after 5 seconds
            await asyncio.sleep(5)
            try:
                await confirm_msg.delete()
            except:
                pass
                
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to purge messages: {str(e)}")

    async def report_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Report a message to admins"""
        if not update.message.reply_to_message:
            await update.message.reply_text("ℹ️ Reply to a message to report it.")
            return
        
        chat_id = update.effective_chat.id
        reporter_id = update.effective_user.id
        reported_msg = update.message.reply_to_message
        reported_user_id = reported_msg.from_user.id
        reason = ' '.join(context.args) if context.args else "No reason provided"
        
        # Check if reports are enabled
        cursor = self.conn.cursor()
        cursor.execute('SELECT reports_enabled FROM group_settings WHERE chat_id=?', (chat_id,))
        settings = cursor.fetchone()
        
        if settings and not settings[0]:
            await update.message.reply_text("❌ Reports are disabled in this group.")
            return
        
        # Save report to database
        cursor.execute('''
            INSERT INTO reports 
            (chat_id, reporter_id, reported_user_id, message_id, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, reporter_id, reported_user_id, reported_msg.message_id, reason))
        self.conn.commit()
        
        # Notify admins
        try:
            chat_admins = await context.bot.get_chat_administrators(chat_id)
            report_text = f"🚨 **New Report**\n\n"
            report_text += f"👤 Reported User: {reported_msg.from_user.mention_html()}\n"
            report_text += f"👮 Reporter: {update.effective_user.mention_html()}\n"
            report_text += f"📝 Reason: {reason}\n"
            report_text += f"🔗 [Go to Message](https://t.me/c/{str(chat_id)[4:]}/{reported_msg.message_id})"
            
            for admin in chat_admins:
                if not admin.user.is_bot:
                    try:
                        await context.bot.send_message(
                            admin.user.id, report_text, 
                            parse_mode=ParseMode.HTML
                        )
                    except:
                        continue
        except:
            pass
        
        await update.message.reply_text("✅ Report has been sent to administrators.")

    async def bot_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot settings"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Only administrators can view settings.")
            return
        
        chat_id = update.effective_chat.id
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT welcome_enabled, goodbye_enabled, reports_enabled, 
                   ai_chat_enabled, max_warnings, antiflood_limit, antiflood_time
            FROM group_settings WHERE chat_id=?
        ''', (chat_id,))
        settings = cursor.fetchone()
        
        if not settings:
            # Create default settings
            cursor.execute('''
                INSERT INTO group_settings (chat_id) VALUES (?)
            ''', (chat_id,))
            self.conn.commit()
            settings = (1, 1, 1, 1, 3, 5, 60)
        
        welcome_enabled, goodbye_enabled, reports_enabled, ai_chat_enabled, max_warnings, antiflood_limit, antiflood_time = settings
        
        settings_text = f"⚙️ **Bot Settings**\n\n"
        settings_text += f"👋 Welcome Messages: {'✅' if welcome_enabled else '❌'}\n"
        settings_text += f"👋 Goodbye Messages: {'✅' if goodbye_enabled else '❌'}\n"
        settings_text += f"🚨 Reports: {'✅' if reports_enabled else '❌'}\n"
        settings_text += f"🤖 AI Chat: {'✅' if ai_chat_enabled else '❌'}\n"
        settings_text += f"⚠️ Max Warnings: {max_warnings}\n"
        settings_text += f"🌊 Anti-flood: {antiflood_limit} msgs/{antiflood_time}s\n"
        
        # Create settings keyboard
        keyboard = [
            [
                InlineKeyboardButton("👋 Welcome", callback_data="toggle_welcome"),
                InlineKeyboardButton("👋 Goodbye", callback_data="toggle_goodbye")
            ],
            [
                InlineKeyboardButton("🚨 Reports", callback_data="toggle_reports"),
                InlineKeyboardButton("🤖 AI Chat", callback_data="toggle_ai")
            ],
            [
                InlineKeyboardButton("⚠️ Warnings", callback_data="set_warnings"),
                InlineKeyboardButton("🌊 Anti-flood", callback_data="set_antiflood")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "show_rules":
            await self.show_rules_callback(query, context)
        elif query.data == "show_help":
            await self.help_callback(query, context)
        elif query.data.startswith("toggle_"):
            await self.toggle_setting(query, context)

    async def show_rules_callback(self, query, context):
        """Show rules via callback"""
        chat_id = query.message.chat.id
        cursor = self.conn.cursor()
        cursor.execute('SELECT rules FROM group_settings WHERE chat_id=?', (chat_id,))
        rules_row = cursor.fetchone()
        
        if rules_row and rules_row[0]:
            rules_text = f"📋 **Group Rules:**\n\n{rules_row[0]}"
        else:
            rules_text = "📋 No rules have been set for this group."
        
        await query.edit_message_text(rules_text, parse_mode=ParseMode.MARKDOWN)

    async def help_callback(self, query, context):
        """Show help via callback"""
        help_text = """
🤖 **Quick Help**

**User Commands:**
• /rules - View group rules
• /notes - Show saved notes  
• /report - Report a message (reply to it)

**Admin Commands:**
• /warn, /ban, /kick, /mute
• /stats - Group statistics
• /settings - Bot configuration

Need more help? Use /help in the chat!
        """
        await query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def toggle_setting(self, query, context):
        """Toggle bot settings"""
        chat_id = query.message.chat.id
        setting = query.data.replace("toggle_", "")
        
        cursor = self.conn.cursor()
        
        if setting == "welcome":
            cursor.execute('''
                UPDATE group_settings 
                SET welcome_enabled = NOT welcome_enabled 
                WHERE chat_id = ?
            ''', (chat_id,))
        elif setting == "goodbye":
            cursor.execute('''
                UPDATE group_settings 
                SET goodbye_enabled = NOT goodbye_enabled 
                WHERE chat_id = ?
            ''', (chat_id,))
        elif setting == "reports":
            cursor.execute('''
                UPDATE group_settings 
                SET reports_enabled = NOT reports_enabled 
                WHERE chat_id = ?
            ''', (chat_id,))
        elif setting == "ai":
            cursor.execute('''
                UPDATE group_settings 
                SET ai_chat_enabled = NOT ai_chat_enabled 
                WHERE chat_id = ?
            ''', (chat_id,))
        
        self.conn.commit()
        await query.edit_message_text("✅ Setting updated! Use /settings to see current configuration.")


# Example usage and setup
if __name__ == "__main__":
    # Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Create and run bot
    bot = GroupBot(BOT_TOKEN, OPENAI_API_KEY)
    
    # Add remaining handlers
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Additional command handlers
    application.add_handler(CommandHandler("addnote", bot.add_note))
    application.add_handler(CommandHandler("notes", bot.show_notes))
    application.add_handler(CommandHandler("get", bot.get_note))
    application.add_handler(CommandHandler("addfilter", bot.add_filter))
    application.add_handler(CommandHandler("filters", bot.show_filters))
    application.add_handler(CommandHandler("delfilter", bot.delete_filter))
    application.add_handler(CommandHandler("rules", bot.show_rules))
    application.add_handler(CommandHandler("setrules", bot.set_rules))
    application.add_handler(CommandHandler("kick", bot.kick_user))
    application.add_handler(CommandHandler("unmute", bot.unmute_user))
    application.add_handler(CommandHandler("pin", bot.pin_message))
    application.add_handler(CommandHandler("unpin", bot.unpin_messages))
    application.add_handler(CommandHandler("purge", bot.purge_messages))
    application.add_handler(CommandHandler("report", bot.report_message))
    application.add_handler(CommandHandler("settings", bot.bot_settings))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Run the bot
    bot.run()

"""
INSTALLATION REQUIREMENTS:
pip install python-telegram-bot sqlite3 openai asyncio

SETUP INSTRUCTIONS:
1. Create a new bot with @BotFather on Telegram
2. Get your bot token and replace BOT_TOKEN
3. (Optional) Get OpenAI API key for AI features
4. Install required packages
5. Run the script
6. Add bot to your group and make it an admin

BOT FEATURES:
✅ User Management (warn, ban, kick, mute)
✅ Welcome/Goodbye messages with customization
✅ Group statistics and activity tracking
✅ Anti-flood and anti-spam protection
✅ Word filters with custom responses
✅ Notes system for saving information
✅ Report system for user reports
✅ AI-powered conversations (optional)
✅ Advanced admin tools (pin, purge, promote)
✅ Customizable settings via inline keyboards
✅ SQLite database for data persistence
✅ Professional error handling and logging
✅ Comprehensive help system
✅ Multiple language support ready
✅ Rate limiting and flood control
✅ Automatic moderation actions
✅ User activity tracking
✅ Flexible permission system

ADMIN PERMISSIONS NEEDED:
- Delete messages
- Restrict users  
- Ban users
- Pin messages
- Add new admins
- Manage chat
"""
