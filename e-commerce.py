from datetime import date, datetime
from typing import List


class CartEmptyError(Exception): pass
class InvalidQuantityError(Exception): pass
class InsufficientBalanceError(Exception): pass
class ExpiredProductError(Exception): pass
class OutOfStockError(Exception): pass


class Product:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.stock = quantity

    def is_available(self, requested_qty: int) -> bool:
        return self.stock >= requested_qty

    def deduct_stock(self, qty: int):
        if not self.is_available(qty):
            raise OutOfStockError(f"{self.name} is out of stock")
        self.stock -= qty


class ExpiringProduct(Product):
    def __init__(self, name: str, price: float, quantity: int, expiry_date: date):
        super().__init__(name, price, quantity)
        self.expiry_date = expiry_date

    def is_expired(self) -> bool:
        return datetime.now().date() > self.expiry_date

    def check_expiration(self):
        if self.is_expired():
            raise ExpiredProductError(f"{self.name} has expired")


class ShippableProduct(Product):
    def __init__(self, name: str, price: float, quantity: int, weight: float):
        super().__init__(name, price, quantity)
        self.weight = weight


class ExpiringShippableProduct(ExpiringProduct, ShippableProduct):
    def __init__(self, name: str, price: float, quantity: int, expiry_date: date, weight: float):
        Product.__init__(self, name, price, quantity)
        self.expiry_date = expiry_date
        self.weight = weight


class CartItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.total_price = product.price * quantity


class Customer:
    def __init__(self, name: str, balance: float):
        self.name = name
        self.balance = balance

    def charge(self, amount: float):
        if self.balance < amount:
            raise InsufficientBalanceError(f"Need {amount}, have {self.balance}")
        self.balance -= amount


class Cart:
    def __init__(self):
        self.items: List[CartItem] = []

    def add(self, product: Product, quantity: int):
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")

        if isinstance(product, ExpiringProduct):
            product.check_expiration()

        if not product.is_available(quantity):
            raise OutOfStockError(f"Only {product.stock} of {product.name} available")

        self.items.append(CartItem(product, quantity))

    def is_empty(self) -> bool:
        return not self.items

    def total(self) -> float:
        return sum(item.total_price for item in self.items)

    def get_shippables(self) -> List[ShippableProduct]:
        return [
            item.product
            for item in self.items
            if isinstance(item.product, ShippableProduct)
            for _ in range(item.quantity)
        ]


class ShippingService:
    FLAT_FEE = 10
    RATE_PER_KG = 20

    @staticmethod
    def calculate(items: List[ShippableProduct]) -> float:
        total_weight = sum(item.weight for item in items)
        return 0 if not items else ShippingService.FLAT_FEE + total_weight * ShippingService.RATE_PER_KG


def checkout(customer: Customer, cart: Cart):
    if cart.is_empty():
        raise CartEmptyError("Cart is empty")

    for item in cart.items:
        if isinstance(item.product, ExpiringProduct):
            item.product.check_expiration()
        if not item.product.is_available(item.quantity):
            raise OutOfStockError(f"{item.product.name} is out of stock")

    shipping_items = cart.get_shippables()
    shipping_cost = ShippingService.calculate(shipping_items)
    subtotal = cart.total()
    total = subtotal + shipping_cost

    customer.charge(total)

    for item in cart.items:
        item.product.deduct_stock(item.quantity)

    print(" Checkout Successful")
    print(f"Subtotal: {subtotal:.2f}, Shipping: {shipping_cost:.2f}, Total: {total:.2f}")
    print(f"Remaining balance: {customer.balance:.2f}")