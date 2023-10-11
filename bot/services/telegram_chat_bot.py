from django.conf import settings
from django.utils.translation import gettext_lazy as _

from telegram.ext import MessageHandler, Filters, Dispatcher
from telegram import (
    Update,
    Bot,
)

from bot.models import UserChatSetting


class BotCommandStatus:
    CHECK_PHONE = 0
    START_CHAT = 1


class TelegramBot(object):
    help = _("Chat Bot")

    @staticmethod
    def echo_handler(update, context):
        UserChatSetting.objects.filter(
            bot_token=update.message.text
        ).update(chat_id=update.message.chat_id)


def setup_dispatcher(dispatchers):
    """
    Adding handlers for events from Telegram
    """
    dispatchers.add_handler(MessageHandler(Filters.text & (~Filters.command) & Filters.chat_type.private, TelegramBot.echo_handler))

    return dispatchers


if settings.TELEGRAM_BOT_TOKEN:
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)

    dispatcher = setup_dispatcher(
        Dispatcher(
            bot,
            update_queue=None,
        )
    )


def process_telegram_event(update_json):
    # processing current command states
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)
