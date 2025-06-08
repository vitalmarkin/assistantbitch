# telegram_bot.py (для python-telegram-bot v20+)

import logging
import requests
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Конфигурация Moloco Ads ===
MOLOCO_API_KEY = 'ca_YfDepYTSy1nKjU55p58EQd81rOIdPGYXZHMuc'
MOLOCO_AD_ACCOUNT_IDS = [
    {'id': 'n1yFBuHnhBy9hoez', 'name': 'Sasha'},
    {'id': 'HJRJQVszZuxX47Ne', 'name': 'Artur'},
    {'id': 'gW82pu0w3sJG7OFQ', 'name': 'Nikita'}
]

# === Функции для работы с Moloco Ads API ===
def get_moloco_access_token(api_key: str) -> str:
    url = 'https://api.moloco.cloud/cm/v1/auth/tokens'
    resp = requests.post(url, json={'api_key': api_key})
    resp.raise_for_status()
    return resp.json().get('token', '')


def get_moloco_spend_by_account(ad_account_id: str, token: str, target_date: str) -> float:
    url = 'https://api.moloco.cloud/cm/v1/analytics-detail'
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'ad_account_id': ad_account_id,
        'date_range': {'start': target_date, 'end': target_date},
        'dimensions': ['CAMPAIGN_ID'],
        'metrics': ['SPEND']
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    rows = resp.json().get('rows', [])
    return sum(float(r.get('metric', {}).get('spend', 0)) for r in rows)

# === Обработчики Telegram ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Moloco", callback_data='moloco')],
        [InlineKeyboardButton("Keitaro", callback_data='keitaro')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите раздел:', reply_markup=reply_markup)

async def moloco_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработка команды /moloco как нажатие кнопки Moloco
    query = update.message
    keyboard = [
        [InlineKeyboardButton("Расход", callback_data='moloco_expense')],
        [InlineKeyboardButton("Статистика", callback_data='moloco_stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.reply_text('Moloco: выберите опцию', reply_markup=reply_markup)

async def keitaro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработка команды /keitaro как нажатие кнопки Keitaro
    query = update.message
    keyboard = [
        [InlineKeyboardButton("Доход", callback_data='keitaro_revenue')],
        [InlineKeyboardButton("Статистика", callback_data='keitaro_stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.reply_text('Keitaro: выберите опцию', reply_markup=reply_markup)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Pong! Бот работает.')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'moloco':
        # Inline handles for callback
        keyboard = [
            [InlineKeyboardButton("Расход", callback_data='moloco_expense')],
            [InlineKeyboardButton("Статистика", callback_data='moloco_stats')]
        ]
        await query.edit_message_text('Moloco: выберите опцию', reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == 'keitaro':
        keyboard = [
            [InlineKeyboardButton("Доход", callback_data='keitaro_revenue')],
            [InlineKeyboardButton("Статистика", callback_data='keitaro_stats')]
        ]
        await query.edit_message_text('Keitaro: выберите опцию', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == 'moloco_expense':
        keyboard = [
            [InlineKeyboardButton("Вчера", callback_data='moloco_exp_yesterday')],
            [InlineKeyboardButton("Сегодня", callback_data='moloco_exp_today')]
        ]
        await query.edit_message_text('Moloco Расход: выберите день', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data in ('moloco_exp_yesterday', 'moloco_exp_today'):
        now = datetime.now(timezone.utc)
        target = (now - timedelta(days=1)).date() if data.endswith('yesterday') else now.date()
        target_date = target.isoformat()
        try:
            token = get_moloco_access_token(MOLOCO_API_KEY)
            lines = [f"Moloco Расход за {target_date}:\n"]
            for acc in MOLOCO_AD_ACCOUNT_IDS:
                spend = get_moloco_spend_by_account(acc['id'], token, target_date)
                lines.append(f"- {acc['name']}: {spend:.2f}")
            await query.edit_message_text("\n".join(lines))
        except Exception as e:
            logger.error(f"Moloco expense error: {e}")
            await query.edit_message_text('❌ Ошибка получения расхода Moloco.')
        return

    if data == 'moloco_stats':
        await query.edit_message_text('Moloco Статистика: (логика ещё не реализована)')
        return
    if data == 'keitaro_revenue':
        await query.edit_message_text('Keitaro Доход: (логика ещё не реализована)')
        return
    if data == 'keitaro_stats':
        await query.edit_message_text('Keitaro Статистика: (логика ещё не реализована)')
        return

# === Запуск бота и установка меню команд ===
BOT_TOKEN = "8165454065:AAEIAOwYdR3uLhKYvj3FjJHfn3p9LXx_yoY"

async def setup_commands(app):
    commands = [
        BotCommand("moloco", "Moloco раздел"),
        BotCommand("keitaro", "Keitaro раздел")
    ]
    await app.bot.set_my_commands(commands)


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('ping', ping))
    app.add_handler(CommandHandler('moloco', moloco_command))
    app.add_handler(CommandHandler('keitaro', keitaro_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()
