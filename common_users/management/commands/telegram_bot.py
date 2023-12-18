import logging
import textwrap
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
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
    create_user,
    create_purchase,
    get_cart_products_info,
    get_categories,
    update_product_expiration_date,
    get_product_detail,
    get_product_info_for_payment,
    get_product_name,
    get_products,
    get_text_faq,
    remove_product_from_cart,
    update_user_car,
    get_purchases,
    complete_purchase,
    get_user_products,
)

(
    HANDLE_CATEGORIES,
    HANDLE_CART,
    HANDLE_DESCRIPTION,
    HANDLE_MENU,
    HANDLE_PRODUCTS,
    HANDLE_USER_REPLY,
    HANDLE_WAITING,
    START_OVER,
    HANDLE_REGISTER,
    HANDLE_REGISTER_CAR_NUMBER,
    HANDLE_REGISTER_CAR_SERIAL_NUMBER,
    HANDLE_REGISTER_CAR_REGION,
    HANDLE_PHONE,
    HANDLE_TOOK_PLACE,
    HANDLE_PURCHASES,
) = range(15)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BACK_BUTTON = InlineKeyboardButton(text="Назад", callback_data="back")

MAIN_MENU_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="📋 Свободные места", callback_data="catalog"
            )
        ],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")],
        [InlineKeyboardButton(text="🅿️ Мои брони", callback_data="purchases")],
        [InlineKeyboardButton(text="🗣 FAQ", callback_data="faq")],
        [
            InlineKeyboardButton(
                text="🛠 Тех. поддержка", callback_data="tech_support"
            )
        ],
    ]
)


def check_car_info_and_phone(user):
    """check car info and phone"""
    return_text = None
    is_phone = False
    handle = None

    if user.car_number is None:
        return_text = "<b>Заполните номер машины</b>"
        handle = HANDLE_REGISTER_CAR_NUMBER

    elif user.car_serial_number is None:
        return_text = "<b>Буквы на номере автомобиля</b>"
        handle = HANDLE_REGISTER_CAR_SERIAL_NUMBER

    elif user.car_number_region is None:
        return_text = "<b>Заполните регион машины</b>"
        handle = HANDLE_REGISTER_CAR_REGION

    elif user.phone is None:
        return_text = "<b>Отправьте номер телефона</b>"
        handle = HANDLE_PHONE
        is_phone = True

    return handle, return_text, is_phone


async def get_chat_member(update, context):
    """get chat member"""

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

    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text, reply_markup=MAIN_MENU_BUTTONS
        )

    # elif await get_chat_member(update, context):
    #     return
    else:
        telegram_user_id = update.effective_user.id
        username = update.effective_user.username
        context.user_data["telegram_user_id"] = telegram_user_id
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        user = await create_user(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        check_user_data, check_text, is_phone = check_car_info_and_phone(
            user=user
        )

        if check_user_data:
            if is_phone:
                button_phone = KeyboardButton(
                    text="Отправить номер телефона 📱️", request_contact=True
                )
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[button_phone]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    reply_markup=keyboard,
                )

            else:
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    parse_mode=ParseMode.HTML,
                )
            return check_user_data

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
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_BUTTONS,
        )
    context.user_data[START_OVER] = True

    return HANDLE_CATEGORIES


async def show_main_page(update, context):
    """show main page"""
    context.user_data["current_page"] = 1

    menu = await get_menu(context.user_data["current_page"])

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите парковочное место:", reply_markup=menu
    )


async def show_next_page(update, context):
    """show next page"""
    context.user_data["current_page"] += 1
    menu = await get_menu(context.user_data["current_page"])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите парковочное место:", reply_markup=menu
    )


async def show_previous_page(update, context):
    """show previous page"""
    context.user_data["current_page"] -= 1
    menu = await get_menu(context.user_data["current_page"])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите парковочное место:", reply_markup=menu
    )


async def get_menu(current_page):
    """get menu"""

    categories_data = await get_categories(page_number=current_page)

    keyboard = [
        InlineKeyboardButton(
            text=category.name, callback_data=str(category.id)
        )
        for category in categories_data.get("categories")
    ]

    footer_buttons = []

    if categories_data.get("has_previous"):
        footer_buttons.insert(
            0, InlineKeyboardButton(text="<<<", callback_data="prev")
        )

    if categories_data.get("has_next"):
        footer_buttons.append(
            InlineKeyboardButton(text=">>>", callback_data="next")
        )

    footer_buttons.append(
        InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    )

    return InlineKeyboardMarkup(
        build_menu(keyboard, n_cols=2, footer_buttons=footer_buttons)
    )


async def handle_categories(update, context):
    """handle categories"""

    if update.callback_query.data in ("catalog", "back"):
        await show_main_page(update, context)

    elif update.callback_query.data == "next":
        await show_next_page(update, context)

    elif update.callback_query.data == "prev":
        await show_previous_page(update, context)

    return HANDLE_PRODUCTS


async def handle_products(update, context):
    """handle products"""

    product_category = update.callback_query.data
    products_category = await get_products(product_category)

    products_num = len(products_category)

    for product in products_category:
        put_cart_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Выбрать", callback_data=str(product.id)
                    )
                ]
            ]
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_product_detail(product),
            reply_markup=put_cart_button,
            parse_mode=ParseMode.HTML,
        )

    keyboard = [
        [
            BACK_BUTTON,
            InlineKeyboardButton(
                text="Главное меню", callback_data="main_menu"
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        text=f"Показано парковочных мест: {products_num}",
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


async def handle_product_detail(update, context):
    """handle product detail"""

    product_id = update.callback_query.data
    context.user_data["product_id"] = product_id

    product_details = await get_product_name(product_id)
    context.user_data["product_details"] = product_details
    text = f"""Парковочное место: {product_details}\nВыберите количество времени или введите свое количество:"""

    keyboard = []

    for i in range(1, 4):
        keyboard.append(
            InlineKeyboardButton(text=f"{i} час(а)", callback_data=i)
        )

    keyboard.append(BACK_BUTTON)
    keyboard_groups = build_menu(keyboard, n_cols=1)

    await context.bot.send_message(
        text=text,
        chat_id=update.effective_chat.id,
        reply_markup=InlineKeyboardMarkup(keyboard_groups),
        parse_mode=ParseMode.HTML,
    )

    return HANDLE_CART


async def check_quantity(update, context):
    """check quantity"""

    if update.message:
        quantity = update.message.text
    else:
        quantity = update.callback_query.data

    if re.match(r"[0-9]", quantity):
        if int(quantity) == 0:
            await context.bot.send_message(
                text=textwrap.dedent(
                    """
                <b>Количество должно быть больше 0</b>
                """
                ),
                chat_id=update.effective_chat.id,
                parse_mode=ParseMode.HTML,
            )
            return HANDLE_CART

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    BACK_BUTTON,
                    InlineKeyboardButton(
                        text="Подтвердить", callback_data="confirm"
                    ),
                ]
            ]
        )
        product_details = context.user_data["product_details"]
        context.user_data["quantity"] = quantity

        await context.bot.send_message(
            text=textwrap.dedent(
                f"""
            Вы выбрали {product_details}  {quantity} час(а).
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


async def update_car_number(update, context):
    """update car number"""

    car_number = update.message.text

    if re.match(r"[0-9]", car_number):
        if len(car_number) == 3:
            user = await update_user_car(
                telegram_user_id=update.effective_user.id,
                update_dict={"car_number": car_number},
            )

            check_user_data, check_text, is_phone = check_car_info_and_phone(
                user=user
            )

            if check_user_data:
                if is_phone:
                    button_phone = KeyboardButton(
                        text="Отправить номер телефона 📱️",
                        request_contact=True,
                    )
                    keyboard = ReplyKeyboardMarkup(
                        keyboard=[[button_phone]],
                        resize_keyboard=True,
                        one_time_keyboard=True,
                    )
                    await update.message.reply_text(
                        text=textwrap.dedent(check_text),
                        reply_markup=keyboard,
                    )

                else:
                    await update.message.reply_text(
                        text=textwrap.dedent(check_text),
                        parse_mode=ParseMode.HTML,
                    )
                return check_user_data

            await update.message.reply_text(
                textwrap.dedent(
                    f"""
                    <b>Здравствуйте {update.effective_user.first_name}!</b>
                     Добро пожаловать "iPark"
                    """
                ),
                parse_mode=ParseMode.HTML,
            )

            await update.message.reply_text(
                text="Выберете действие:",
                parse_mode=ParseMode.HTML,
                reply_markup=MAIN_MENU_BUTTONS,
            )
            return HANDLE_CATEGORIES

        else:
            await context.bot.send_message(
                text=textwrap.dedent(
                    """<b>Значение должно быть равна 3 цифрам</b>"""
                ),
                chat_id=update.effective_chat.id,
                parse_mode=ParseMode.HTML,
            )
            return HANDLE_REGISTER_CAR_NUMBER
    else:
        await context.bot.send_message(
            text=textwrap.dedent("""<b>Значение должно быть числом</b>"""),
            chat_id=update.effective_chat.id,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_REGISTER_CAR_NUMBER


async def update_car_serial_number(update, context):
    """update car serial number"""

    car_serial_number = update.message.text

    if len(car_serial_number) > 3:
        await context.bot.send_message(
            text=textwrap.dedent(
                """<b>Значение не должно быть больше 3</b>"""
            ),
            chat_id=update.effective_chat.id,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_REGISTER_CAR_SERIAL_NUMBER

    else:
        user = await update_user_car(
            telegram_user_id=update.effective_user.id,
            update_dict={"car_serial_number": car_serial_number},
        )

        check_user_data, check_text, is_phone = check_car_info_and_phone(
            user=user
        )

        if check_user_data:
            if is_phone:
                button_phone = KeyboardButton(
                    text="Отправить номер телефона 📱️", request_contact=True
                )
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[button_phone]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    reply_markup=keyboard,
                )

            else:
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    parse_mode=ParseMode.HTML,
                )
            return check_user_data

        await update.message.reply_text(
            textwrap.dedent(
                f"""
                <b>Здравствуйте {update.effective_user.first_name}!</b>
                 Добро пожаловать "iPark"
                """
            ),
            parse_mode=ParseMode.HTML,
        )

        await update.message.reply_text(
            text="Выберете действие:",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_BUTTONS,
        )
        return HANDLE_CATEGORIES


async def update_car_number_region(update, context):
    """update car number region"""

    car_region = update.message.text

    if re.match(r"[0-9]", car_region):
        if int(car_region) == 0 or len(car_region) > 2:
            await context.bot.send_message(
                text=textwrap.dedent("b>Введенный регион не существует</b>"),
                chat_id=update.effective_chat.id,
                parse_mode=ParseMode.HTML,
            )
            return HANDLE_REGISTER_CAR_REGION

        user = await update_user_car(
            telegram_user_id=update.effective_user.id,
            update_dict={"car_number_region": int(car_region)},
        )

        check_user_data, check_text, is_phone = check_car_info_and_phone(
            user=user
        )

        if check_user_data:
            if is_phone:
                button_phone = KeyboardButton(
                    text="Отправить номер телефона 📱️", request_contact=True
                )
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[button_phone]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    reply_markup=keyboard,
                )

            else:
                await update.message.reply_text(
                    text=textwrap.dedent(check_text),
                    parse_mode=ParseMode.HTML,
                )
            return check_user_data

        await update.message.reply_text(
            textwrap.dedent(
                f"""
                <b>Здравствуйте {update.effective_user.first_name}!</b>
                 Добро пожаловать "iPark"
                """
            ),
            parse_mode=ParseMode.HTML,
        )

        await update.message.reply_text(
            text="Выберете действие:",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_BUTTONS,
        )
        return HANDLE_CATEGORIES

    else:
        await context.bot.send_message(
            text=textwrap.dedent("<b>Значение должно быть числом</b>"),
            chat_id=update.effective_chat.id,
            parse_mode=ParseMode.HTML,
        )

        return HANDLE_REGISTER_CAR_REGION


async def update_user_phone(update, context):
    phone = update.message.contact.phone_number

    user = await update_user_car(
        telegram_user_id=update.effective_user.id,
        update_dict={"phone": phone},
    )

    check_user_data, check_text, is_phone = check_car_info_and_phone(user=user)

    if check_user_data:
        await update.message.reply_text(
            textwrap.dedent(check_text),
            parse_mode=ParseMode.HTML,
        )
        return check_user_data

    await update.message.reply_text(
        textwrap.dedent(
            f"""
            <b>Здравствуйте {update.effective_user.first_name}!</b>
             Добро пожаловать "iPark"
            """
        ),
        parse_mode=ParseMode.HTML,
    )

    await update.message.reply_text(
        text="Выберете действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_BUTTONS,
    )
    return HANDLE_CATEGORIES


async def add_cart(update, context):
    """add cart"""
    if update.callback_query.data == "cart":
        await show_main_page(update, context)
        return HANDLE_CATEGORIES

    elif update.callback_query.data == "back":
        await show_main_page(update, context)
        return HANDLE_PRODUCTS

    else:
        await add_product_to_cart(context)
        products_info, products = await get_cart_products_info(context)
        keyboard = []

        back = [BACK_BUTTON]

        for position, product in enumerate(products, start=1):
            keyboard.append(
                InlineKeyboardButton(
                    text=f"Удалить позицию №{position}",
                    callback_data=str(product.id),
                )
            )
        keyboard_groups = build_menu(keyboard, n_cols=2)
        keyboard_groups.append(
            [InlineKeyboardButton(text="Оплатить", callback_data="payment")]
        )
        keyboard_groups.append(back)

        reply_markup = InlineKeyboardMarkup(keyboard_groups)

        await update.callback_query.edit_message_text(
            text=products_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_MENU


async def show_cart_info(update, context):
    """show cart info"""
    products = await get_purchases(context)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=products)


async def show_purchases_info(update, context):
    """show purchases info"""
    products = await get_user_products(context)

    if len(products) == 0:
        await update.callback_query.answer("Брони отсутствуют")
        return

    product_info = ""

    for position, product in enumerate(products, start=1):
        product_info += textwrap.dedent(
            f"""
                №{position}. 
                <i>Парковочное место:</i> <b>{product.name}</b>
                <i>Время выезда:</i> {product.str_expiration_date}
                """
        )

    reply_markup = InlineKeyboardMarkup([[BACK_BUTTON]])

    await update.callback_query.edit_message_text(
        text=product_info,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return HANDLE_MENU


async def handle_cart(update, context):
    """handle cart"""
    if "cart" not in context.user_data:
        await update.callback_query.answer("Пустая корзина")
        return
    else:
        products_info, products = await get_cart_products_info(context)
        keyboard = []
        for position, product in enumerate(products, start=1):
            keyboard.append(
                InlineKeyboardButton(
                    text=f"Удалить позицию №{position}",
                    callback_data=str(product.id),
                )
            )
        keyboard_groups = build_menu(keyboard, n_cols=2)
        keyboard_groups.append(
            [InlineKeyboardButton(text="Оплатить", callback_data="payment")]
        )
        keyboard_groups.append([BACK_BUTTON])
        reply_markup = InlineKeyboardMarkup(keyboard_groups)
        await update.callback_query.edit_message_text(
            text=products_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
        return HANDLE_MENU


async def remove_product(update, context):
    """remove product"""
    product_id = update.callback_query.data
    context.user_data["product_id"] = product_id
    await remove_product_from_cart(context)
    await update.callback_query.answer("Товар удален из корзины")
    await handle_cart(update, context)
    return HANDLE_MENU


async def handle_user_payment(update, context):
    """handle user payment"""
    order_info = await get_product_info_for_payment(context)

    chat_id = update.effective_user.id
    price = order_info["total_order_price"]
    prices = [LabeledPrice("Оплата товаров", int(price) * 100)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title='Оплата услуг "iPark"',
        description=order_info["products_info"],
        payload="telegram-store",
        provider_token=settings.PAYMENT_TOKEN,
        currency="KZT",
        prices=prices,
    )
    return HANDLE_USER_REPLY


async def pre_checkout_callback(update, context):
    """pre checkout callback"""
    query = update.pre_checkout_query
    if query.invoice_payload != "telegram-store":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)
    return HANDLE_USER_REPLY


async def successful_payment_callback(update, context):
    """successful payment callback"""

    if await create_purchase(context):
        context.user_data["cart"] = None

        text = f"""
        <b>Бронь успешно поставлена</b>
        При занятии парковочного места необходимо нажать кнопку «занял место».
        Бронь держится {settings.START_MINUTE} минут, в случае если не 
        успеете уложиться в данное время, бронь снимается."""

        await update.message.reply_text(
            text=textwrap.dedent(text), parse_mode=ParseMode.HTML
        )

        purchases = await get_purchases(context)

        for purchase in purchases:
            purchase_button = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Занял место", callback_data=str(purchase.id)
                        )
                    ]
                ]
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=textwrap.dedent(f"<b>{purchase.product_name}</b>"),
                reply_markup=purchase_button,
                parse_mode=ParseMode.HTML,
            )

    return HANDLE_TOOK_PLACE


async def took_place(update, context):
    purchase_id = update.callback_query.data
    expiration_date = await complete_purchase(purchase_id)

    text = f"<b>Место занято ✅ </b>\nВремя выезда {expiration_date}"

    reply_markup = InlineKeyboardMarkup(
        [
            [
                BACK_BUTTON,
            ]
        ]
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=textwrap.dedent(text),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return HANDLE_MENU


async def handle_check_product_expiration_date(context):
    await update_product_expiration_date()
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


async def handle_faq(update, context):
    """handle faq"""
    text = "<b>Часто задаваемые вопросы:</b>"
    reply_markup = InlineKeyboardMarkup([[BACK_BUTTON]])

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
    """bot stat command"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    application = Application.builder().token(bot_token).build()

    if application.job_queue:
        application.job_queue.run_repeating(
            handle_check_product_expiration_date, interval=60, first=10
        )

    uuid_pattern = settings.BASE_PATTERN

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(handle_user_payment, pattern=r"payment"),
                # CallbackQueryHandler(remove_product, pattern=uuid_pattern),
                CallbackQueryHandler(start, pattern="back"),
            ],
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_categories, pattern=uuid_pattern),
                CallbackQueryHandler(start, pattern=r"main_menu"),
                CallbackQueryHandler(handle_cart, pattern=r"cart"),
                CallbackQueryHandler(handle_faq, pattern=r"faq"),
                CallbackQueryHandler(
                    show_purchases_info, pattern=r"purchases"
                ),
                CallbackQueryHandler(handle_categories),
            ],
            HANDLE_PRODUCTS: [
                CallbackQueryHandler(handle_products, pattern=uuid_pattern),
                CallbackQueryHandler(handle_categories, pattern=r"back"),
                CallbackQueryHandler(start, pattern=r"main_menu"),
                CallbackQueryHandler(handle_categories),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(
                    handle_product_detail, pattern=uuid_pattern
                ),
                CallbackQueryHandler(handle_categories, pattern=r"back"),
                CallbackQueryHandler(start, pattern=r"main_menu"),
            ],
            HANDLE_CART: [
                CallbackQueryHandler(check_quantity, pattern=r"[1-3]"),
                MessageHandler(filters.TEXT, check_quantity),
                CallbackQueryHandler(handle_categories, pattern=r"back"),
                CallbackQueryHandler(add_cart, pattern=r"confirm"),
                CallbackQueryHandler(handle_cart, pattern=r"cart"),
                CallbackQueryHandler(add_cart),
            ],
            HANDLE_USER_REPLY: [
                PreCheckoutQueryHandler(pre_checkout_callback),
                MessageHandler(
                    filters.SUCCESSFUL_PAYMENT, successful_payment_callback
                ),
            ],
            HANDLE_REGISTER_CAR_NUMBER: [
                MessageHandler(filters.TEXT, update_car_number),
            ],
            HANDLE_REGISTER_CAR_SERIAL_NUMBER: [
                MessageHandler(filters.TEXT, update_car_serial_number),
            ],
            HANDLE_REGISTER_CAR_REGION: [
                MessageHandler(filters.TEXT, update_car_number_region),
            ],
            HANDLE_PHONE: [
                MessageHandler(filters.CONTACT, update_user_phone),
            ],
            HANDLE_TOOK_PLACE: [
                CallbackQueryHandler(took_place, pattern=uuid_pattern),
            ],
            HANDLE_PURCHASES: [
                CallbackQueryHandler(
                    show_purchases_info, pattern=r"purchases"
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
    """Command"""

    help = "Telegram bot"

    def handle(self, *args, **options):
        bot_starting()
