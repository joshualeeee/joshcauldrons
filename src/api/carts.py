from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


cart_tracker = {}
count = [0]
count[0] = 0

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    count[0] += 1
    cart_tracker[count[0]] = []

    return {"cart_id": count[0]}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    # cart = cart_tracker[cart_id]
    
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    cart = cart_tracker[cart_id]


    for order in cart:
        if order[0] == item_sku:
            order[1] = cart_item.quantity
            return "OK"

    cart.append([item_sku, cart_item.quantity])
    cart_tracker[cart_id] = cart

    return "OK"

class CartCheckout(BaseModel):
    payment: str

# increase gold, decrease potions
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(cart_checkout)

    query = "SELECT num_red_potions, gold FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
    
    row = result.fetchone()
    if row is not None:
        pots = row[0]
        gold = row[1]

    cart = cart_tracker[cart_id]

    new_gold = 0
    pots_sold = 0
    for order in cart:
        while order[1] > 0 and pots > 0:
            new_gold += 50
            pots_sold += 1
            pots -= 1
            order[1] -= 1

    gold += new_gold

    query = "UPDATE global_inventory SET num_red_potions = {}, gold = {}".format(pots, gold)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(query))

    return {"total_potions_bought": pots_sold, "total_gold_paid": new_gold}
