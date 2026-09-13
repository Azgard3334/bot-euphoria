import json
import asyncio
import os
import aiomysql
from dotenv import load_dotenv
from utils.loggerManager import LoggerManager

load_dotenv()


def _require_env(name: str) -> str:
    """Возвращает значение переменной окружения или бросает исключение."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f'Отсутствует обязательная переменная окружения: {name}')
    return value


class Database:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            logger = LoggerManager().get_logger('database')
            try:
                cls._pool = await aiomysql.create_pool(
                    host=_require_env('DB_HOST'),
                    port=int(_require_env('DB_PORT')),
                    user=_require_env('DB_USER'),
                    password=_require_env('DB_PASSWORD'),
                    db=_require_env('DB_NAME'),
                    charset=_require_env('DB_CHARSET'),
                    autocommit=_require_env('DB_AUTOCOMMIT').lower() == 'true',
                    cursorclass=aiomysql.DictCursor,
                    minsize=int(_require_env('DB_MINSIZE')),
                    maxsize=int(_require_env('DB_MAXSIZE')),
                    pool_recycle=int(_require_env('DB_POOL_RECYCLE')),
                    connect_timeout=int(_require_env('DB_CONNECT_TIMEOUT')),
                    echo=_require_env('DB_ECHO').lower() == 'true',
                )
                logger.success('Подключение к базе данных установлено')
            except Exception as e:
                logger.exception(f'Ошибка подключения к базе данных: {e}')
                raise
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool is not None:
            logger = LoggerManager().get_logger('database')
            try:
                if hasattr(cls._pool, '_close_waiter'):
                    cls._pool._close_waiter.cancel()

                cls._pool.close()

                try:
                    await asyncio.wait_for(cls._pool.wait_closed(), timeout=10.0)
                except Exception:
                    pass

                cls._pool = None

                await asyncio.sleep(1)
                logger.info('Соединение с базой данных закрыто')
            except Exception as e:
                logger.exception(f'Ошибка при закрытии соединения с БД: {e}')
                cls._pool = None

    @classmethod
    async def execute(cls, query: str, params: tuple = ()):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()
                return cur.lastrowid

    @classmethod
    async def fetchall(cls, query: str, params: tuple = ()):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    @classmethod
    async def add(cls, id: int, info: json = {}, base: str = 'activities'):
        pool = await cls.get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                columns = ['id'] + list(info.keys())
                values = [id] + list(info.values())

                columns_str = ', '.join(columns)
                values_str = ', '.join(['%s'] * len(values))

                await cur.execute(f'INSERT INTO {base} ({columns_str}) VALUES ({values_str})', values)

    @classmethod
    async def get(cls, id: int, base: str = 'activities'):
        pool = await cls.get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f'SELECT * FROM {base} WHERE id = %s', (id,))
                result = await cur.fetchone()
                return result

    @classmethod
    async def set(cls, id: int, values, base: str = 'activities'):
        pool = await cls.get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                resp = ', '.join([f'{key} = %s' for key in values.keys()])
                vals = list(values.values()) + [id]

                await cur.execute(f'UPDATE {base} SET {resp} WHERE id = %s', (tuple(vals)))

    @classmethod
    async def delete(cls, id: int, base: str = 'activities'):
        pool = await cls.get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f'DELETE FROM {base} WHERE id = %s', (id,))
                await conn.commit()
