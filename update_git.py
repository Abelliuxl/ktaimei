import asyncio
import subprocess

async def run_update():
    command1 = ['python', "/home/liuxl/Abelliuxl.github.io/update_githhub_pages.py"]

    process1 = await asyncio.create_subprocess_exec(*command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process1.communicate()

    if process1.returncode != 0:
        error_message1 = stderr.decode()
        print(f"SimulationCraft failed with exit code {process1.returncode} and error message:\n{error_message1}")
        raise Exception(f'SimulationCraft failed: {error_message1}')
    