import logging
import textwrap
import re

from more_itertools import chunked
from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
    PreCheckoutQueryHandler,
)

from common_users.services.bot_tools import (
    add_product_to_cart,
    build_menu,
    create_client,
    create_order,
    get_cart_products_info,
    get_catigories,
    get_mailing,
    get_product_detail,
    get_product_info_for_payment,
    get_product_name,
    get_products,
    get_text_faq,
    remove_product_from_cart,
    upload_to_exel,
)


(
    HANDLE_CATEGORIES,
    HANDLE_CART,
    HANDLE_DESCRIPTION,
    HANDLE_MENU,
    HANDLE_SUB_CATEGORIES,
    HANDLE_PRODUCTS,
    HANDLE_USER_REPLY,
    HANDLE_WAITING,
    START_OVER,
) = range(9)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def get_chat_member(update, context):
    subscription_channel_id = 1
    subscription_channel_link = "Test"
    user_status_chanel = await context.bot.get_chat_member(
        chat_id=subscription_channel_id, user_id=update.effective_chat.id
    )

    if "left" in user_status_chanel["status"]:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Наш канал", subscription_channel_link)]]
        )
        await context.bot.send_message(
            text="Сначала нужно подписаться на наш канал",
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup,
        )
        return True


async def start(update, context):
    text = "Выберете действие:"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="📋 Свободные места", callback_data="catalog"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Мой брони", callback_data="Корзина"
                )
            ],
            [InlineKeyboardButton(text="🗣 FAQ", callback_data="faq")],
            [
                InlineKeyboardButton(
                    text="🛠 Тех. поддержка", callback_data="tech_support"
                )
            ],
        ]
    )
    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text, reply_markup=keyboard
        )

    # elif await get_chat_member(update, context):
    #     return
    else:
        telegram_user_id = update.effective_user.id
        username = update.effective_user.username
        context.user_data["tg_user_id"] = telegram_user_id
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        await create_client(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

        await update.message.reply_text(
            textwrap.dedent(
                f"""
        <b>Здравствуйте {first_name}!</b>
         Добро пожаловать "iPark"
        """
            ),
            parse_mode=ParseMode.HTML,
        )

        await update.message.reply_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )
    context.user_data[START_OVER] = True

    return HANDLE_CATEGORIES


async def show_main_page(update, context, super_category_id):
    context.user_data["current_page"] = 0

    menu = await get_menu(context.user_data["current_page"], super_category_id)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите категорию:", reply_markup=menu
    )


async def show_next_page(update, context, super_category_id):
    context.user_data["current_page"] += 1
    menu = await get_menu(context.user_data["current_page"], super_category_id)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите категорию:", reply_markup=menu
    )


async def show_previos_page(update, context, super_category_id):
    context.user_data["current_page"] -= 1
    menu = await get_menu(context.user_data["current_page"], super_category_id)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите категорию:", reply_markup=menu
    )


async def get_menu(current_page, category_id):
    categories = await get_catigories(category_id)

    categories_per_page = 4
    categories_group = list(chunked(categories, categories_per_page))

    keyboard = [
        InlineKeyboardButton(category.name, callback_data=category.id)
        for category in categories_group[current_page]
    ]
    footer_buttons = []
    if current_page > 0:
        footer_buttons.insert(
            0, InlineKeyboardButton("<<<", callback_data="prev")
        )
    if current_page < len(categories_group) - 1:
        footer_buttons.append(
            InlineKeyboardButton(">>>", callback_data="next")
        )
    if category_id:
        footer_buttons.append(
            InlineKeyboardButton("Назад", callback_data="Назад")
        )
    footer_buttons.append(
        InlineKeyboardButton("Главное меню", callback_data="Главное меню")
    )
    return InlineKeyboardMarkup(
        build_menu(keyboard, n_cols=2, footer_buttons=footer_buttons)
    )


async def handle_categories(update, context):
    context.user_data["super_category_id"] = None
    super_category_id = context.user_data["super_category_id"]
    if update.callback_query.data in ("catalog", "Назад"):
        await show_main_page(update, context, super_category_id)

    elif update.callback_query.data == "next":
        await show_next_page(update, context, super_category_id)

    elif update.callback_query.data == "prev":
        await show_previos_page(update, context, super_category_id)
    return HANDLE_SUB_CATEGORIES


async def handle_sub_categories(update, context):
    if update.callback_query.data == "next":
        super_category_id = context.user_data["super_category_id"]
        await show_next_page(update, context, super_category_id)

    elif update.callback_query.data == "prev":
        super_category_id = context.user_data["super_category_id"]
        await show_previos_page(update, context, super_category_id)

    elif re.match(r"[0-9]", update.callback_query.data):
        context.user_data["super_category_id"] = update.callback_query.data
        super_category_id = context.user_data["super_category_id"]
        await show_main_page(update, context, super_category_id)

    elif update.callback_query.data == "Назад":
        super_category_id = context.user_data["super_category_id"]
        await show_main_page(update, context, super_category_id)
    return HANDLE_PRODUCTS


async def handle_products(update, context):
    product_category = update.callback_query.data
    products_category = await get_products(product_category)
    products_num = len(products_category)
    for product in products_category:
        put_cart_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Добавить в корзину", callback_data=product.id
                    )
                ]
            ]
        )
        if not product.image:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_product_detail(product),
                reply_markup=put_cart_button,
                parse_mode=ParseMode.HTML,
            )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=product.image,
                caption=get_product_detail(product),
                reply_markup=put_cart_button,
                parse_mode=ParseMode.HTML,
            )
    keyboard = [
        [
            InlineKeyboardButton("Назад", callback_data="Назад"),
            InlineKeyboardButton("Главное меню", callback_data="Главное меню"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        text=f"Показано товаров: {products_num}",
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


async def handle_product_detail(update, context):
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Назад", callback_data="Назад")]]
    )
    product_id = update.callback_query.data
    context.user_data["product_id"] = product_id
    product_detais = await get_product_name(product_id)
    context.user_data["product_detais"] = product_detais
    await context.bot.send_message(
        text=f"{product_detais}\nВведите количество:",
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return HANDLE_CART


async def check_quantity(update, context):
    quantity = update.message.text
    if re.match(r"[0-9]", quantity):
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Назад", callback_data="Назад"),
                    InlineKeyboardButton(
                        "Подтвердить", callback_data="Подтвердить"
                    ),
                ]
            ]
        )
        product_detais = context.user_data["product_detais"]
        context.user_data["quantity"] = quantity
        await context.bot.send_message(
            text=textwrap.dedent(
                f"""
            Вы выбрали {product_detais}  {quantity} шт.
            """
            ),
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        await context.bot.send_message(
            text=textwrap.dedent(
                """
            <b>Количество должно быть числом</b>
            \n<b>Введите количество</b>
            """
            ),
            chat_id=update.effective_chat.id,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_CART


async def add_cart(update, context):
    if update.callback_query.data == "Категории":
        await show_main_page(update, context, super_category_id=None)
        return HANDLE_CATEGORIES
    elif update.callback_query.data == "Назад":
        super_category_id = context.user_data["super_category_id"]
        await show_main_page(update, context, super_category_id)
        return HANDLE_PRODUCTS
    else:
        product_to_cart = await add_product_to_cart(context)
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Категории", callback_data="Категории"
                    ),
                    InlineKeyboardButton("Корзина", callback_data="Корзина"),
                    InlineKeyboardButton("Назад", callback_data="Назад"),
                ]
            ]
        )
        await context.bot.send_message(
            text=product_to_cart,
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )


async def show_cart_info(update, context):
    products = await get_cart_products_info(context)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=products)


async def handle_cart(update, context):
    back = [InlineKeyboardButton("Назад", callback_data="Назад")]
    delivery_address = [
        InlineKeyboardButton(
            "Добавить адрес для доставки", callback_data="delivery_address"
        )
    ]
    if "cart" not in context.user_data:
        await update.callback_query.answer("Пустая корзина")
        return
    else:
        products_info, products = await get_cart_products_info(context)
        keyboard = []
        for position, product in enumerate(products, start=1):
            keyboard.append(
                InlineKeyboardButton(
                    f"Удалить позицию №{position}", callback_data=product.id
                )
            )
        keyboard_groups = build_menu(keyboard, n_cols=2)
        keyboard_groups.append(back)
        keyboard_groups.append(delivery_address)
        reply_markup = InlineKeyboardMarkup(keyboard_groups)
        await update.callback_query.edit_message_text(
            text=products_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_MENU


async def remove_product(update, context):
    product_id = update.callback_query.data
    context.user_data["product_id"] = product_id
    await remove_product_from_cart(context)
    await update.callback_query.answer("Товар удален из корзины")
    await handle_cart(update, context)
    return HANDLE_MENU


async def add_delivery_address(update, context):
    keyboard = [
        [InlineKeyboardButton("Корзина", callback_data="Корзина")],
        [InlineKeyboardButton("Назад", callback_data="Назад")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Хорошо, для доставки товаров пришлите нам ваш адрес текстом",
        reply_markup=reply_markup,
    )
    return HANDLE_WAITING


async def check_address_text(update, context):
    address = update.message.text
    context.user_data["address"] = address
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Верно", callback_data="Верно")],
            [
                InlineKeyboardButton(
                    "Ввести снова", callback_data="Ввести снова"
                )
            ],
        ]
    )
    await context.bot.send_message(
        text=f"Вы ввели: <b>{address}</b>",
        chat_id=update.message.chat_id,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return HANDLE_WAITING


async def save_customer(update, context):
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Оплатить", callback_data="Оплатить")],
            [
                InlineKeyboardButton(
                    "Главное меню", callback_data="Главное меню"
                )
            ],
        ]
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Ваш адрес успешно сохранен, теперь можите оплатить ваш заказ",
        reply_markup=reply_markup,
    )
    return HANDLE_MENU


async def handle_user_payment(update, context):
    order_info = await get_product_info_for_payment(context)
    chat_id = update.effective_user.id
    title = 'Оплата товаров "Магазин в Телеграме"'
    description = order_info["products_info"]
    payload = "telegram-store"
    currency = "RUB"
    price = order_info["total_order_price"]
    payment_token = settings.PAYMENT_TOKEN
    prices = [LabeledPrice("Оплата товаров", int(price) * 100)]
    await context.bot.send_invoice(
        chat_id, title, description, payload, payment_token, currency, prices
    )
    return HANDLE_USER_REPLY


async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != "telegram-store":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)
    return HANDLE_USER_REPLY


async def successful_payment_callback(update, context):
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Назад", callback_data="Назад")]]
    )
    if await create_order(context):
        await upload_to_exel()
        context.user_data["cart"] = None
        await update.message.reply_text(
            "Успешно! Ожидайте доставку.", reply_markup=reply_markup
        )
    return HANDLE_MENU


async def handle_mailing(context):
    await get_mailing()
    # if mailings:
    #     for mailing in mailings:
    #         start_time = mailing.start_date.strftime('%m-%d-%Y %H:%M')
    #         now_time = timezone.now().strftime('%m-%d-%Y %H:%M')
    #         if start_time == now_time:
    #             clients = await get_clients()
    #             for client in clients:
    #                 await context.bot.send_message(
    #                     text=mailing.text,
    #                     chat_id=client,
    #                     parse_mode=ParseMode.HTML
    #                 )
    #             await change_status_mailing(mailing)


async def cancel(update, context):
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data[START_OVER] = False
    return ConversationHandler.END


async def handle_tech_support(update, context):
    text = "<b>Что вас беспокоит </b>"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Назад", callback_data="Назад")]]
    )
    text_faq = await get_text_faq()

    await update.callback_query.answer()

    await update.callback_query.edit_message_text(
        textwrap.dedent(
            f"""
        {text}
        {text_faq}
        """
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return HANDLE_MENU


async def handle_error(update, context):
    logger.error(context.error)


def bot_starting():
    tg_token = settings.TELEGRAM_BOT_TOKEN
    application = Application.builder().token(tg_token).build()
    application.job_queue.run_repeating(handle_mailing, interval=60, first=10)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(handle_user_payment, pattern=r"Оплатить"),
                CallbackQueryHandler(remove_product, pattern=r"[0-9]"),
                CallbackQueryHandler(start, pattern="Назад"),
                CallbackQueryHandler(
                    add_delivery_address, pattern=r"delivery_address"
                ),
            ],
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_sub_categories, pattern=r"[0-9]"),
                CallbackQueryHandler(start, pattern=r"Главное меню"),
                CallbackQueryHandler(handle_cart, pattern=r"Корзина"),
                CallbackQueryHandler(
                    handle_tech_support, pattern=r"tech_support"
                ),
                CallbackQueryHandler(handle_categories),
            ],
            HANDLE_SUB_CATEGORIES: [
                CallbackQueryHandler(handle_sub_categories, pattern=r"[0-9]"),
                CallbackQueryHandler(start, pattern=r"Главное меню"),
                CallbackQueryHandler(handle_categories),
            ],
            HANDLE_PRODUCTS: [
                CallbackQueryHandler(handle_products, pattern=r"[0-9]"),
                CallbackQueryHandler(handle_categories, pattern=r"Назад"),
                CallbackQueryHandler(start, pattern=r"Главное меню"),
                CallbackQueryHandler(handle_sub_categories),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(handle_product_detail, pattern=r"[0-9]"),
                CallbackQueryHandler(handle_sub_categories, pattern=r"Назад"),
                CallbackQueryHandler(start, pattern=r"Главное меню"),
            ],
            HANDLE_CART: [
                MessageHandler(filters.TEXT, check_quantity),
                CallbackQueryHandler(handle_sub_categories, pattern=r"Назад"),
                CallbackQueryHandler(add_cart, pattern=r"Подтвердить"),
                CallbackQueryHandler(handle_cart, pattern=r"Корзина"),
                CallbackQueryHandler(add_cart),
            ],
            HANDLE_WAITING: [
                CallbackQueryHandler(
                    add_delivery_address, pattern=r"Ввести снова"
                ),
                CallbackQueryHandler(save_customer, pattern=r"Верно"),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, check_address_text
                ),
            ],
            HANDLE_USER_REPLY: [
                PreCheckoutQueryHandler(precheckout_callback),
                MessageHandler(
                    filters.SUCCESSFUL_PAYMENT, successful_payment_callback
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        per_chat=False,
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    application.run_polling()


class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **options):
        bot_starting()
