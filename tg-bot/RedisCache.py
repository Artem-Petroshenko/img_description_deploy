import os

import redis.asyncio as redis


def get_env_var(var_name: str):
    """
    A function for safely obtaining an environment variable. If specified env is not exist raise EnvironmentError

    :param var_name: name of the environment variable
    :return: value of environment variable if it exists
    """
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f'Missing required environment variable: {var_name}')
    return value


REDIS_HOST = get_env_var("REDIS_HOST")
REDIS_PORT = get_env_var("REDIS_PORT")


async def get_redis():

    return redis.Redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/0", decode_responses=True)


async def cache_data(key: str, value: str, ttl: int = 3600):
    r = await get_redis()
    await r.setex(key, ttl, value)


async def get_cached_data(key: str):
    r = await get_redis()
    return await r.get(key)
