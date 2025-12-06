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

    # Обработчик для кнопок с пунктами приема с отладкой
    async def debug_show_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"DEBUG: Кнопка '{update.message.text}' попала в обработчик show_point!")
        return await show_point(update, context)
    
    application.add_handler(MessageHandler(filters.Regex("^(Пластик|Стекло|Бумага|Металл|Батарейки)$"), debug_show_point))

    # Обработчик для кнопки "Назад" с отладкой
    async def debug_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"DEBUG: Кнопка 'Назад' нажата")
        await start(update, context)
    
    application.add_handler(MessageHandler(filters.Regex("^(⬅️ Назад)$"), debug_back))

    # Обработчик для всех остальных текстовых сообщений с отладкой
    async def debug_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"DEBUG: Текст '{update.message.text}' попал в общий обработчик")
        return await handle_main_menu(update, context)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, debug_main_menu))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()