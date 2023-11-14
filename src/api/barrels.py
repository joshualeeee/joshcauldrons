from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver") 
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    gold_paid = 0
    ml = [0,0,0,0]

    for barrel in barrels_delivered:
        gold_paid += barrel.price * barrel.quantity
        if barrel.potion_type == [1,0,0,0]:
            ml[0] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,1,0,0]:
            ml[1] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,0,1,0]:
            ml[2] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,0,0,1]:
            ml[3] += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("Invalid Potion Type")
        
    with db.engine.begin() as connection:
        for i, amount in enumerate(ml):
            if amount == 0:
                continue
            connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO transactions_orders (barrel_id, ml_change, time)
                                    VALUES (:id, :change, NOW())
                                    """),
                    [{"id": i + 1,
                    "change": amount}])
            
        connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO transactions_orders (gold_change, time)
                                    VALUES (:change, NOW())
                                    """),
                    [{"change": gold_paid * -1}])
        
    return "OK"


options = [[1,0,0,0], [0,1,0,0], [0,0,1,0]]
current_index = 0

# Function to rotate to the next option
def rotate_options():
    global current_index
    current_index = (current_index + 1) % len(options)

# Gets called once a day 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("wholesale catalog:", wholesale_catalog)
    global current_index
    
    with db.engine.begin() as connection:
        query = connection.execute(sqlalchemy.text("""SELECT sum(gold_change) FROM transactions_orders""")).fetchone()
        
        gold = query[0]

        res = []
        bought = 0
        for barrel in wholesale_catalog:
            if [0,0,0,1] == barrel.potion_type and barrel.price <= gold:
                bought += 1
                gold -= barrel.price
                res.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
                break

        # while gold >= 50 and bought < 3:
        #     for barrel in wholesale_catalog:
        #         if options[current_index] == barrel.potion_type and barrel.price <= gold:
        #             if barrel.price * 5 <= gold and barrel.ml_per_barrel == 10000:
        #                 bought += 1
        #                 gold -= barrel.price * 5
        #                 res.append({
        #                     "sku": barrel.sku,
        #                     "quantity": 5,
        #                 })
        #                 rotate_options()
        #                 break
        #     if bought == 0:
        #         rotate_options()
        # if bought == 0:
        #         rotate_options()
    
    print(res)
    return res
