import os
import pyAesCrypt

async def decrypt(file, key, bot):
    file_id = file
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, 'file')
    file_name = os.path.basename(file_path)
    file = os.path.splitext(file_name)
    output = 'file_dec' + file[1]
    pyAesCrypt.decryptFile("file", output, key)

    return output