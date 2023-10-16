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

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING id")).fetchone()

    return {"cart_id": result[0]}


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


    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                                INSERT INTO cart_items (cart_id, quantity, potion_id) 
                                                SELECT :cart_id, :quantity, potions.id 
                                                FROM potions 
                                                WHERE potions.sku = :item_sku
                                                """),
                                            [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
    print(item_sku)
    return "OK"

class CartCheckout(BaseModel):
    payment: str

# increase gold, decrease potions
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(cart_checkout)

    with db.engine.begin() as connection:
        cart_orders = connection.execute(sqlalchemy.text("""
                                                UPDATE potions
                                                SET inventory = potions.inventory - cart_items.quantity
                                                FROM cart_items
                                                WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id
                                                RETURNING cart_items.quantity, cart_items.potion_id
                                            """), [{"cart_id": cart_id}]).fetchall()
        
        pots = 0
        new_gold = 0
        for order in cart_orders:
            connection.execute(sqlalchemy.text("""
                                                DELETE FROM cart_items
                                                WHERE cart_id = :cart_id 
                                                AND potion_id = :potion_id;
                                            """), [{"cart_id": cart_id, "potion_id": order[1]}])
        
            gold_paid = connection.execute(sqlalchemy.text("""
                                                UPDATE globals
                                                SET gold = gold + potions.cost * :quantity
                                                FROM potions
                                                WHERE potions.id = :potion_id
                                                RETURNING potions.cost
                                                """), 
                                                [{"potion_id": order[1], "quantity": order[0]}]).fetchone()
        
            pots += order[0]
            new_gold += gold_paid[0] * order[1]

    print("total_potions_bought", pots, "total_gold_paid", new_gold)
    return {"total_potions_bought": pots, "total_gold_paid": new_gold}
