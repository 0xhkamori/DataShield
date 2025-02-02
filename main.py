import os, asyncio, sys, logging
from config import TOKEN
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types.input_file import FSInputFile
from encrypt import encrypt
from decrypt import decrypt

router = Router()
bot = Bot(token=TOKEN)

class FileOperation(StatesGroup):
    waiting_for_file = State()
    waiting_for_key = State()

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔒 Encrypt File", callback_data="encrypt"),
                InlineKeyboardButton(text="🔓 Decrypt File", callback_data="decrypt")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Help", callback_data="help")
            ]
        ]
    )
    return keyboard

def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel Operation", callback_data="cancel")]
        ]
    )

@router.message(CommandStart())
async def start_bot(message: Message):
    await message.answer(
        "🔐 <b>Welcome to File Encryption Bot!</b>\n\n"
        "I can help you encrypt and decrypt your files securely.\n"
        "Choose an operation below:",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📚 <b>How to use this bot:</b>\n\n"
        "1️⃣ Choose whether to encrypt or decrypt a file\n"
        "2️⃣ Send your file when prompted\n"
        "3️⃣ Provide an encryption/decryption key\n\n"
        "🔒 <b>For encryption:</b>\n"
        "• Send any file and create a new key\n"
        "• Save the key safely - you'll need it to decrypt!\n\n"
        "🔓 <b>For decryption:</b>\n"
        "• Send an encrypted file\n"
        "• Provide the original encryption key\n\n"
        "⚠️ <b>Security Note:</b>\n"
        "Keep your encryption keys private and secure!",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data.in_({"encrypt", "decrypt"}))
async def process_operation_selection(callback: CallbackQuery, state: FSMContext):
    operation = callback.data
    await state.update_data(operation=operation)
    await state.set_state(FileOperation.waiting_for_file)

    message_text = (
        "🔒 <b>Send the file you want to encrypt</b>"
        if operation == "encrypt" else
        "🔓 <b>Send the encrypted file you want to decrypt</b>"
    )

    await callback.message.edit_text(
        f"{message_text}\n\n"
        "📁 Send any file to continue...",
        reply_markup=get_cancel_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.message(FileOperation.waiting_for_file, F.document)
async def process_file(message: Message, state: FSMContext):
    await state.update_data(file=message.document.file_id)
    await state.set_state(FileOperation.waiting_for_key)

    data = await state.get_data()
    operation = data['operation']

    if operation == "encrypt":
        await message.answer(
            "🔑 <b>Create an encryption key</b>\n\n"
            "⚠️ Remember this key - you'll need it to decrypt the file later!",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            "🔑 <b>Enter the decryption key</b>\n\n"
            "This should be the same key used for encryption.",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.HTML
        )

@router.message(FileOperation.waiting_for_key, F.text)
async def process_key(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = data.get('file')
    operation = data.get('operation')
    key = message.text

    processing_message = await message.answer(
        "⏳ Processing your file...",
        parse_mode=ParseMode.HTML
    )

    try:
        if operation == "encrypt":
            output = await encrypt(file_id, key, bot)
            success_text = "✅ <b>File successfully encrypted!</b>"
        else:
            output = await decrypt(file_id, key, bot)
            success_text = "✅ <b>File successfully decrypted!</b>"

        await processing_message.delete()
        await message.answer(success_text, parse_mode=ParseMode.HTML)
        if operation == "encrypt":
            await message.answer(
                f"🔑 <b>Encryption Key:</b> <code>{key}</code>\n\n"
                "⚠️ Save this key in a secure place!",
                parse_mode=ParseMode.HTML
            )

        await message.answer_document(
            FSInputFile(output),
            caption="🎉 Here's your processed file!"
        )

        await message.answer(
            "Would you like to perform another operation?",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )

        os.remove("file")
        os.remove(output)
        await state.clear()

    except ValueError:
        await processing_message.delete()
        await message.answer(
            "❌ <b>Error:</b> Invalid decryption key!\n"
            "Please try again with the correct key.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await state.clear()
    except Exception as e:
        await processing_message.delete()
        await message.answer(
            "❌ <b>An error occurred while processing your file.</b>\n"
            "Please try again later.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await state.clear()
        logging.error(f"Error processing file: {e}")

@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Operation cancelled.\n\n"
        "Would you like to try something else?",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    asyncio.run(main())
