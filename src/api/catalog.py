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
    query = "SELECT num_red_potions FROM global_inventory"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
    
    row = result.fetchone()
    if row is not None:
        num_red_potions = row[0]

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
