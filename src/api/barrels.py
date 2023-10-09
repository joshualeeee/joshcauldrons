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

    query = "SELECT num_red_ml, num_blue_ml, num_green_ml, gold FROM global_inventory"
    

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        red_ml = row[0]
        blue_ml = row[1]
        green_ml = row[2]
        gold = row[3]
    
    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_RED_BARREL":
            red_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
        if barrel.sku == "SMALL_BLUE_BARREL":
            blue_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
        if barrel.sku == "SMALL_GREEN_BARREL":
            green_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
    
    query = "UPDATE global_inventory SET num_red_ml = {}, num_blue_ml = {}, num_green_ml = {}, gold = {}".format(red_ml,blue_ml,green_ml,gold)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    return "OK"

# Gets called once a day 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    query = "SELECT num_red_potions, num_blue_potions, num_green_potions, gold FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
    
    row = result.fetchone()
    pots = []
    if row is not None:
        pots.append(("SMALL_RED_BARREL", row[0]))
        pots.append(("SMALL_BLUE_BARREL", row[1]))
        pots.append(("SMALL_GREEN_BARREL", row[2]))
        gold = row[3]
     
    # sorts in asc by second value 

    min_tuple = min(pots, key=lambda x: x[1])
    
    res = []


    for barrel in wholesale_catalog:
        if barrel.sku == min_tuple[0] and gold >= barrel.price:
            gold -= barrel.price
            res.append({
                "sku": min_tuple[0],
                "quantity": 1,
            })

    # pots.sort(key = lambda x: x[1]) 
    # for p in pots:
    #     if p[1] < 10:
    #         for barrel in wholesale_catalog:
    #             if barrel.sku == p[0] and gold >= barrel.price:
    #                 gold -= barrel.price
    #                 res.append({
    #                     "sku": p[0],
    #                     "quantity": 1,
    #                 })
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(query))

    print(res)
    return res
