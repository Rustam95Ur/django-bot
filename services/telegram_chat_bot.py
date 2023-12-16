from django.conf import settings
from django.utils.translation import gettext_lazy as _

from telegram.ext import (
    MessageHandler,
    Filters,
    Dispatcher,
    CommandHandler,
    ConversationHandler,
    CallbackContext,
)
from telegram import (
    Update,
    Bot,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from common_users.models import CommonUser


class BotCommandStatus:
    """BotCommandStatus"""

    UPDATE_PHONE = 0
    START_CHAT = 1


class TelegramBot(object):
    help = _("Chat Bot")

    @staticmethod
    def start_command(update: Update, context: CallbackContext):
        user, created = CommonUser.objects.get_or_create(
            chat_id=update.message.chat_id
        )

        if created:
            button_phone = KeyboardButton(
                text=str(_("Submit phone number 📱️")), request_contact=True
            )
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[button_phone]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            update.message.reply_text(
                text=str(
                    _("To enter, click the 'Submit phone number' button")
                ),
                reply_markup=keyboard,
            )
            return BotCommandStatus.UPDATE_PHONE

        else:
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📋 Каталог", callback_data="catalog"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🛒Корзина", callback_data="Корзина"
                        )
                    ],
                    [InlineKeyboardButton("🗣 FAQ", callback_data="faq")],
                ]
            )
            text = "Выберете действие:"
            update.message.reply_text(
                text=text,
                reply_markup=keyboard,
            )
            return BotCommandStatus.START_CHAT

    @staticmethod
    def update_phone(update: Update, context: CallbackContext):
        phone = update.message.contact.phone_number
        # check manager exist
        CommonUser.objects.filter(chat_id=update.message.chat_id).update(
            phone=phone,
            first_name=update.message.contact.first_name,
            last_name=update.message.contact.last_name,
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📋 Каталог", callback_data="catalog")],
                [InlineKeyboardButton("🛒Корзина", callback_data="Корзина")],
                [InlineKeyboardButton("🗣 FAQ", callback_data="faq")],
            ]
        )
        text = "Выберете действие:"
        update.message.reply_text(
            text=text,
            reply_markup=keyboard,
        )

        return BotCommandStatus.START_CHAT

    @staticmethod
    def end_chat(update: Update, context: CallbackContext):
        return ConversationHandler.END

    @staticmethod
    def start_chat(update: Update, context: CallbackContext):
        return

        # if update.message.text == "/start":
        #     # ignore /start text command
        #     return

        # chat_info = cache.get(f"telegram_chat_{update.message.chat_id}")

        # if chat_info is None:
        #     # if the data is not in the cache,
        #     # restart the chat to update the data in the cache
        #     update.message.reply_text(
        #         str(
        #             _(
        #                 "Sorry, an error occurred, "
        #                 "please try sending your phone number again"
        #             )
        #         ),
        #     )
        #     return TelegramBot.start(update, context)

        # save chat and send message in socket
        # chat_history_data = {
        #     "room_name": chat_info["active_chat_id"],
        #     "message": update.message.text,
        #     "sender_id": chat_info["manager_id"],
        # }
        # if update.message.photo:
        #     # generates uuid file name and
        #     # downloads photo in media root directory
        #     photo = update.message.photo[-1].file_id
        #     image_name = "{}/{}.jpg".format(CHAT_IMAGE_PATH, uuid.uuid4())
        #     media_path = "{}/{}".format(settings.MEDIA_ROOT, image_name)
        #     context.bot.get_file(photo).download(custom_path=media_path)
        #     chat_history_data["image"] = image_name


def setup_dispatcher(dispatchers):
    """
    Adding handlers for events from Telegram
    """
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", TelegramBot.start_command)],
        states={
            BotCommandStatus.UPDATE_PHONE: [
                MessageHandler(Filters.contact, TelegramBot.update_phone)
            ],
            BotCommandStatus.START_CHAT: [
                MessageHandler(
                    Filters.text | Filters.command | Filters.photo,
                    TelegramBot.start_chat,
                )
            ],
        },
        fallbacks=[CommandHandler("end_chat", TelegramBot.end_chat)],
    )

    dispatchers.add_handler(conversation_handler)

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
