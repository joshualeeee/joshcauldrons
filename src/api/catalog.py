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
                                                    SELECT p.sku, p.potion_name, SUM(tran.potion_change), p.cost, p.potion_type
                                                    FROM transactions_orders as tran
                                                    JOIN potions AS p ON tran.potion_id = p.id
                                                    GROUP BY p.id
                                                  """)).fetchall()
    
    res = []
    for p in pots:
        if p[2] > 0:
            res.append({"sku": p[0],
                "name": p[1],
                "quantity": p[2],
                "price": p[3],
                "potion_type": p[4]})
    print("get_catalog:", res)
    return res
