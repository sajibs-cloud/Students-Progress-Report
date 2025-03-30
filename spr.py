import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the bot token
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

print(f"✅ Bot token loaded successfully!")  # Debug print

import sqlite3
import logging
import pytz
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext,
    ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure pytz is used for timezone compatibility
TIMEZONE = pytz.timezone("UTC")

# ✅ Remove the duplicate token retrieval here!

# Database setup
def init_db():
    conn = sqlite3.connect("teacher_bot.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                      id INTEGER PRIMARY KEY, 
                      name TEXT, 
                      class TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS marks (
                      id INTEGER PRIMARY KEY, 
                      student_id INTEGER, 
                      subject TEXT, 
                      test_type TEXT, 
                      practical_marks INTEGER, 
                      theoretical_marks INTEGER, 
                      FOREIGN KEY(student_id) REFERENCES students(id))''')
    conn.commit()
    conn.close()

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_marks", add_marks_start)],
        states={
            STUDENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_name)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, subject)],
            TEST_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_type)],
            PRACTICAL_MARKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, practical_marks)],
            THEORETICAL_MARKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, theoretical_marks)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("view_report", view_report))
    
    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
