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
# from config import BOT_TOKEN

BOT_TOKEN = "8107170808:AAGebZU8yqKjkk0PZEB456CKdH-VZcwsY1Y"

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Состояния для ConversationHandler ---
WAITING_FOR_ITEM = 1

# --- Загрузка данных ---
def load_recycling_points():
    with open('data/recycling_points.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_waste_dictionary():
    with open('data/waste_dictionary.json', 'r', encoding='utf-8') as f:
        return json.load(f)

RECYCLING_POINTS = load_recycling_points()
WASTE_DICTIONARY = load_waste_dictionary()

# --- Глобальные переменные для текста ---
SORTING_GUIDE = """
📚 **Как правильно сортировать мусор?**

*Пластик (маркировка 1, 2, 4, 5):*
• Промойте от остатков пищи.
• Снимите крышки (они часто из другого пластика).
• Смните бутылку, чтобы уменьшить объем.

*Стекло:*
• Промойте банки и бутылки.
• Не нужно снимать этикетки.

*Бумага и картон:*
• Убедитесь, что бумага сухая и чиная.
• Удалите скотч, пластиковые вставки, скрепки.
• Глянцевые журналы и чеки не подходят для переработки.

*Металл:*
• Алюминиевые и жестяные банки сполосните и смните.

*Опасные отходы (батарейки, лампы):*
• Ни в коем случае не выбрасывайте в общий мусор!
• Относите в специальные пункты приема.
"""

USEFUL_LINKS = """
🔗 *Полезные ресурсы и сообщества:*

• «РазДельный Сбор Оренбург» (VK) - https://vk.com/rsbor
• Карта RecycleMap (пункты приема по всей России) - https://recyclemap.ru/
• «РазДельный Сбор Москва» (VK) - https://vk.com/rsbor_msk

*Следи за новостями!* В городе появляются новые контейнеры и акции.
"""

# --- Вспомогательные функции ---
def main_menu_keyboard():
    """Создает клавиатуру главного меню."""
    keyboard = [
        [KeyboardButton("♻️ Пункты приема"), KeyboardButton("📚 Как сортировать?")],
        [KeyboardButton("❓ Что куда?"), KeyboardButton("🔗 Полезные ссылки")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Обработчики команд и сообщений ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start и показывает главное меню."""
    welcome_text = """
    Привет, житель Оренбурга! 🌍
Я, EcoOrenBot, помогу тебе разобраться в раздельном сборе мусора.
Выбери нужный пункт в меню ниже:
    """
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

async def recycling_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню для выбора категории отходов."""
    keyboard = [
        [KeyboardButton("Пластик"), KeyboardButton("Стекло"), KeyboardButton("Бумага")],
        [KeyboardButton("Металл"), KeyboardButton("Батарейки"), KeyboardButton("⬅️ Назад")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери категорию отходов:", reply_markup=reply_markup)

async def show_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие на кнопку категории отходов и выдает адреса."""
    user_choice = update.message.text.lower()
    
    # Сопоставление русских названий с ключами JSON
    category_mapping = {
        "пластик": "plastic",
        "стекло": "glass", 
        "бумага": "paper",
        "металл": "metal",
        "батарейки": "batteries"
    }

    # Проверяем "назад" в разных вариантах написания
    if "⬅️" in user_choice or "назад" in user_choice:
        await start(update, context)
        return

    category_key = category_mapping.get(user_choice)
    
    if not category_key or category_key not in RECYCLING_POINTS:
        await update.message.reply_text(f"Категория '{update.message.text}' не найдена.")
        return

    category_data = RECYCLING_POINTS[category_key]
    response = f"♻️ Пункты приема *{category_data['category_name']}*:\n\n"

    for i, point in enumerate(category_data["points"], 1):
        response += f"*{i}. {point['name']}*\n"
        response += f"📍 Адрес: {point['address']}\n"
        # Используем .get() чтобы избежать KeyError если ключей нет
        response += f"🕒 Часы работы: {point.get('working_hours', 'не указано')}\n"
        response += f"🔗 Ссылка: {point.get('link', 'нет ссылки')}\n\n"

    await update.message.reply_text(response)

async def sorting_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает инструкцию по сортировке."""
    await update.message.reply_text(SORTING_GUIDE)

async def what_where(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запускает интерактивный режим 'Что куда?'."""
    await update.message.reply_text(
        "Введи название предмета, чтобы узнать, как его утилизировать (например, 'бутылка', 'батарейка').\n"
        "Для отмены напиши /cancel."
    )
    return WAITING_FOR_ITEM

async def handle_waste_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает введенный пользователем предмет."""
    user_input = update.message.text.lower().strip()
    item_data = WASTE_DICTIONARY.get(user_input)

    if item_data:
        response = (
            f"*{user_input.capitalize()}*:\n\n"
            f"🗂️ Категория: *{item_data['category']}*\n"
            f"📌 Инструкция: {item_data['instruction']}"
        )
    else:
        response = (
            f"🤔 Не могу найти информацию о '{user_input}'.\n"
            "Попробуй ввести другое название или убедись, что предмет подлежит переработке."
        )

    await update.message.reply_text(response)
    return WAITING_FOR_ITEM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text("Диалог отменен.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def useful_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает полезные ссылки."""
    await update.message.reply_text(USEFUL_LINKS)

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок главного меню."""
    text = update.message.text
    if text == "♻️ Пункты приема":
        await recycling_points(update, context)
    elif text == "📚 Как сортировать?":
        await sorting_guide(update, context)
    elif text == "❓ Что куда?":
        await what_where(update, context)
    elif text == "🔗 Полезные ссылки":
        await useful_links(update, context)
    elif "⬅️" in text or text.lower() == "назад":
        await start(update, context)
    else:
        # Если это не кнопки главного меню, возможно это кнопки из других меню
        # которые должны обрабатываться другими обработчиками
        # Поэтому не отвечаем здесь
        pass

def main() -> None:
    """Основная функция, запускающая бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # ConversationHandler для интерактивного режима "Что куда?"
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(❓ Что куда?)$"), what_where)],
        states={
            WAITING_FOR_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_waste_item)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # ВАЖНО: Сначала специфичные обработчики, потом общие
    
    # 1. Обработчик для кнопок категорий (Пластик, Стекло и т.д.)
    application.add_handler(MessageHandler(filters.Regex("^(Пластик|Стекло|Бумага|Металл|Батарейки)$"), show_point))
    
    # 2. Обработчик для кнопки "Назад" из меню категорий
    application.add_handler(MessageHandler(filters.Regex("^(⬅️ Назад)$"), 
                                          lambda u, c: start(u, c)))
    
    # 3. Обработчик для кнопок главного меню (только для главного меню)
    application.add_handler(MessageHandler(
        filters.Regex("^(♻️ Пункты приема|📚 Как сортировать\?|❓ Что куда\?|🔗 Полезные ссылки)$"), 
        handle_main_menu
    ))
    
    # 4. Обработчик для кнопки "Назад" в главном меню
    application.add_handler(MessageHandler(
        filters.Regex("^(⬅️ назад|⬅️ Назад)$"), 
        lambda u, c: start(u, c)
    ))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()