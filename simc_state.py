import asyncio
import subprocess
from update_git import run_update
import os

async def run_simc_stats(simc_config:str,author_id): # 运行SimulationCraft，输入内容为原始simcaddon插件的内容
    path = "/home/liuxl/ktaimei/config/simc_caches/" + author_id
    if not os.path.exists(path):
        # 创建目录
        os.makedirs(path)
        print("导出文件夹目录已创建")
    else:
        print("导出文件夹目录已存在")
    try:
        print("❓",simc_config)

        #运行模拟器

        command = ['/home/liuxl/simc/engine/simc', simc_config,'html='f'{path}/index.html','threads=16','iterations=20000','calculate_scale_factors=1']
        print("🥲",command)
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            # 如果SimulationCraft返回非零退出码，打印错误信息，并抛出异常
            error_message = stderr.decode()
            print(f"SimulationCraft failed with exit code {process.returncode} and error message:\n{error_message}")
            raise Exception(f'SimulationCraft failed: {error_message}')


    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

    return stdout.decode()



async def get_simc_output_stats(simc_config:str,author_id): #作为一个函数能在其他py文件中被调用
    #await run_update()
    return await run_simc_stats(simc_config,author_id)