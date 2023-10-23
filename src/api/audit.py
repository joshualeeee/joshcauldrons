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
        results = connection.execute(sqlalchemy.text("""
                                                  SELECT sum(potion_change) as pots, sum(ml_change) as mls, sum(gold_change) as gold
                                                FROM transactions_orders
                                                  """)).fetchone()

    print("number_of_potions", results[0], "ml_in_barrels", results[1], "gold", results[2])
    return {"number_of_potions": results[0], "ml_in_barrels": results[1], "gold": results[2]}

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
