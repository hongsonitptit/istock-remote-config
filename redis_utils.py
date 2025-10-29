import redis
from typing import Any
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
import json

redis_conn = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

REPORT_LINK_BLACKLIST_KEY = "report_link_blacklist"

REMOTE_CONFIG_KEY_NAME = 'remote-config'

def get_all_remote_config() -> dict:
    data = redis_conn.get(REMOTE_CONFIG_KEY_NAME)
    if not data:
        data = dict()
    else:
        data = json.loads(data)
    return data


def set_remote_config(data: dict):
    redis_conn.set(REMOTE_CONFIG_KEY_NAME, json.dumps(data))


def get_hall(key: str) -> dict:
    return redis_conn.hgetall(key)


def set_hset(key: str, symbol: str, value: Any):
    redis_conn.hset(key, symbol, value)


def set_hmset(key: str, data: dict):
    redis_conn.hmset(key, data)


def get_list(key: str):
    return redis_conn.lrange(key, 0, -1)


def add_to_list(key: str, value: str):
    redis_conn.rpush(key, value)


def shrink_list(key: str, count: int):
    redis_conn.lpop(key, count)


def set_expired(key: str, expired_time_s: int):
    redis_conn.expire(key, expired_time_s)


def set_hexpired(key: str, unix_time_seconds: int, field: str):
    redis_conn.hexpireat(key=key, unix_time_seconds=unix_time_seconds, fields=[field])