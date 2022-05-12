from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message
from apscheduler.triggers.interval import IntervalTrigger

from schedulers.jobs import add_user_checker
from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import CreateChecker, EditChecker


@checker_router.message(Command(commands=['edit_checker']))
async def edit_checker(message: Message, state: FSMContext):
    """Entry point for create checker conversation"""

    await message.answer(
        'Let\'s see...\n'
        'What do you want to edit?'
    )

    await state.set_state(EditChecker.chain)


@checker_router.message(state=CreateChecker.chain)
async def enter_chain(message: Message, state: FSMContext):
    """Enter chain name"""
    data = await state.get_data()
    data['chain'] = message.text
    await message.answer(
        'Okay, now I need the name of this validator'
    )

    await state.update_data(data)
    await state.set_state(EditChecker.operator_address)


@checker_router.message(state=EditChecker.operator_address)
async def enter_operator_address(message: Message, state: FSMContext, scheduler):
    """Enter validator's name"""

    data = await state.get_data()
    moniker = message.text

    chain = data.pop('chain')
    data.setdefault('validators', {})

    i = len(data.get('validators'))
    data['validators'][i] = {
        'chain': chain,
        'operator_address': moniker
    }

    await message.answer(
        'Nice! Now I\'ll be checking this validator all day long '
        'till the end of time👌'
    )

    await state.set_state(None)
    await state.update_data(data)

    scheduler.add_job(
        add_user_checker,
        IntervalTrigger(minutes=10),
        kwargs={
            'user_id': message.from_user.id,
            'platform': chain,
            'moniker': moniker,
        },
        id=f'{message.from_user.id}:{i}'
    )
