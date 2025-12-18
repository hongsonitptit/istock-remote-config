from typing import Dict, List
from logger import default_logger as logger
import sqlalchemy as db
from sqlalchemy.engine import ResultProxy
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from database.postgre_engine_factory import PostgreEngineFactory, NEON_ENGINE, NHOST_ENGINE, COCK_ENGINE

Base = declarative_base()

def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


@singleton
class PostgreDatabase():
    def __init__(self):
        self.engine = PostgreEngineFactory.get_engine(COCK_ENGINE)
        # logger.debug("DB Engine created")

    def get_session(self) -> Session:
        return Session(bind=self.engine.connect())

    def dispose(self):
        self.engine.dispose()

    def raw_query(self, sql_cmd: str) -> List[Dict]:
        session = self.get_session()
        try:
            session.expire_all() # Expire all objects in the session to ensure fresh data
            result = session.execute(text(sql_cmd))
            return [dict(item) for item in result.mappings()]
        finally:
            session.close()
    
    def crud_query(self, sql_cmd: str):
        session = self.get_session()
        try:
            session.execute(text(sql_cmd))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# pg_db = PostgreDatabase()


class PostgreHandler():
    def save(self, commit: bool = True):
        session = PostgreDatabase().get_session()
        try:
            session.add(self)
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update(self, commit: bool = True):
        session = PostgreDatabase().get_session()
        try:
            maps = [self.to_dict()]
            session.bulk_update_mappings(self.__class__, mappings=maps)
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def upsert(self, commit: bool = True):
        session = PostgreDatabase().get_session()
        try:
            session.add(self)
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            try:
                maps = [self.to_dict()]
                session.bulk_update_mappings(self.__class__, mappings=maps)
                if commit:
                    session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        finally:
            session.close()

    def remove(self, commit: bool = True):
        session = PostgreDatabase().get_session()
        try:
            session.delete(self)
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def to_dict(self) -> dict:
        result = {}
        for item in self._sa_instance_state.attrs:
            # key = f"{self.__tablename__}.{item.key}"
            result[item.key] = item.value
        return result

    def set_data(self, data: dict):
        for key, value in data.items():
            if value is None:
                continue
            if hasattr(self, key):
                setattr(self, key, value)


# db = Database()