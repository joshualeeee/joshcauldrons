import os
import dotenv
from sqlalchemy import create_engine
import sqlalchemy

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
metadata_obj = sqlalchemy.MetaData()
carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=engine)
potions = sqlalchemy.Table("potions", metadata_obj, autoload_with=engine)
transactions_orders = sqlalchemy.Table("transactions_orders", metadata_obj, autoload_with=engine)
