import stripe
from config.settings import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY


def create_stripe_product(name: str, description: str = None) -> stripe.Product:
    """Создает продукт в Stripe"""
    product_data = {"name": name}
    if description:
        product_data["description"] = description

    product = stripe.Product.create(**product_data)
    return product


def create_stripe_price(
    product_id: str, amount: int, currency: str = "rub"
) -> stripe.Price:
    """Создает цену для продукта в Stripe"""
    price = stripe.Price.create(
        currency=currency.lower(),
        unit_amount=amount * 100,  # Конвертируем в копейки
        product=product_id,
    )
    return price


def create_stripe_checkout_session(
    price_id: str, success_url: str, cancel_url: str
) -> stripe.checkout.Session:
    """Создает сессию оплаты"""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def create_payment_session(amount: int, product_name: str = "Подписка") -> tuple:
    """Полный процесс создания платежа - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        # Создаем продукт
        product = create_stripe_product(product_name, "Доступ к премиум контенту")

        # Создаем цену
        price = create_stripe_price(product.id, amount)

        # Создаем сессию
        success_url = "http://127.0.0.1:8000/users/payment/success/"
        cancel_url = "http://127.0.0.1:8000/users/payment/cancel/"

        session = create_stripe_checkout_session(price.id, success_url, cancel_url)

        # ВОЗВРАЩАЕМ ТОЛЬКО session_id И url
        return session.id, session.url

    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error creating payment session: {str(e)}")
