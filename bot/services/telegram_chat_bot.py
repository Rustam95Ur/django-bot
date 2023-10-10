# import uuid
#
# from django.core.cache import cache
# from django.conf import settings
# from django.utils.translation import gettext_lazy as _
# from django.utils.translation import activate
#
# from order.models import ChatHistory
# from order.constants import CHAT_IMAGE_PATH
# from order.services.send_notify import convert_text_before_sending_telegram_api
#
# from profiles.models import ManagerProfile, ManagerUserChat
# from profiles.tasks import (
#     send_message_to_socket,
#     send_manager_chat_data_to_socket,
# )
#
# from telegram.ext import (
#     Dispatcher,
#     Filters,
#     CommandHandler,
#     MessageHandler,
#     ConversationHandler,
# )
# from telegram import (
#     ParseMode,
#     Update,
#     KeyboardButton,
#     ReplyKeyboardMarkup,
#     Bot,
# )
# from telegram.ext import CallbackContext
#
#
# class BotCommandStatus:
#     CHECK_PHONE = 0
#     START_CHAT = 1
#
#
# class TelegramBot(object):
#     help = _("Manager Chat Bot")
#
#     @staticmethod
#     def start(update: Update, context: CallbackContext):
#         # activate translate
#         activate(update.message.from_user.language_code)
#
#         button_phone = KeyboardButton(
#             text=str(_("Submit phone number 📱️")), request_contact=True
#         )
#         keyboard = ReplyKeyboardMarkup(
#             keyboard=[[button_phone]],
#             resize_keyboard=True,
#             one_time_keyboard=True,
#         )
#         update.message.reply_text(
#             str(_("To enter, click the 'Submit phone number' button")),
#             reply_markup=keyboard,
#         )
#         return BotCommandStatus.CHECK_PHONE
#
#     @staticmethod
#     def check_contact(update: Update, context: CallbackContext):
#         phone = update.message.contact.phone_number
#         # check manager exist
#         manager = (
#             ManagerProfile.objects.filter(user__phone__contains=phone)
#             .select_related("user")
#             .first()
#         )
#         if manager is None:
#             update.message.reply_text(
#                 str(_("You have not permission")),
#             )
#             return ConversationHandler.END
#
#         # update chat id for manager
#         if manager.chat_id is None:
#             manager.chat_id = update.message.chat_id
#             manager.save()
#
#         # get active chat for manager
#         active_chat = manager.manager_chats.filter(is_finish=False).first()
#         if active_chat is None:
#             update.message.reply_text(
#                 str(_("You don't have active chats")),
#             )
#             return ConversationHandler.END
#
#         # get customer messages
#         last_messages = ChatHistory.objects.filter(
#             room_name=active_chat.id
#         ).order_by("created")
#
#         # reply all messages
#         for message in last_messages:
#             sender_message = convert_text_before_sending_telegram_api(
#                 message=message.message,
#                 is_bot=message.is_bot,
#                 sender=message.sender,
#             )
#             update.message.reply_text(
#                 sender_message, parse_mode=ParseMode.HTML
#             )
#
#         chat_obj = {
#             "active_chat_id": active_chat.id,
#             "manager_id": manager.user.id,
#             "user_id": active_chat.user_id,
#         }
#         cache.set(
#             f"telegram_chat_{update.message.chat_id}", chat_obj, timeout=300
#         )
#         # send to the socket information about the manager.
#         # In order to display on the front that the manager is connected
#         # to the chat
#         send_manager_chat_data_to_socket.delay(active_chat.id)
#         return BotCommandStatus.START_CHAT
#
#     @staticmethod
#     def end_chat(update: Update, context: CallbackContext):
#         # updated chat status and close chat
#         chat_info = cache.get(f"telegram_chat_{update.message.chat_id}")
#
#         if chat_info is None:
#             # if the data is not in the cache,
#             # restart the chat to update the data in the cache
#             update.message.reply_text(
#                 str(
#                     _(
#                         "Sorry, an error occurred, "
#                         "please try sending your phone number again"
#                     )
#                 ),
#             )
#             return TelegramBot.start(update, context)
#
#         ManagerUserChat.objects.filter(id=chat_info["active_chat_id"]).update(
#             is_finish=True
#         )
#         update.message.reply_text(
#             str(_("Good bye")),
#         )
#         # send to the socket information about the manager.
#         # In order to display on the front that the chat is close
#         send_manager_chat_data_to_socket.delay(chat_info["active_chat_id"])
#         cache.delete(f"telegram_chat_{update.message.chat_id}")
#         return ConversationHandler.END
#
#     @staticmethod
#     def start_chat(update: Update, context: CallbackContext):
#         # close chat after send command
#         if update.message.text == "/end_chat":
#             return TelegramBot.end_chat(update, context)
#
#         elif update.message.text == "/start":
#             # ignore /start text command
#             return
#
#         chat_info = cache.get(f"telegram_chat_{update.message.chat_id}")
#
#         if chat_info is None:
#             # if the data is not in the cache,
#             # restart the chat to update the data in the cache
#             update.message.reply_text(
#                 str(
#                     _(
#                         "Sorry, an error occurred, "
#                         "please try sending your phone number again"
#                     )
#                 ),
#             )
#             return TelegramBot.start(update, context)
#
#         # save chat and send message in socket
#         chat_history_data = {
#             "room_name": chat_info["active_chat_id"],
#             "message": update.message.text,
#             "sender_id": chat_info["manager_id"],
#         }
#         if update.message.photo:
#             # generates uuid file name and
#             # downloads photo in media root directory
#             photo = update.message.photo[-1].file_id
#             image_name = "{}/{}.jpg".format(CHAT_IMAGE_PATH, uuid.uuid4())
#             media_path = "{}/{}".format(settings.MEDIA_ROOT, image_name)
#             context.bot.get_file(photo).download(custom_path=media_path)
#             chat_history_data["image"] = image_name
#         chat = ChatHistory.objects.create(**chat_history_data)
#
#         send_message_to_socket.delay(chat.id, chat_info["user_id"])
#
#         cache.set(
#             f"telegram_chat_{update.message.chat_id}", chat_info, timeout=300
#         )
#
#
# def setup_dispatcher(dispatchers):
#     """
#     Adding handlers for events from Telegram
#     """
#     conversation_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", TelegramBot.start)],
#         states={
#             BotCommandStatus.CHECK_PHONE: [
#                 MessageHandler(Filters.contact, TelegramBot.check_contact)
#             ],
#             BotCommandStatus.START_CHAT: [
#                 MessageHandler(
#                     Filters.text | Filters.command | Filters.photo,
#                     TelegramBot.start_chat,
#                 )
#             ],
#         },
#         fallbacks=[CommandHandler("end_chat", TelegramBot.end_chat)],
#     )
#
#     dispatchers.add_handler(conversation_handler)
#
#     return dispatchers
#
#
# if settings.TELEGRAM_CHAT_BOT_TOKEN:
#     bot = Bot(settings.TELEGRAM_CHAT_BOT_TOKEN)
#
#     dispatcher = setup_dispatcher(
#         Dispatcher(
#             bot,
#             update_queue=None,
#         )
#     )
#
#
# @app.task(ignore_result=True)
# def process_telegram_event(update_json):
#     # processing current command states
#     update = Update.de_json(update_json, bot)
#     dispatcher.process_update(update)


def process_telegram_event():
    pass