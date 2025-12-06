import logging
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

BOT_TOKEN = "8107170808:AAGebZU8yqKjkk0PZEB456CKdH-VZcwsY1Y"

# --- Логи ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Состояния ---
WAITING_FOR_ITEM = 1

# --- Загрузка данных ---
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

RECYCLING_POINTS = load_json("data/recycling_points.json")
WASTE_DICTIONARY = load_json("data/waste_dictionary.json")

# --- Клавиатуры ---
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("♻️ Пункты приема"), KeyboardButton("📚 Как сортировать?")],
            [KeyboardButton("❓ Что куда?"), KeyboardButton("🔗 Полезные ссылки")],
        ],
        resize_keyboard=True
    )

def recycling_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Пластик", "Стекло", "Бумага"],
            ["Металл", "Батарейки"],
            ["⬅️ Назад"]
        ],
        resize_keyboard=True
    )

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я EcoOrenBot 🌿\nВыбери нужный пункт меню:",
        reply_markup=main_menu_keyboard()
    )

# --- Пункты приема ---
async def recycling_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери категорию отходов:",
        reply_markup=recycling_menu_keyboard()
    )

async def show_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    mapping = {
        "пластик": "plastic",
        "стекло": "glass",
        "бумага": "paper",
        "металл": "metal",
        "батарейки": "batteries"
    }

    if text == "⬅️ назад":
        return await start(update, context)

    key = mapping.get(text)

    if not key or key not in RECYCLING_POINTS:
        return await update.message.reply_text("Категория не найдена.")

    category = RECYCLING_POINTS[key]
    response = f"♻️ Пункты приема *{category['category_name']}*:\n\n"

    for i, point in enumerate(category["points"], 1):
        response += f"*{i}. {point.get('name', '—')}*\n"
        response += f"📍 {point.get('address', 'Адрес не указан')}\n"
        if "working_hours" in point:
            response += f"🕒 {point['working_hours']}\n"
        if "link" in point:
            response += f"🔗 {point['link']}\n"
        response += "\n"

    await update.message.reply_text(response)

# --- Как сортировать ---
SORTING_GUIDE = """
📚 *Как правильно сортировать мусор?*

*Пластик:* промыть, снять крышки, сплющить.
*Стекло:* промыть, не нужно снимать этикетки.
*Бумага:* должна быть чистой и сухой, глянец и чеки — нельзя.
*Металл:* промыть, смять банки.
*Опасные отходы:* сдавать ТОЛЬКО в спецпункты.
"""

async def sorting_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SORTING_GUIDE)

# --- Что куда? ---
async def what_where(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введи название предмета (например: «бутылка», «батарейка»).\n"
        "Для выхода напиши /cancel."
    )
    return WAITING_FOR_ITEM

async def handle_waste_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Игнорируем кнопки главного меню, чтобы они не попадали в поиск
    if text in ["♻️ Пункты приема", "📚 Как сортировать?", "❓ Что куда?", "🔗 Полезные ссылки", "⬅️ Назад"]:
        return ConversationHandler.END

    item = WASTE_DICTIONARY.get(text.lower())
    if item:
        response = (
            f"*{text.capitalize()}*\n\n"
            f"🗂 Категория: *{item['category']}*\n"
            f"📌 {item['instruction']}"
        )
    else:
        response = f"Не нашёл информацию о «{text}».\nПопробуй другое название."

    await update.message.reply_text(response)
    return WAITING_FOR_ITEM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

# --- Полезные ссылки ---
USEFUL_LINKS = """
🔗 *Полезные ресурсы:*
• RecycleMap — карта пунктов приёма: https://recyclemap.ru/
• РазДельный Сбор (Оренбург): https://vk.com/rsbor
"""

async def useful_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(USEFUL_LINKS)

# --- Главное меню ---
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    handlers = {
        "♻️ Пункты приема": recycling_points,
        "📚 Как сортировать?": sorting_guide,
        "❓ Что куда?": what_where,
        "🔗 Полезные ссылки": useful_links
    }

    if text in handlers:
        return await handlers[text](update, context)

    await update.message.reply_text(
        "Не понял. Используй меню ниже.",
        reply_markup=main_menu_keyboard()
    )

# --- Запуск ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Диалог "Что куда?"
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❓ Что куда\\?$"), what_where)],
        states={
            WAITING_FOR_ITEM: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_waste_item
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        block=False  # <-- ВАЖНО 🔥
    )
    application.add_handler(conv_handler)

    # Обработка категорий приёма
    application.add_handler(
        MessageHandler(
            filters.Regex("^(Пластик|Стекло|Бумага|Металл|Батарейки|⬅️ Назад)$"),
            show_point
        )
    )

    # Главное меню
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )

    application.add_handler(CommandHandler("start", start))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
