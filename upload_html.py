import asyncio
import subprocess

async def upload_files_async(file_path, target_path):
    command = ['coscmd', 'upload', '-r', file_path, target_path, '--ignore', '*.txt']
    process = await asyncio.create_subprocess_exec(*command)
    await process.communicate()
