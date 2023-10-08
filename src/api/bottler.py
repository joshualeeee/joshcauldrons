from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

# increase red pots decrease red ml
@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    
    query = "SELECT num_red_potions, num_red_ml, num_blue_potions, num_blue_ml, num_green_potions, num_green_ml FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        red_pots = row[0]
        red_ml = row[1]
        blue_pots = row[2]
        blue_ml = row[3]
        green_pots = row[4]
        green_ml = row[5]
        
    
    for deliveries in potions_delivered:
        if deliveries.potion_type == [100, 0, 0, 0] or deliveries.potion_type == [1, 0, 0, 0]:
            red_pots += deliveries.quantity
            red_ml -= deliveries.quantity * 100
        if deliveries.potion_type == [0, 0, 100, 0] or deliveries.potion_type == [0, 0, 1, 0]:
            blue_pots += deliveries.quantity
            blue_ml -= deliveries.quantity * 100
        if deliveries.potion_type == [0, 0, 100, 0] or deliveries.potion_type == [0, 0, 1, 0]:
            green_pots += deliveries.quantity
            green_ml -= deliveries.quantity * 100

    query = "UPDATE global_inventory SET num_red_potions = {}, num_red_ml = {}, num_blue_potions = {}, num_blue_ml = {}, num_green_potions = {}, num_green_ml = {}".format(red_pots, red_ml, blue_pots, blue_ml, green_pots, green_ml)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    query = "SELECT num_red_ml, num_blue_ml, num_green_ml FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        red_ml = row[0]
        blue_ml = row[1]
        green_ml = row[2]

    quantity = 0
    res = []
    while red_ml >= 100:
        red_ml -= 100
        quantity += 1
    if quantity > 0:
        res.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": quantity,
        })
    
    quantity = 0
    while blue_ml >= 100:
        blue_ml -= 100
        quantity += 1
    if quantity > 0:
        res.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": quantity,
        })
    
    quantity = 0
    while green_ml >= 100:
        green_ml -= 100
        quantity += 1
    if quantity > 0:
        res.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": quantity,
        })

    return res
