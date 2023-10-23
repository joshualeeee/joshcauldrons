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
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:name) RETURNING id"),
                                    [{"name": new_cart.customer}]).fetchone()

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
                                                INSERT INTO public.transactions_orders (cart_id, potion_id, potion_change, gold_change, time)
                                                SELECT ci.cart_id, ci.potion_id, ci.quantity * -1, ci.quantity * p.cost, NOW()
                                                FROM public.cart_items AS ci
                                                JOIN public.potions AS p ON ci.potion_id = p.id
                                                WHERE ci.cart_id = :cart_id
                                                RETURNING potion_change * -1 as potion_change, gold_change
                                            """), [{"cart_id": cart_id}]).fetchall()
        
        connection.execute(sqlalchemy.text("""
                                                DELETE FROM cart_items
                                                WHERE cart_id = :cart_id
                                            """), [{"cart_id": cart_id}])
        pots = 0
        gold_change = 0
        for order in cart_orders:
            pots += order[0]
            gold_change += order[1]
            
    print("total_potions_bought", pots, "total_gold_paid", gold_change)
    return {"total_potions_bought": pots, "total_gold_paid": gold_change}
