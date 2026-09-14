import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from PIL import Image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
أنت مساعد خبير وميكانيكي سيارات محترف تخدم فنيي الصيانة وأصحاب الورش.
مهامك:
1. تحليل أكواد الأعطال (OBD-II Codes مثل P0300) وتقديم الأسباب المرجحة وخطوات الفحص.
2. شرح أعراض المشاكل الميكانيكية والكهربائية واستراتيجيات الإصلاح.
3. تحليل صور القطع التالفة أو التسريبات وتحديد المشكلة إن أمكن.
4. تقديم نصائح حول زيوت المحرك، عزم الربط (Torque Specs)، ومخططات الصيانة.
اجعل إجاباتك عملية، واضحة، ومباشرة وموجهة لفني ميكانيك.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "أهلاً بك يا معلّم! 🛠️🚗 أرسل لي كود العطل أو صورة القطعة لتشخيصها."
    await update.message.reply_text(welcome_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=update.message.text,
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء معالجة الطلب.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or "حلل هذه الصورة وأخبرني بالمشكلة الميكانيكية."
    await update.message.chat.send_action(action="typing")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"temp_{update.message.message_id}.jpg"
        await photo_file.download_to_drive(photo_path)
        img = Image.open(photo_path)
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, caption],
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
        if os.path.exists(photo_path):
            os.remove(photo_path)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء تحليل الصورة.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == '__main__':
    main()
