import os
import sqlite3
import logging
import pytz
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext,
    ConversationHandler
)

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

# ✅ Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Ensure pytz is used for timezone compatibility
TIMEZONE = pytz.timezone("UTC")

# ✅ Define states for conversation handler
STUDENT_NAME, SUBJECT, TEST_TYPE, PRACTICAL_MARKS, THEORETICAL_MARKS = range(5)

# ✅ Database setup function
def init_db():
    with sqlite3.connect("teacher_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                          id INTEGER PRIMARY KEY, 
                          name TEXT UNIQUE, 
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

# ✅ Command: /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to the Teacher's Assistant Bot! Use /help to see available commands.")

# ✅ Command: /help
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Available Commands:\n"
        "/add_marks - Add student marks\n"
        "/view_report - View student performance\n"
        "/export_excel - Export exam-wise reports\n"
        "/edit_student - Edit student name\n"
        "/edit_marks - Edit student marks\n"
        "/delete_student - Delete a student\n"
        "/delete_marks - Delete student marks\n"
        "/clear_text - Clear bot messages\n"
        "/cancel - Cancel current operation"
    )
    await update.message.reply_text(help_text)

# ✅ Command: /cancel
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

# ✅ Command: /add_marks
async def add_marks_start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Enter the student's name:")
    return STUDENT_NAME

async def student_name(update: Update, context: CallbackContext) -> int:
    context.user_data["student_name"] = update.message.text
    await update.message.reply_text("Enter the subject:")
    return SUBJECT

async def subject(update: Update, context: CallbackContext) -> int:
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("Enter the test type (e.g., Midterm, Final):")
    return TEST_TYPE

async def test_type(update: Update, context: CallbackContext) -> int:
    context.user_data["test_type"] = update.message.text
    await update.message.reply_text("Enter the practical marks:")
    return PRACTICAL_MARKS

async def practical_marks(update: Update, context: CallbackContext) -> int:
    context.user_data["practical_marks"] = update.message.text
    await update.message.reply_text("Enter the theoretical marks:")
    return THEORETICAL_MARKS

async def theoretical_marks(update: Update, context: CallbackContext) -> int:
    context.user_data["theoretical_marks"] = update.message.text

    with sqlite3.connect("teacher_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM students WHERE name = ?", (context.user_data["student_name"],))
        student = cursor.fetchone()
        
        if student:
            student_id = student[0]
        else:
            cursor.execute("INSERT INTO students (name, class) VALUES (?, ?)", (context.user_data["student_name"], "Unknown"))
            student_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO marks (student_id, subject, test_type, practical_marks, theoretical_marks) VALUES (?, ?, ?, ?, ?)",
            (student_id, context.user_data["subject"], context.user_data["test_type"],
             context.user_data["practical_marks"], context.user_data["theoretical_marks"])
        )
        conn.commit()

    await update.message.reply_text("✅ Marks recorded successfully!")
    return ConversationHandler.END

# ✅ Command: /export_excel
async def export_excel(update: Update, context: CallbackContext) -> None:
    with sqlite3.connect("teacher_bot.db") as conn:
        df = pd.read_sql_query("SELECT * FROM marks", conn)
    df.to_excel("exam_report.xlsx", index=False)
    await update.message.reply_text("📊 Report exported successfully!")

# ✅ Main function
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
    app.add_handler(CommandHandler("export_excel", export_excel))

    logger.info("🚀 Bot started successfully!")
    app.run_polling()

# ✅ Run the bot
if __name__ == "__main__":
    main()
