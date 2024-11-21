from config.sql_token import sql_connection, sql_pass
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import pandas as pd
import logging

def create_db_engine():
    """
    Create the engine
    """

    return create_engine(sql_connection % quote_plus(sql_pass))

def select(sql: str, engine: any) -> pd.DataFrame:
    """
    Convert 'SELECT' SQL query to DataFrame
    """
    try:
        return pd.read_sql(sql, engine)
    except Exception as e:
        logging.error(f'Error executing SQL query: {e}')
        return pd.DataFrame()

