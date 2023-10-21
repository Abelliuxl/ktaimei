import asyncio
import subprocess
import os

async def run_simc(simc_config:str):
    #print("❓",simc_config)
    with open("/home/liuxl/ktaimei/profiles.text", "w") as f:
    # 将字符串写入到文件中
        f.write(simc_config)
    #print("🥲",command)
    command = "/home/liuxl/simc/engine/simc","/home/liuxl/ktaimei/profiles.text"
    process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        # 如果SimulationCraft返回非零退出码，打印错误信息，并抛出异常
        error_message = stderr.decode()
        print(f"SimulationCraft failed with exit code {process.returncode} and error message:\n{error_message}")
        raise Exception(f'SimulationCraft failed: {error_message}')

    return stdout.decode()

async def get_simc_output(simc_config:str):
    return await run_simc(simc_config)