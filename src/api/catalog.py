from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        pots = connection.execute(sqlalchemy.text("""
                                                  SELECT sku, potion_name, inventory, cost, potion_type
                                                  FROM potions""")).fetchall()
    
    res = []
    for p in pots:
        if p[2] > 0:
            res.append({"sku": p[0],
                "name": p[1],
                "quantity": p[2],
                "price": p[3],
                "potion_type": p[4]})
    print(res)
    return res
