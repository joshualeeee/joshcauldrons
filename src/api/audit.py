from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    
    with db.engine.begin() as connection:
        pots = connection.execute(sqlalchemy.text("""
                                                  SELECT inventory
                                                  FROM potions""")).fetchall()
        total_pots = 0
        for p in pots:
            total_pots += p[0]
        
        g = connection.execute(sqlalchemy.text("""
                                                  SELECT gold, red_ml, green_ml, blue_ml, dark_ml
                                                  FROM globals""")).fetchone()

    print("number_of_potions", total_pots, "ml_in_barrels", g[0], "gold", (g[1] + g[2] + g[3] + g[4]))
    return {"number_of_potions": total_pots, "ml_in_barrels": g[0], "gold": (g[1] + g[2] + g[3] + g[4])}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
