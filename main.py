import asyncio
import sys
import logging
import os
from config import TOKEN
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types.input_file import FSInputFile
from encrypt_file import encrypt
from decrypt_file import decrypt

router = Router()
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML, session=session)

class FileEnc(StatesGroup):
    file = State()
    key = State()

class FileDec(StatesGroup):
    file = State()
    key = State()

@router.message(CommandStart())
async def start_bot(message: Message):
    await message.answer('<b>Зашифрувати файл - /encrypt \
    \nРозшифрувати файл - /decrypt</b>')

# EncryptFile

@router.message(Command('encrypt'))
async def get_file(message: Message, state: FSMContext):
    await message.answer('<b>Відправте файл📁</b>')
    await state.set_state(FileEnc.file)

@router.message(FileEnc.file, F.document)
async def get_key(message: Message, state: FSMContext):
    await state.update_data(file=message.document.file_id)
    await message.answer('<b>Придумайте ключ🔑</b>')
    await state.set_state(FileEnc.key)

@router.message(FileEnc.key, F.text)
async def encrypt_file(message: Message, state: FSMContext):
    data = await state.get_data()
    file = data.get('file')
    key = message.text
    output = await encrypt(file, key, bot)
    await message.answer('<b>Файл успішно зашифровано🔒</b>')
    await message.answer(f'<b>Ключ: <code>{key}</code>🔑</b>')
    await message.answer_document(FSInputFile(output))
    os.remove("file")
    os.remove(output)
    await state.clear()

# DecryptFile

@router.message(Command('decrypt'))
async def get_file_enc(message: Message, state: FSMContext):
    await message.answer('<b>Відправте файл📁</b>')
    await state.set_state(FileDec.file)

@router.message(FileDec.file, F.document)
async def get_key_enc(message: Message, state: FSMContext):
    await state.update_data(file=message.document.file_id)
    await message.answer('<b>Відправте ключ🔑</b>')
    await state.set_state(FileDec.key)

@router.message(FileDec.key, F.text)
async def decrypt_file(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        file = data.get('file')
        key = message.text
        output = await decrypt(file, key, bot)
        await message.answer('<b>Файл успішно розшифровано🔓</b>')
        await message.answer_document(FSInputFile(output))
        os.remove("file")
        os.remove(output)
        await state.clear()
    except ValueError:
        await message.answer('<b>Невірний ключ❌</b>')

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())