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
    with db.engine.begin() as connection:
        print(potions_delivered)    

        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        for potion in potions_delivered:
            red_ml += potion.quantity * potion.potion_type[0]
            green_ml += potion.quantity * potion.potion_type[1]
            blue_ml += potion.quantity * potion.potion_type[2]
            dark_ml += potion.quantity * potion.potion_type[3]

            connection.execute(
                sqlalchemy.text("""
                                UPDATE potions 
                                SET inventory = inventory + :additional_potions
                                WHERE potion_type = :potion_type
                                """),
                [{"additional_potions": potion.quantity,
                "potion_type": potion.potion_type}])
            
            print("additional_potions", potion.quantity, "potion_type", potion.potion_type)
        
        connection.execute(
                sqlalchemy.text("""
                                UPDATE globals SET 
                                red_ml = red_ml - :red_ml,
                                green_ml = green_ml - :green_ml,
                                blue_ml = blue_ml - :blue_ml,
                                dark_ml = dark_ml - :dark_ml
                                """),
                [{"red_ml": red_ml,
                "green_ml": green_ml,
                "blue_ml": blue_ml,
                "dark_ml": dark_ml}])

    return "OK"


def create_potions(ml, potion_type, result_array, threshold):
    new = 0

    while ml[0] >= threshold[0] and ml[1] >= threshold[1] and ml[2] >= threshold[2] and ml[3] >= threshold[3]:
        for i in range(4):
            ml[i] -= potion_type[i]
        new += 1
    
    if new > 0:
        result_array.append({
            "potion_type": potion_type,
            "quantity": new,
        })


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    with db.engine.begin() as connection:
        q = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM globals")).fetchone()

        ml_amounts = [q[0], q[1], q[2], q[3]]

        potions = connection.execute(sqlalchemy.text("""SELECT potion_type
                                                        FROM potions
                                                        ORDER BY inventory ASC, cost ASC""")).fetchall()

        res = []
        for pot in potions:
            if pot[0][0] == 100 or pot[0][1] == 100 or pot[0][2] == 100 or pot[0][3] == 100:
                double_threshold = [2 * value for value in pot[0]]
                create_potions(ml_amounts, pot[0], res, double_threshold)
            else:
                create_potions(ml_amounts, pot[0], res, pot[0]) 

        print(res)
        return res
