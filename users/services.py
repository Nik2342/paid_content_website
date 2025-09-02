import stripe
from config.settings import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY


def create_stripe_price(amount):

    price = stripe.Price.create(
        currency="rub",
        unit_amount=amount * 100,
        product_data={"name": "Payment"},
    )
    return price


def create_stripe_sessions(price):

    session = stripe.checkout.Session.create(
        success_url="http://127.0.0.1:8000/",
        line_items=[{"price": price.get("id"), "quantity": 1}],
        mode="payment",
    )
    return session.get("id"), session.get("url")
