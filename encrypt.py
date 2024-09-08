import os
import pyAesCrypt

async def encrypt(file, key, bot):
    file_id = file
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, 'file')
    file_name = os.path.basename(file_path)
    file = os.path.splitext(file_name)
    output = 'file_enc' + file[1]
    pyAesCrypt.encryptFile("file", output, key)

    return output