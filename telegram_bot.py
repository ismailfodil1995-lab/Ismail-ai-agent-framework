import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from brain import process_user_query

# توكن البوت الخاص بك
TOKEN = "8435539430:AAGNon5dx8vKx1TbXYbeqvx1IPKFcwr7AC0"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    chat_id = update.message.chat_id

    if document.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ يرجى إرسال ملف PDF فقط.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        os.makedirs("uploads", exist_ok=True)
        safe_name = os.path.basename(document.file_name or "document.pdf")
        file_path = os.path.join("uploads", f"{chat_id}_{safe_name}")

        telegram_file = await context.bot.get_file(document.file_id)
        await telegram_file.download_to_drive(custom_path=file_path)

        response_text = process_user_query(
            f"المستخدم أرسل ملف PDF باسم {safe_name}. اقرأ محتواه وقدّم ملخصاً.",
            chat_id=chat_id,
            pdf_path=file_path
        )

        await update.message.reply_text(response_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء معالجة ملف PDF: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    # إرسال تنبيه بأن الوكيل يفكّر
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # تشغيل العقل والأدوات مع تمرير معرف المحادثة للذاكرة
        response_text = process_user_query(user_message, chat_id=chat_id)

        sent_file = False
        
        # فحص الملفات الشائعة وإرسالها مباشرة للمستخدم
        for filename in ["summary_report.pdf", "leads_data.csv", "export.csv"]:
            if os.path.exists(filename) and (filename in response_text or "SUCCESS" in response_text or "PDF report generated" in response_text):
                with open(filename, 'rb') as f:
                    await context.bot.send_document(chat_id=chat_id, document=f, caption="📄 إليك الملف جاهزاً للتحميل كما طلبت.")
                sent_file = True
                break

        # إذا لم يكن هناك ملف للإرسال، نرسل النص العادي
        if not sent_file:
            await update.message.reply_text(response_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء معالجة الطلب: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 Telegram Agent with Direct File Sending & Memory is running...")
    app.run_polling()

if __name__ == '__main__':
    main()