import json
from urllib.parse import urljoin

import aiohttp


class MintScanner:

    def __init__(self, base_api_uri, api_token):
        # Set up a request's session for interacting with the API.
        self.api_token = api_token
        self.session = aiohttp.ClientSession()
        self.base_api_uri = base_api_uri

    async def parse_application(self, platform: str, moniker: str):
        data = {
            "moniker": moniker,
            "token": self.api_token
        }
        response = await self._post(platform, json=data)

        return response

    async def get_repeated_missing_blocks(self, platform: str, consensus_pubkey: str):
        data = {
            "token": self.api_token,
            "platform": platform,
            "consensus_pubkey": consensus_pubkey,
        }
        response = await self._post('repeat', 'missed_block_counter', json=data)
        return response

    async def get_validators(self, platform: str):
        data = {
            "token": self.api_token,
        }
        response = await self._post('load_validators', platform, json=data)
        if response.get('ok'):
            return response.get('validators')
        else:
            return []

    async def _post(self, *args, **kwargs):
        return await self._request('post', *args, **kwargs)

    async def _get(self, *args, **kwargs):
        return await self._request('get', *args, **kwargs)

    async def _request(self, method, *relative_path_parts, **kwargs):
        parts = '/'.join(relative_path_parts)

        uri = urljoin(self.base_api_uri, parts)

        async with getattr(self.session, method)(uri, **kwargs) as resp:
            response = await resp.json()
            return response
