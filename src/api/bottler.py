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
    
    query = "SELECT num_red_potions, num_red_ml FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        pots = row[0]
        ml = row[1]

    pots += potions_delivered[0].quantity
    ml -= potions_delivered[0].quantity * 100

    query = "UPDATE global_inventory SET num_red_potions = {}, num_red_ml = {}".format(pots, ml)

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

    # Initial logic: bottle all barrels into red potions.

    query = "SELECT num_red_ml FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))

    row = result.fetchone()
    if row is not None:
        ml = row[0]

    quantity = 0
    while ml >= 100:
        ml -= 100
        quantity += 1
    if quantity == 0:
        return []
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity,
            }
        ]
