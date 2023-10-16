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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    for barrel in barrels_delivered:
        gold_paid += barrel.price * barrel.quantity
        if barrel.potion_type == [1,0,0,0]:
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,1,0,0]:
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,0,1,0]:
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0,0,0,1]:
            dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("Invalid Potion Type")
        
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            """
            UPDATE globals SET
            red_ml = red_ml + :red_ml,
            green_ml = green_ml + :green_ml,
            blue_ml = blue_ml + :blue_ml,
            dark_ml = dark_ml + :dark_ml
            """),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}])

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
        query = connection.execute(sqlalchemy.text("""SELECT gold FROM globals""")).fetchone()
        
        gold = query[0]

        res = []
        bought = 0
        while gold >= 120 and bought < 5:
            bought += 1
            for barrel in wholesale_catalog:
                if options[current_index] == barrel.potion_type and (barrel.price == 100 or barrel.price == 120):
                    gold -= barrel.price
                    res.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    rotate_options()
                    break
        if bought == 0:
            rotate_options()
    
    print(res)
    return res
