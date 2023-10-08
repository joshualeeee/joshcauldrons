from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    query = "SELECT num_red_potions, num_blue_potions, num_green_potions FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
    
    row = result.fetchone()
    if row is not None:
        num_red_potions = row[0]
        num_blue_potions = row[1]
        num_green_potions = row[2]
    
    pots = []
    
    

    if num_red_potions > 0:
        pots.append({
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            })
    
    if num_blue_potions > 0:
        pots.append({
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue_potions,
                "price": 60,
                "potion_type": [0, 0, 100, 0],
            })
        
    if num_green_potions > 0:
        pots.append({
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            })
    
    return pots
