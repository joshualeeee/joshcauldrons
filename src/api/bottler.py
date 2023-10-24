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

        ml = [0,0,0,0]

        for potion in potions_delivered:
            ml[0] += potion.quantity * potion.potion_type[0]
            ml[1] += potion.quantity * potion.potion_type[1]
            ml[2] += potion.quantity * potion.potion_type[2]
            ml[3] += potion.quantity * potion.potion_type[3]

            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO transactions_orders (potion_id, potion_change, time)
                                SELECT p.id, :additional_potions, NOW()
                                FROM potions AS p
                                WHERE p.potion_type = :potion_type
                                """),
                [{"additional_potions": potion.quantity,
                "potion_type": potion.potion_type}])
            
            print("additional_potions", potion.quantity, "potion_type", potion.potion_type)
        
        for i, amount in enumerate(ml):
            if amount == 0:
                continue
            connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO transactions_orders (barrel_id, ml_change, time)
                                    VALUES (:id, :change, NOW())
                                    """),
                    [{"id": i + 1,
                    "change": amount * -1}])

    return "OK"


def create_potions(ml, potion_type, result_array, threshold, total):
    new = 0

    while ml[0] >= threshold[0] and ml[1] >= threshold[1] and ml[2] >= threshold[2] and ml[3] >= threshold[3]:
        if total < 300:
            for i in range(4):
                ml[i] -= potion_type[i]
            new += 1
            total += 1
        else:
            break
    
    if new > 0:
        result_array.append({
            "potion_type": potion_type,
            "quantity": new,
        })
    return new


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
        q = connection.execute(sqlalchemy.text("""
                                                SELECT barrel_id, SUM(ml_change) AS total_ml_change
                                                FROM transactions_orders
                                                WHERE barrel_id IN (1, 2, 3, 4)
                                                GROUP BY barrel_id
                                                ORDER BY barrel_id ASC
                                               """)).fetchall()
        
        p = connection.execute(sqlalchemy.text("""SELECT sum(potion_change) as pots FROM transactions_orders""")).fetchone()

        ml_amounts = []
        total_pots = p[0]
        print("total", total_pots)

        for amount in q:
            ml_amounts.append(amount[1])
        
        potions = connection.execute(sqlalchemy.text("""
                                                    SELECT p.potion_type
                                                    FROM potions as p
                                                    JOIN transactions_orders as tran ON p.id = tran.potion_id
                                                    GROUP BY p.id
                                                    ORDER BY SUM(tran.potion_change) ASC, p.cost DESC
                                                     """)).fetchall()
        res = []
        for pot in potions:
            if pot[0][0] == 100 or pot[0][1] == 100 or pot[0][2] == 100 or pot[0][3] == 100:
                double_threshold = [20 * value for value in pot[0]]
                new = create_potions(ml_amounts, pot[0], res, double_threshold, total_pots)
                total_pots += new
            else:
                new = create_potions(ml_amounts, pot[0], res, pot[0], total_pots) 
                total_pots += new

        print(total_pots, res, ml_amounts)
        return res
