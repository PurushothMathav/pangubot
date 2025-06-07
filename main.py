#BOT_TOKEN = '8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew'

import asyncio
import random
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from telegram import Update, ChatMemberUpdated, MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
    CallbackQueryHandler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedChatBot:
    def __init__(self):
        # Bot configuration
        self.BOT_TOKEN = "8080188016:AAFgwqLg4tAA6Uw7XPNd8tpbiIQKTMBTXew"
        
        # In-memory storage (use database in production)
        self.warnings = {}
        self.user_contexts = {}  # Store conversation context per user
        self.group_stats = {}
        self.muted_users = {}
        
        # Enhanced bad words list with categories
        self.profanity_patterns = {
            'mild': ['damn', 'hell', 'crap', 'bloody'],
            'moderate': ['shit', 'ass', 'bitch', 'piss', 'dick'],
            'severe': ['fuck', 'fucking', 'fucker', 'motherfucker', 'cocksucker', 'cunt'],
            'slurs': ['nigger', 'faggot', 'retard']  # Handle with extreme caution
        }
        
        # Conversation patterns for human-like responses
        self.conversation_patterns = {
            'greetings': {
                'patterns': [r'\b(hi|hello|hey|sup|yo|good morning|good evening)\b'],
                'responses': [
                    "Hey there! 👋 How's your day going?",
                    "Hello! Nice to see you here! 😊",
                    "Hi! What's on your mind today?",
                    "Hey! Hope you're having a great day! ✨",
                    "Yo! What's up? 🤙"
                ]
            },
            'questions': {
                'patterns': [r'\?', r'\bwhat\b', r'\bhow\b', r'\bwhy\b', r'\bwhen\b', r'\bwhere\b'],
                'responses': [
                    "That's an interesting question! 🤔",
                    "Hmm, let me think about that...",
                    "Good question! What do you think?",
                    "I'm curious about that too! 💭",
                    "That's something worth discussing!"
                ]
            },
            'thanks': {
                'patterns': [r'\b(thanks|thank you|thx|ty)\b'],
                'responses': [
                    "You're welcome! 😊",
                    "No problem at all! 👍",
                    "Happy to help! ✨",
                    "Anytime! 🙌",
                    "Glad I could help! 😄"
                ]
            },
            'jokes': {
                'patterns': [r'\b(joke|funny|lol|haha|😂|🤣)\b'],
                'responses': [
                    "Haha, I love a good laugh! 😄",
                    "Humor makes everything better! 😂",
                    "That's hilarious! 🤣",
                    "You're pretty funny! 😁",
                    "Laughter is the best medicine! 💊😂"
                ]
            },
            'sad': {
                'patterns': [r'\b(sad|depressed|down|upset|😢|😭|☹️)\b'],
                'responses': [
                    "I'm sorry you're feeling down. Things will get better! 💙",
                    "Sending you virtual hugs! 🤗 You're not alone.",
                    "It's okay to feel sad sometimes. Take care of yourself! 💝",
                    "Remember, tough times don't last, tough people do! 💪",
                    "Here if you need to talk. You matter! ❤️"
                ]
            },
            'compliments': {
                'patterns': [r'\b(good|great|awesome|amazing|wonderful|perfect)\b'],
                'responses': [
                    "That's fantastic! 🌟",
                    "Awesome to hear! 🎉",
                    "That sounds amazing! ✨",
                    "So happy for you! 😊",
                    "That's wonderful news! 🎊"
                ]
            }
        }
        
        # Fun commands responses
        self.fun_responses = {
            'motivational': [
                "You've got this! 💪 Every small step counts!",
                "Believe in yourself! You're capable of amazing things! ✨",
                "Today is full of possibilities! Make it count! 🌟",
                "You're stronger than you think! Keep pushing forward! 🚀",
                "Success is a journey, not a destination. Enjoy the ride! 🎯"
            ],
            'jokes': [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "I told my wife she was drawing her eyebrows too high. She looked surprised! 😂",
                "Why did the math book look so sad? Because it had too many problems! 📚",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why don't eggs tell jokes? They'd crack each other up! 🥚"
            ],
            'facts': [
                "🧠 Did you know? Octopuses have three hearts and blue blood!",
                "🌙 Fun fact: A day on Venus is longer than its year!",
                "🐝 Amazing: Bees can recognize human faces!",
                "🌊 Cool fact: There are more possible chess games than atoms in the observable universe!",
                "🎵 Interesting: Music can trigger the same dopamine release as food and sex!"
            ]
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_msg = (
            "🤖 **Advanced Chat Bot Online!** \n\n"
            "I'm here to help moderate your chat and have conversations! Here's what I can do:\n\n"
            "🔧 **Moderation:**\n"
            "• Auto-warn for inappropriate language\n"
            "• Ban/unban/mute users\n"
            "• Welcome new members\n\n"
            "💬 **Chat Features:**\n"
            "• Natural conversations (mention me!)\n"
            "• Fun commands (/joke, /motivate, /fact)\n"
            "• Group statistics\n\n"
            "📋 **Commands:** /help for full list\n\n"
            "Let's make this chat awesome! 🎉"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🔧 **Moderation Commands:**
/warn - Warn a user (reply to their message)
/ban - Ban a user (reply to their message)
/unban - Unban a user (reply to their message)
/mute - Mute a user for 1 hour (reply to their message)
/unmute - Unmute a user (reply to their message)

🎉 **Fun Commands:**
/joke - Get a random joke
/motivate - Get motivational message
/fact - Learn something interesting
/stats - View group statistics
/roll - Roll a dice (1-6)
/flip - Flip a coin
/link - Get PanguPlay website link

💬 **Chat Features:**
• Mention me (@botname) for natural conversation
• I respond to greetings, questions, and emotions
• Auto-moderation for inappropriate content

🎯 **Tips:**
• Reply to messages when using moderation commands
• I'm always learning and improving!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a user's message to warn them.")
            return
            
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        count = self.warnings[user_id]
        
        warning_msg = f"⚠️ **Warning issued to {user_name}**\n"
        warning_msg += f"Total warnings: **{count}/3**\n"
        
        if count >= 3:
            try:
                await update.effective_chat.ban_member(user_id)
                warning_msg += "🚫 **User auto-banned after 3 warnings!**"
            except Exception as e:
                warning_msg += "❌ Failed to ban user (insufficient permissions)"
        else:
            warning_msg += f"Next warning will result in a ban!"
            
        await update.message.reply_text(warning_msg, parse_mode='Markdown')

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a user's message to ban them.")
            return
            
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        try:
            await update.effective_chat.ban_member(user_id)
            await update.message.reply_text(f"🚫 **{user_name} has been banned!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("❌ Failed to ban user. I might not have admin permissions.")

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a user's message to unban them.")
            return
            
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        try:
            await update.effective_chat.unban_member(user_id)
            # Reset warnings
            self.warnings[user_id] = 0
            await update.message.reply_text(f"✅ **{user_name} has been unbanned and warnings reset!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("❌ Failed to unban user.")

    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a user's message to mute them.")
            return
            
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        # Mute for 1 hour
        until_date = datetime.now() + timedelta(hours=1)
        self.muted_users[user_id] = until_date
        
        try:
            await update.effective_chat.restrict_member(
                user_id, 
                permissions=telegram.ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await update.message.reply_text(f"🔇 **{user_name} has been muted for 1 hour!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("❌ Failed to mute user.")

    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a user's message to unmute them.")
            return
            
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        try:
            await update.effective_chat.restrict_member(
                user_id, 
                permissions=telegram.ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True
                )
            )
            if user_id in self.muted_users:
                del self.muted_users[user_id]
            await update.message.reply_text(f"🔊 **{user_name} has been unmuted!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("❌ Failed to unmute user.")

    def detect_profanity_level(self, text: str) -> Optional[str]:
        """Detect profanity and return severity level"""
        text_lower = text.lower()
        
        for level, words in self.profanity_patterns.items():
            if any(word in text_lower for word in words):
                return level
        return None

    async def check_bot_mention(self, message, bot_username: str) -> bool:
        """Enhanced bot mention detection"""
        if not message or not message.text:
            return False
            
        text = message.text.lower()
        bot_username = bot_username.lower()
        
        # Method 1: Check message entities for @mentions
        if message.entities:
            for entity in message.entities:
                if entity.type == MessageEntity.MENTION:
                    mention_text = message.text[entity.offset:entity.offset + entity.length].lower()
                    if mention_text == f"@{bot_username}":
                        return True
        
        # Method 2: Check if bot username appears anywhere in text
        if f"@{bot_username}" in text:
            return True
            
        # Method 3: Check if message starts with bot name
        if text.startswith(f"@{bot_username}"):
            return True
            
        return False

    async def smart_content_moderation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced content moderation with contextual responses - only when bot is mentioned"""
        message = update.message
        if not message or not message.text:
            return

        # Only moderate when bot is mentioned
        bot_username = (await context.bot.get_me()).username
        if not await self.check_bot_mention(message, bot_username):
            return

        user_id = message.from_user.id
        user_name = message.from_user.first_name
        text = message.text

        # Check for profanity
        profanity_level = self.detect_profanity_level(text)
        
        if profanity_level:
            self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
            count = self.warnings[user_id]
            
            # Different responses based on severity
            if profanity_level == 'mild':
                response = f"😅 Hey {user_name}, let's keep it clean! Warning {count}/3"
            elif profanity_level == 'moderate':
                response = f"😐 {user_name}, that language isn't cool here. Warning {count}/3"
            elif profanity_level == 'severe':
                response = f"😠 {user_name}, that's too much! Please watch your language. Warning {count}/3"
            else:  # slurs
                response = f"🚫 {user_name}, that language is completely unacceptable! Final warning {count}/3"
            
            if count >= 3:
                try:
                    await update.effective_chat.ban_member(user_id)
                    response += "\n🚫 **User has been banned for repeated violations!**"
                except:
                    response += "\n❌ Unable to ban (need admin permissions)"
                    
            await message.reply_text(response, parse_mode='Markdown')

    async def natural_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural conversation when bot is mentioned"""
        message = update.message
        if not message or not message.text:
            return

        bot_username = (await context.bot.get_me()).username.lower()
        text = message.text.lower()
        original_text = message.text
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        # Check if bot is mentioned (multiple ways)
        bot_username = (await context.bot.get_me()).username
        mentioned = await self.check_bot_mention(message, bot_username)

        if not mentioned:
            return

        # Update user context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {'messages': [], 'last_interaction': datetime.now()}
        
        self.user_contexts[user_id]['messages'].append(text)
        self.user_contexts[user_id]['last_interaction'] = datetime.now()
        
        # Keep only last 5 messages for context
        if len(self.user_contexts[user_id]['messages']) > 5:
            self.user_contexts[user_id]['messages'].pop(0)

        # Check for profanity first
        if self.detect_profanity_level(text):
            await self.smart_content_moderation(update, context)
            return

        # Find matching conversation pattern
        response = None
        for category, pattern_data in self.conversation_patterns.items():
            for pattern in pattern_data['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    response = random.choice(pattern_data['responses'])
                    break
            if response:
                break

        # Default responses if no pattern matches
        if not response:
            default_responses = [
                f"That's interesting, {user_name}! Tell me more! 🤔",
                f"I hear you, {user_name}! What's your take on that? 💭",
                f"Thanks for sharing that with me, {user_name}! 😊",
                f"That's a great point, {user_name}! 👍",
                f"I'm listening, {user_name}! Keep going! 👂",
                f"Fascinating perspective, {user_name}! 🌟",
                f"You always have something interesting to say, {user_name}! ✨"
            ]
            response = random.choice(default_responses)

        await message.reply_text(response)

    # Fun commands
    async def joke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        joke = random.choice(self.fun_responses['jokes'])
        await update.message.reply_text(joke)

    async def motivate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        motivation = random.choice(self.fun_responses['motivational'])
        await update.message.reply_text(motivation)

    async def fact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        fact = random.choice(self.fun_responses['facts'])
        await update.message.reply_text(fact)

    async def roll_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        roll = random.randint(1, 6)
        await update.message.reply_text(f"🎲 You rolled a **{roll}**!", parse_mode='Markdown')

    async def flip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = random.choice(['Heads', 'Tails'])
        emoji = '🟡' if result == 'Heads' else '⚪'
        await update.message.reply_text(f"🪙 {emoji} **{result}**!", parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        total_warnings = len(self.warnings)
        active_users = len(self.user_contexts)
        muted_count = len(self.muted_users)
        
        stats_msg = f"""
📊 **Group Statistics**

👥 Active conversationalists: **{active_users}**
⚠️ Total users with warnings: **{total_warnings}**
🔇 Currently muted users: **{muted_count}**

🤖 Bot uptime: Online and ready!
💬 I'm here to help keep things fun and friendly!
        """
        await update.message.reply_text(stats_msg.strip(), parse_mode='Markdown')

    async def link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        link_msg = (
            "🌐 **Check out PanguPlay!** 🎮\n\n"
            "🔗 **Website**: http://purushothmathav.github.io/PanguPlay/\n\n"
            "🎯 Your one stop destination to Tamil entertainment!\n"
            "✨ Click the link above to explore!"
        )
        await update.message.reply_text(link_msg, parse_mode='Markdown')

    async def welcome_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced welcome/goodbye messages"""
        result: ChatMemberUpdated = update.chat_member
        old_status = result.old_chat_member.status
        new_status = result.new_chat_member.status
        user = result.new_chat_member.user

        if old_status in ("left", "kicked") and new_status == "member":
            welcome_messages = [
                f"🎉 Welcome to the party, {user.mention_html()}! Glad you're here!",
                f"👋 Hey {user.mention_html()}! Welcome aboard! Feel free to jump into any conversation!",
                f"🌟 Welcome {user.mention_html()}! We're excited to have you with us!",
                f"🎊 {user.mention_html()} just joined! Let's give them a warm welcome!",
                f"✨ Welcome {user.mention_html()}! Hope you enjoy your time here!"
            ]
            welcome_msg = random.choice(welcome_messages)
            await update.effective_chat.send_message(welcome_msg, parse_mode='HTML')
            
        elif new_status in ("left", "kicked"):
            goodbye_messages = [
                f"👋 See you later, {user.mention_html()}! You're always welcome back!",
                f"🌅 Goodbye {user.mention_html()}! Thanks for being part of our community!",
                f"✌️ {user.mention_html()} has left the building! Catch you on the flip side!",
                f"👋 Take care, {user.mention_html()}! Hope to see you again soon!"
            ]
            goodbye_msg = random.choice(goodbye_messages)
            await update.effective_chat.send_message(goodbye_msg, parse_mode='HTML')

    async def combined_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Combined handler for moderation and conversation"""
        # First check for moderation (if bot is mentioned with bad words)
        await self.smart_content_moderation(update, context)
        
        # Then handle natural conversation (if bot is mentioned)
        await self.natural_conversation(update, context)

    def setup_handlers(self, app):
        """Setup all command and message handlers"""
        # Command handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("warn", self.warn_user))
        app.add_handler(CommandHandler("ban", self.ban_user))
        app.add_handler(CommandHandler("unban", self.unban_user))
        app.add_handler(CommandHandler("mute", self.mute_user))
        app.add_handler(CommandHandler("unmute", self.unmute_user))
        
        # Fun commands
        app.add_handler(CommandHandler("joke", self.joke_command))
        app.add_handler(CommandHandler("motivate", self.motivate_command))
        app.add_handler(CommandHandler("fact", self.fact_command))
        app.add_handler(CommandHandler("roll", self.roll_command))
        app.add_handler(CommandHandler("flip", self.flip_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("link", self.link_command))

        # Message handlers - Updated order and combined
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.combined_message_handler))

        # Chat member updates
        app.add_handler(ChatMemberHandler(self.welcome_goodbye, ChatMemberHandler.CHAT_MEMBER))

    def run(self):
        """Start the bot"""
        app = ApplicationBuilder().token(self.BOT_TOKEN).build()
        self.setup_handlers(app)
        
        print("🤖 Advanced Chat Bot is running... Press Ctrl+C to stop.")
        print("✨ Features: Natural conversation, smart moderation, fun commands!")
        app.run_polling()

def main():
    bot = AdvancedChatBot()
    bot.run()

if __name__ == '__main__':
    main()
