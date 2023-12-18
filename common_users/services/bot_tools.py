import textwrap as tw
from datetime import datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator

from asgiref.sync import sync_to_async
from django.db.models import Count, F

from common_users.models import CommonUser, FAQ, CommonUserPurchase
from common_users.services.cart import Cart

from orders.models import Category, Product


@sync_to_async
def create_user(telegram_user_id, first_name, last_name, username):
    """create user"""
    user, created = CommonUser.objects.get_or_create(
        telegram_user_id=telegram_user_id,
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
        },
    )
    return user


@sync_to_async
def update_user_car(telegram_user_id, update_dict):
    """update user car"""
    CommonUser.objects.filter(
        telegram_user_id=telegram_user_id,
    ).update(**update_dict)
    user = CommonUser.objects.filter(
        telegram_user_id=telegram_user_id,
    ).first()

    return user


@sync_to_async
def get_categories(page_number):
    """returns category paginate objects"""

    categories = (
        Category.objects.filter(
            is_active=True,
        )
        .annotate(product_count=Count(F("products")))
        .filter(product_count__gt=0)
        .order_by("name")
    )

    paginator = Paginator(
        object_list=categories, per_page=settings.BASE_PAGINATE_BY
    )

    page_obj = paginator.get_page(page_number)

    categories_list = [x for x in page_obj]

    return_data = {
        "categories": categories_list,
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
    }

    return return_data


@sync_to_async
def get_category(category_id):
    """get category"""
    category = Category.objects.get(id=category_id)
    return category


@sync_to_async
def get_products(category_id):
    """returns products list"""
    products = Product.objects.select_related("category").filter(
        category=category_id, is_free=True
    )
    return [product for product in products]


def get_product_detail(product):
    """returns product detail"""
    return tw.dedent(f"<b>{product.name}</b>")


@sync_to_async
def get_product_name(product_id):
    """returns product name"""
    product = Product.objects.get(id=product_id)
    return tw.dedent(f"<b>{product.name}</b>")


@sync_to_async
def add_product_to_cart(context):
    """add product to card"""
    product_id = context.user_data["product_id"]
    quantity = int(context.user_data["quantity"])
    product = Product.objects.get(id=product_id)
    cart = Cart(context)
    cart.add(product=product, quantity=quantity)
    return tw.dedent(
        f"""
    Добавлено в корзину:
    <b>{quantity} час(а) {product.name}</b>"""
    )


@sync_to_async
def remove_product_from_cart(context):
    """remove product from cart"""
    product_id = context.user_data["product_id"]
    product = Product.objects.get(id=product_id)
    cart = Cart(context)
    cart.remove(product)


def get_cart_info(context):
    """returns cart info"""
    cart = Cart(context)
    return cart


@sync_to_async
def get_cart_products_info(context):
    """get cart products info"""

    cart = Cart(context)
    products = []
    products_info = ""

    for position, product in enumerate(cart, start=1):
        products.append(product["product"])
        raw_name = product["product"]
        name = raw_name.name
        quantity = product["quantity"]
        price = product["price"]
        product_total_price = product["total_price"]
        products_info += tw.dedent(
            f"""
        №{position}. 
        <i>Парковочное место:</i> <b>{name}</b>
        <i>Цена:</i> {price} тг.
        <i>Количество:</i> {quantity} час(а)
        <i>Стоимость:</i> {product_total_price} тг.
        """
        )
    products_info += tw.dedent(
        f"""
    <i>Общая стоимость:</i> {cart.get_total_price()} тг.
    """
    )
    return products_info, products


@sync_to_async
def get_product_info_for_payment(context):
    """get product info for payment"""
    products_in_cart = get_cart_info(context)
    total_order_price = products_in_cart.get_total_price()
    products_info = ""

    for product in products_in_cart:
        raw_name = product["product"]
        name = raw_name.name
        quantity = product["quantity"]
        products_info += tw.dedent(
            f"""
        {name}
        Количество: {quantity} час(а)
        """
        )
    products_info += tw.dedent(
        f"""
    Общая стоимость: {total_order_price} тг.
    """
    )
    return {
        "products_info": products_info,
        "total_order_price": total_order_price,
    }


@sync_to_async
def create_purchase(context):
    """create order"""
    cart = Cart(context)
    telegram_user_id = context.user_data["telegram_user_id"]
    user = CommonUser.objects.get(telegram_user_id=telegram_user_id)

    purchase_elements = []
    update_product = []

    for order_product in cart:
        product = order_product["product"]
        quantity = order_product["quantity"]
        purchase = CommonUserPurchase(
            user=user,
            product=product,
            quantity=quantity,
            amount=order_product["total_price"],
        )

        product.is_free = False
        product.lessor = user
        product.expiration_date = datetime.now() + timedelta(
            minutes=settings.START_MINUTE
        )

        update_product.append(product)
        purchase_elements.append(purchase)

    CommonUserPurchase.objects.bulk_create(purchase_elements)
    Product.objects.bulk_update(
        update_product, ["is_free", "lessor", "expiration_date"]
    )
    return True


@sync_to_async
def get_purchases(context):
    """returns purchases"""
    telegram_user_id = context.user_data["telegram_user_id"]
    purchases = CommonUserPurchase.objects.filter(
        user__telegram_user_id=telegram_user_id,
        is_completed=False,
    ).annotate(product_name=F("product__name"))

    return [purchase for purchase in purchases]


@sync_to_async
def get_user_products(context):
    """returns user products"""
    telegram_user_id = context.user_data["telegram_user_id"]
    products = Product.objects.filter(
        lessor__telegram_user_id=telegram_user_id,
    )

    return [product for product in products]


@sync_to_async
def complete_purchase(purchase_id):
    """complete purchase"""
    purchase = CommonUserPurchase.objects.get(id=purchase_id)

    product = purchase.product

    product.expiration_date = datetime.now() + timedelta(
        hours=purchase.quantity
    )
    product.expiration_date += timedelta(minutes=settings.END_MINUTE)
    product.is_took_place = True
    product.save()

    purchase.is_completed = True
    purchase.save()

    expiration_date = product.expiration_date - timedelta(
        minutes=settings.END_MINUTE
    )
    return expiration_date.strftime("%d %B %Y, %H:%M:%S")


@sync_to_async
def update_product_expiration_date():
    Product.objects.filter(
        is_free=False, lessor__isnull=False, expiration_date__lt=datetime.now()
    ).update(is_free=True, lessor=None, expiration_date=None)


@sync_to_async
def get_text_faq():
    all_faq = FAQ.objects.all()
    text_faq = ""

    for num, faq in enumerate(all_faq, start=1):
        question = faq.question
        answer = faq.answer
        text_faq += tw.dedent(
            f"""
        <b>№{num} {question}</b>
        <i>{answer}</i>
        """
        )
    return text_faq


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """build menu"""
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
