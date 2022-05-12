from aiogram import Router
from aiogram.types import Message

user_router = Router()


@user_router.message(commands=["start"])
async def user_start(message: Message):
    await message.reply(f'Hello, {message.chat.first_name}! \n'
                        '\n'
                        'You can add validator checker through /create_checker command. \n'
                        ' - This will make me check this validator for missing blocks. \n'
                        'You can show your validator checker through /list_checker command.\n'
                        'You can delete your validator checker through /delete_checker command.\n'
                        '\n'
                        'Hey, if you like this bot, you can delegate funds to the web34ever validator.')
