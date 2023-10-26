from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    start = 0 if search_page == "" else int(search_page)

    if sort_col is search_sort_options.customer_name:
        order_by = db.carts.c.customer_name
    elif sort_col is search_sort_options.item_sku:
        order_by = db.potions.c.sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = db.transactions_orders.c.potion_change
    elif sort_col is search_sort_options.timestamp:
        order_by = db.transactions_orders.c.time
    else:
        assert False
    

    if sort_order == search_sort_order.desc:
        if sort_col is search_sort_options.line_item_total:
            order_by = sqlalchemy.asc(order_by)
        else:
            order_by = sqlalchemy.desc(order_by)
    else:
        if sort_col is search_sort_options.line_item_total:
            order_by = sqlalchemy.desc(order_by)
        else:
            order_by = sqlalchemy.asc(order_by)

    joined_tables = sqlalchemy.join(
        db.transactions_orders,
        db.potions,
        db.transactions_orders.c.potion_id == db.potions.c.id
    ).join(
        db.carts,
        db.transactions_orders.c.cart_id == db.carts.c.id
    )

    stmt = (
        sqlalchemy.select(
            db.transactions_orders.c.id,
            db.potions.c.sku,
            db.carts.c.customer_name,
            db.transactions_orders.c.potion_change,
            db.transactions_orders.c.time,
        )
        .select_from(joined_tables)
        .limit(6)
        .offset(start)
        .order_by(order_by)
    )

    if customer_name != "":
        stmt = stmt.where(db.carts.c.customer_name.ilike(f"%{customer_name}%"))
    
    if potion_sku != "":
        stmt = stmt.where(db.potions.c.sku.ilike(f"%{potion_sku}%"))

    prevP = "" if start == 0 else str(start - 5)
    nextP = ""
    
    with db.engine.connect() as conn:
        result = conn.execute(stmt).fetchall()
        if len(result) >= 6:
            if prevP == "":
                nextP = "5"
            else:
                nextP = str(int(prevP) + 10)
        res = []
        i = 0
        for row in result:
            if i < 5:
                i += 1
                res.append(
                    {
                        "line_item_id": row.id,
                        "item_sku": row.sku,
                        "customer_name": row.customer_name,
                        "line_item_total": row.potion_change * -1,
                        "timestamp": row.time,
                    }
                )

    return  {
                "previous": prevP,
                "next": nextP,
                "results": res
            }

    # return {
    #     "previous": "",
    #     "next": "",
    #     "results": [
    #         {
    #             "line_item_id": 1,
    #             "item_sku": "1 oblivion potion",
    #             "customer_name": "Scaramouche",
    #             "line_item_total": 50,
    #             "timestamp": "2021-01-01T00:00:00Z",
    #         }
    #     ],
    # }


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
