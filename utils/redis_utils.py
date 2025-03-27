import json
import os
from redis import ConnectionPool, Redis
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from utils.logger import init_logger

# Load environment variables
load_dotenv()

# Create a connection pool that can be reused
REDIS_POOL = ConnectionPool(
    host=os.getenv('REDIS_HOST', '192.168.7.168'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

logger = init_logger('redis')

def get_redis_client() -> Redis:
    """Get a Redis client using the connection pool"""
    return Redis(connection_pool=REDIS_POOL)


def write_data_to_redis(key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """
    Write data to Redis server using JSON serialization

    Args:
        data: Dictionary to store in Redis
        key: The key under which to store the data
        ttl: Time to live in seconds (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    redis = get_redis_client()
    try:

        # Convert the data to JSON string
        json_data = json.dumps(data, indent=None)
        data_size_kb = len(json_data) / 1024
        logger.info(f'Saving {data_size_kb:.2f} KB to Redis key: {key}')

        # Store the JSON string in Redis
        if ttl is not None:
            redis.setex(key, ttl, json_data)
        else:
            redis.set(key, json_data)

        return True

    except Exception as e:
        logger.warn(f'Error writing to Redis: {str(e)}')
        return False


def read_data_from_redis(key: str) -> Optional[Dict]:
    """
    Read data from Redis server and parse JSON

    Args:
        key: The key to retrieve the data from

    Returns:
        Dict if successful, None if key doesn't exist or on error
    """
    try:
        redis_client = get_redis_client()
        json_data = redis_client.get(key)

        if json_data is None:
            logger.warn(f'No data found for key: {key}')
            return None

        return json.loads(json_data)

    except Exception as e:
        logger.warn(f'Error reading from Redis: {str(e)}')
        return None



write_data_to_redis("kent", {"1": "asdfasfasdfsaf"})

logger.info(read_data_from_redis("kent"))