import asyncio
from types import MappingProxyType

from utils.commons import load_user_prefs, save_user_prefs
from utils.logger import init_logger

logger = init_logger('Memory')


class Memory:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._user_prefs = load_user_prefs()

    async def get_timezone(self, ctx):
        async with self._lock:
            return (self._user_prefs.get(str(ctx.author.id), {})
                    .get('timezone', 'UTC'))

    async def get_timezone_by_id(self, user_id: str):
        async with self._lock:
            return (self._user_prefs.get(str(user_id), {})
                    .get('timezone', 'UTC'))

    async def get_alias(self, ctx):
        async with self._lock:
            return (self._user_prefs.get(str(ctx.author.id), {})
                    .get('alias', ctx.author.name))

    async def get_alias_by_id(self, user_id: str, default: str):
        async with self._lock:
            return self._user_prefs.get(str(user_id), {}).get('alias', default)

    async def has_prefs(self, user_id: str):
        async with self._lock:
            return str(user_id) in self._user_prefs

    async def get_prefs(self, user_id: str):
        async with self._lock:
            prefs = self._user_prefs.get(str(user_id), {})
            if not prefs:
                return self.create_default_preferences_dict(user_id)
            return prefs

    async def get_prefs_all(self):
        """
        Returns a read-only copy of the entire user preferences dictionary.
        Uses MappingProxyType for a true read-only view of the dictionary.
        """
        async with self._lock:
            return MappingProxyType(self._user_prefs)

    async def create_default_preferences(self, ctx):
        async with self._lock:
            prefs = {
                'name': ctx.author.display_name,
                'alias': ctx.author.display_name,
                'timezone': 'UTC'
            }
            self._user_prefs[str(ctx.author.id)] = prefs
            logger.info(f'created default preferences for {ctx.author.id} = {prefs}')
            await self.save_prefs()
            return prefs

    @staticmethod
    def create_default_preferences_dict(user_id: str):
        # Helper method for creating default prefs without context
        return {
            'name': str(user_id),
            'alias': str(user_id),
            'timezone': 'UTC'
        }

    async def save_prefs(self):
        async with self._lock:
            save_user_prefs(self._user_prefs)

    async def update_prefs(self, user_id: str, new_prefs: dict):
        async with self._lock:
            self._user_prefs[str(user_id)] = new_prefs
            await self.save_prefs()


# Create a singleton instance
state_manager = Memory()
