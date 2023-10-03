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

    query = "SELECT num_red_ml, gold FROM global_inventory"
    

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        ml = row[0]
        gold = row[1]
    
    for barrel in barrels_delivered:
        ml += barrel.ml_per_barrel * barrel.quantity
        gold -= barrel.price 
    
    query = "UPDATE global_inventory SET num_red_ml = {}, gold = {}".format(ml, gold)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    return "OK"

# Gets called once a day 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    query = "SELECT num_red_potions, gold FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
    
    row = result.fetchone()
    if row is not None:
        num_red_potions = row[0]
        gold = row[1]
    
    quantity = 0

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            if num_red_potions < 10 and gold >= barrel.price:
                quantity = barrel.quantity
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(query))

    if quantity > 0:
        return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": quantity,
        }
        ]
    else:
        return []
