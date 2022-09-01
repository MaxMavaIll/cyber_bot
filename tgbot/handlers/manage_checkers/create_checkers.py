import logging
from datetime import datetime

from name_node import name
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from api.config import nodes
from api.functions import get_index_by_moniker
from api.requests import MintScanner
from schedulers.jobs import add_user_checker
from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import CreateChecker


@checker_router.message(Command(commands=['create_checker']))
async def create_checker(message: Message, state: FSMContext):
    """Entry point for create checker conversation"""

    await message.answer(
        'Let\'s see...\n'
        'What\'s your validator name?'
    )

    await state.set_state(CreateChecker.operator_address)


#
# @checker_router.message(state=CreateChecker.chain)
# async def enter_chain(message: Message, state: FSMContext):
#     """Enter chain name"""
#     data = await state.get_data()
#     if message.text in nodes.keys():
#         data['chain'] = message.text
#
#         await message.answer(
#             'Okay, now I need the name of this validator'
#         )
#         await state.set_state(CreateChecker.operator_address)
#         await state.update_data(data)
#     else:
#         await message.answer(
#             'Sorry, but we dont have this validator\'s network\n'
#             'Try again'
#         )


@checker_router.message(state=CreateChecker.operator_address)
async def enter_operator_address(message: Message, state: FSMContext,
                                 scheduler: AsyncIOScheduler,
                                 mint_scanner: MintScanner):
    """Enter validator's name"""
    moniker = message.text
    data = await state.get_data()
    name_node = name
    validators = await mint_scanner.get_validators(name_node)
    logging.info(f'Got {len(validators)} validators')

    if get_index_by_moniker(moniker, validators) is None:
        await message.answer(
            'Sorry, but I don\'t found this validator'
        )
        await state.set_state(None)
    else: 

        data.setdefault('validators', {})
        i = str( len(data.get('validators')) )
        for validator_id, validator in data['validators'].items():
            if validator['operator_address'] == moniker:
                await state.set_state(None)

                return await message.answer(
                    'You already have this validator in your list'
                )
        
        logging.info(f'\n\n\n, {data}, \n\n\n')

        data['validators'][i] = {
            'chain': name_node,
            'operator_address': message.text
        }
        logging.info(f'"\n\n\n", {data}, "\n\n\n"')
        print("\n\n\n", data, "\n\n\n")
        await message.answer(
            'Nice! Now I\'ll be checking this validator all day👌'
            )
        # await message.send_stiker(message)

        await state.set_state(None)
        logging.info(f'"\n\n\n", {data}, "\n\n\n"')
        await state.update_data(data)

        scheduler.add_job(
            add_user_checker,
            IntervalTrigger(minutes=10),
            kwargs={
                'user_id': message.from_user.id,
                'platform': name_node,
                'moniker': moniker,
            },
            id=f'{message.from_user.id}:{name_node}:{moniker}',
            next_run_time=datetime.now()
        )

