import asyncio

from core.ganglia import Ganglia
from utils.logger import init_logger

logger = init_logger('Memory')


class Thalamus:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._ganglia = Ganglia()

class ThalamusInterface:
    def __init__(self, thalamus: Thalamus):
        self._lock = asyncio.Lock()
        self._thalamus = thalamus