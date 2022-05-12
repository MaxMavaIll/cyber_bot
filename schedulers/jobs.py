import json
import logging

from aiogram import Bot
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from api.requests import MintScanner
from schedulers.exceptions import raise_error


async def add_user_checker(bot: Bot, mint_scanner: MintScanner, user_id: int, platform: str, moniker: str,
                           storage: RedisStorage):
    checkers = await storage.redis.get('checkers') or '{}'
    checkers = json.loads(checkers)
    if str(user_id) not in checkers:
        checkers[str(user_id)] = {}

    if platform not in checkers[str(user_id)]:
        checkers[str(user_id)][platform] = {}

    if moniker not in checkers[str(user_id)][platform]:
        checkers[str(user_id)][platform][moniker] = {
            'last_check': 0,
        }

    last_check = checkers[str(user_id)].get(platform, {}).get(moniker, {}).get('last_check', 0)

    data = await mint_scanner.parse_application(platform, moniker)

    if not data['ok']:
        await bot.send_message(user_id, "Error happened: " + data['error'] + "\n\n" + f'{moniker=}, {platform=}')
        raise raise_error(data['error'])

    missed_blocks_counter = data['missed_blocks_counter']

    logging.info(f"Missed blocks counter: {missed_blocks_counter}")
    if missed_blocks_counter > last_check:
        await bot.send_message(user_id, f"I've found {missed_blocks_counter} missed blocks. On {platform} network, "
                                        f"moniker: {moniker}.")

    checkers[str(user_id)][platform][moniker]['last_check'] = missed_blocks_counter
    await storage.redis.set('checkers', json.dumps(checkers))
