import sqlalchemy
from sqlalchemy.engine import Engine
from config import (
    NEON_DATABASE, NEON_HOST, NEON_PASSWORD, NEON_USER,
    NHOST_DATABASE, NHOST_HOST, NHOST_PASSWORD, NHOST_USER,
    COCK_DATABASE, COCK_HOST, COCK_PASSWORD, COCK_USER
)

NEON_ENGINE = "neon"
NHOST_ENGINE = "nhost"
COCK_ENGINE = "cock"

class PostgreEngineFactory():
    
    @staticmethod
    def get_engine(engine_type: str) -> Engine:
        if engine_type == NEON_ENGINE:
            HOST = NEON_HOST
            DATABASE = NEON_DATABASE
            USER = NEON_USER
            PASSWORD = NEON_PASSWORD
            return sqlalchemy.create_engine(f'postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}?options=endpoint%3Dep-misty-cake-843760')
        if engine_type == NHOST_ENGINE:
            HOST = NHOST_HOST
            DATABASE = NHOST_DATABASE
            USER = NHOST_USER
            PASSWORD = NHOST_PASSWORD
            CONNECTION_TIMEOUT_S = 8 * 60 * 60
            return sqlalchemy.create_engine(f'postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}',
                                           connect_args={"connect_timeout": CONNECTION_TIMEOUT_S},
                                           pool_pre_ping=True, # prevent server disconnect
                                           )
        if engine_type == COCK_ENGINE:
            # NOTE: remember to download CA cert to $HOME by follow command
            # curl --create-dirs -o $HOME/.postgresql/root.crt 'https://cockroachlabs.cloud/clusters/7528ccf1-1753-4e09-ba63-957c2c15159c/cert'
            HOST=COCK_HOST
            DATABASE=COCK_DATABASE
            USER=COCK_USER
            PASSWORD=COCK_PASSWORD
            PORT=26257
            # return sqlalchemy.create_engine(f"cockroachdb://istock:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=verify-full")
            return sqlalchemy.create_engine(f"cockroachdb://istock:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?options=--cluster%3Distock-3053")

            
        raise Exception(f"Cannot get engine with type = {engine_type}")