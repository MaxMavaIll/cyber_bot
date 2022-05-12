from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.handlers.manage_checkers.router import checker_router


@checker_router.message(Command(commands=['list_checkers']))
async def list_my_validators(message: Message, state: FSMContext):
    """List all registered validators"""

    data = await state.get_data()
    validators = data.get('validators')

    if validators:
        validators_str = 'I\'m checking the following validators:\n\n'
        validators_str = validators_str + '\n'.join([
            f'{num}. {validator["chain"]} {validator["operator_address"]}\n'
            for num, validator in enumerate(validators.values(), 1)
        ]
        )
    else:
        validators_str = 'No checkers are currently running. ' \
                         'You can add checker with /create_checker command'

    await message.answer(validators_str)
