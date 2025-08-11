import logging
import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ضع توكن البوت هنا مباشرة - غيّره عند رفعه على السيرفر لمتغير بيئة أو خزن آمن
TELEGRAM_TOKEN = "8438230728:AAFI4QGU5bdu7ORIsOjWrypfU4lq1m7LTnM"

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # تأكد من تعيين هذا المتغير للويبهوك الصحيح في بيئتك

(ASK_PHONE, ASK_NAME, ASK_UNI, ASK_COLLEGE, ASK_MAJOR, ASK_SUBJECT, ASK_SOURCE, ASK_RECOMMENDER, CONFIRMATION) = range(9)

scope =  ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("The Source Academy").worksheet("الحجز")

subjects = [
    "برمجة الحاسب م/أميرة",
    "أساسيات قواعد البيانات م/مروة",
    "أساسيات قواعد البيانات م/عبدالله",
    "أساسيات قواعد البيانات م/عبدالهادي",
    "معمارية الحاسب م/ليلى",
    "كيمياء عامة د/محمد سالم",
    "أساسيات نظم التشغيل م/إيمان",
    "نظم التشغيل م/إيمان",
    "تصميم منطقي م/ليلى",
    "هياكل البيانات م/أميرة",
    "📝 أخرى"
]

sources = ["فيسبوك", "صديق", "طالب", "انستجرام", "بحث Google", "أخرى"]

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 مرحبًا بك في The Source Academy\n\nمن فضلك شارك رقم هاتفك للبدء:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 إرسال رقم الهاتف", request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return ASK_PHONE

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    user_data[update.effective_chat.id] = {"phone": contact.phone_number}
    await update.message.reply_text("ما اسمك الثنائي؟", reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_uni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_chat.id]["name"] = update.message.text
    await update.message.reply_text("ما اسم الجامعة؟")
    return ASK_UNI

async def ask_college(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_chat.id]["university"] = update.message.text
    await update.message.reply_text("ما اسم الكلية؟")
    return ASK_COLLEGE

async def ask_major(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_chat.id]["college"] = update.message.text
    await update.message.reply_text("ما التخصص؟")
    return ASK_MAJOR

async def ask_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_chat.id]["major"] = update.message.text
    buttons = [[s] for s in subjects]
    await update.message.reply_text("اختر المادة:", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
    return ASK_SUBJECT

async def ask_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_chat.id]["subject"] = update.message.text
    buttons = [[s] for s in sources]
    await update.message.reply_text("كيف عرفت عن الأكاديمية؟", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
    return ASK_SOURCE

async def ask_recommender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    source = update.message.text
    user_data[update.effective_chat.id]["source"] = source
    if source == "طالب":
        await update.message.reply_text("من هو الطالب الذي أخبرك؟")
        return ASK_RECOMMENDER
    else:
        return await confirm(update, context)

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and user_data[update.effective_chat.id]["source"] == "طالب":
        user_data[update.effective_chat.id]["recommender"] = update.message.text
    else:
        user_data[update.effective_chat.id]["recommender"] = "-"

    text = f"""يرجى مراجعة بياناتك:
📱 رقم الهاتف: {user_data[update.effective_chat.id]['phone']}
👤 الاسم: {user_data[update.effective_chat.id]['name']}
🏫 الجامعة: {user_data[update.effective_chat.id]['university']}
🏢 الكلية: {user_data[update.effective_chat.id]['college']}
🎓 التخصص: {user_data[update.effective_chat.id]['major']}
📘 المادة: {user_data[update.effective_chat.id]['subject']}
📡 المصدر: {user_data[update.effective_chat.id]['source']}
👤 الطالب المعرّف (إن وجد): {user_data[update.effective_chat.id]['recommender']}

📌 الشروط والأحكام:
- التسجيل لا يُعد حجزًا نهائيًا إلا بعد التواصل والتأكيد من الإدارة.
- لا يجوز تحويل الحجز لطالب آخر دون الرجوع للإدارة.
- نسخة المحاضرات خاصة بك فقط، وممنوع مشاركتها أو إعادة رفعها بأي وسيلة.

هل توافق على الشروط؟
"""
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(
        [["✅ أوافق", "❌ لا أوافق"]], one_time_keyboard=True, resize_keyboard=True))
    return CONFIRMATION

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ أوافق":
        await update.message.reply_text("❌ تم إلغاء التسجيل.")
        return ConversationHandler.END

    data = user_data[update.effective_chat.id]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, data["phone"], data["name"], data["university"], data["college"], data["major"], data["subject"], data["source"], data["recommender"]]
    sheet.append_row(row)

    await update.message.reply_text("✅ تم تسجيل بياناتك بنجاح، وسيتم التواصل معك قريبًا.")

    context.bot.send_message(chat_id="@Emanpr", text=f"📥 تسجيل جديد:\n\n" + "\n".join([
        f"{k}: {v}" for k, v in data.items()
    ]))

    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PHONE: [MessageHandler(filters.CONTACT, ask_name)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_uni)],
            ASK_UNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_college)],
            ASK_COLLEGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_major)],
            ASK_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_subject)],
            ASK_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_source)],
            ASK_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_recommender)],
            ASK_RECOMMENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    # نستخدم webhook بدلاً من polling
    port = int(os.environ.get('PORT', '8443'))  # تأكد من أن هذا متغير بيئة مضبوط حسب المنصة
    print("✅ Bot is running with webhook...")

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=app.run_polling()

    )


if __name__ == "__main__":
    main()
