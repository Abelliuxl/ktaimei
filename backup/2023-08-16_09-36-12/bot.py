import json
import requests
from khl import *
from khl.command import *
import datetime 
import random
import os
import logging
import re
import simc
from logging.handlers import TimedRotatingFileHandler
from DPSdata import process_input_string
from raider_talents import fetch_talent_loadouts
from khl.card    import CardMessage, Card, Module, Element, Types
from typing import Dict

current_time = datetime.datetime.now()

# Load config from json file
with open('/home/liuxl/ktaimei/config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Define your OpenAI API key and the new URL
openai_api2d_api_key = config['openai_api2d_api_key']
openai_api2d_url = config['openai_api2d_url']

# Initialize bot
bot = Bot(token=config['token'])  # default is using websocket

if not config['using_ws']:  # if using webhook
    print(f"[BOT] using webhook at port {config['webhook_port']}")
    bot = Bot(cert=Cert(token=config['token'],
                        verify_token=config['verify_token'],
                        encrypt_key=config['encrypt_token']),
              port=config['webhook_port'])

# Function to make the API request
def make_request(content_q: str): #chatGPT通讯的实现函数
    data = {
        "model": "gpt-3.5-turbo-16k-0613",
        "messages": [
            {"role": "system", "content": "你是一个脾气暴躁、尖酸刻薄的资深魔兽世界玩家,作为助手执行任务认真、严谨,回答一些主观问题时不要超过150字"},
            {"role": "user", "content": content_q},
        ]
    }

    # Make the API request
    response = requests.post(
        openai_api2d_url,
        headers={'Authorization': f'Bearer {openai_api2d_api_key}'},
        json=data,
    )

    # Check for errors
    response.raise_for_status()

    # Get the content of the response
    return response.json()

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
log_dir = '/home/liuxl/ktaimei/log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'bot.log')
file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7, atTime=datetime.time(5, 0, 0))
file_handler.suffix = "%Y-%m-%d.log"
file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")

# Create a stream handler (for console output)
stream_handler = logging.StreamHandler()

# Set a format for the handlers
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

@bot.command(regex='(?s)/[tT][mM](.+)', case_sensitive=False)
async def handle_text_msg(msg: Message,content_q: str):
    current_time = datetime.datetime.now()
    logger.info(f"{current_time} - ❓提问： {content_q}")

    try:
        # Make the API request
        content = make_request(content_q)

        # Send the model's output back to the chat
        await msg.reply(content['choices'][0]['message']['content'])
        logger.info(f"{current_time} - 🙃回答： {content['choices'][0]['message']['content']}")

    except Exception as e:
        logger.info(f"{current_time} - 发生异常：{e}")
        await msg.reply("鸡你太美")

@bot.on_message(MessageTypes.SYS) #鸡你太美、@回复
async def handle_text_mention(msg: RawMessage):
    content_mention = msg.content
    
    if "(met)726976194(met)" in content_mention:
        if content_mention.replace(" ", "") == "(met)726976194(met)":
            await msg.reply("鸡你太美")
        else:
            new_content_mention = content_mention.replace("(met)726976194(met)", "你")
            logger.info(f"{current_time} - ❓提问： {new_content_mention}")

            try:
                # Make the API request
                content = make_request(new_content_mention)

                # Send the model's output back to the chat
                await msg.reply(content['choices'][0]['message']['content'])
                logger.info(f"{current_time} - 🙃回答： {content['choices'][0]['message']['content']}")

            except Exception as e:
                logger.info(f"{current_time} - 发生异常：{e}")
                await msg.reply("鸡你太美")
                
                
@bot.command(regex=r'(?is)/moni(.+)', case_sensitive=False)
async def simc_single(msg: Message,content:str):
    if msg.ctx.channel.id in ["8611282625041719", "8907901392281511"]: #只在指定频道生效
        content_q = content.replace("/moni", "").strip()    
        content_q_modified = content_q.replace("\\", "")
        output = await simc.get_simc_output(content_q_modified)# 传入原始字符串
        logger.info(output)
        answer = process_input_string(output)
        await msg.reply(answer)
    
@bot.command(name="gf")#倒计时国服完蛋
async def gf_count(msg: Message):
    target_date = datetime.datetime(2023, 1, 24, 0, 0)
    time_passed = datetime.datetime.now() - target_date

    # 提取 timedelta 对象的天数和秒数
    days = time_passed.days
    seconds = time_passed.seconds

    # 将秒数转换为小时和分钟
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # 将结果转换为中文并打印
    result = "{}天{}小时{}分钟".format(days, hours, minutes)
    reply = "距离国服魔兽世界关服已经过去了: "+ str(result)
    logger.info(reply)
    await msg.reply(reply)
    

@bot.command(regex=r'(?is)/tf(.+)', case_sensitive=False)
async def talent_fetch(msg: Message, content: str):
    content = content.strip().lower()
    print(content)  
    if not content or content.isspace():
        await msg.reply("缺少具体职业，输入职业简称/tf 惩戒骑")
        return
    else:
        if content == "jc":
            with open("/home/liuxl/ktaimei/config/class_spec_abbre.txt", "r") as file:
                file_content = file.read()
                await msg.reply(file_content)
            return

    result = await fetch_talent_loadouts(content)
    if result is None:
        await msg.reply("无法找到匹配的职业和专精")
        return

    result_string = result
    await msg.reply(result_string)
    
    
#测试用
@bot.command(name="cs")
async def test_bot(msg: Message):
    
    part_mapping = {
        "# head": "头",
        "# neck": "项链",
        "# shoulder": "肩",
        "# back": "披风",
        "# chest": "胸",
        "# wrist": "腕",
        "# hands": "手",
        "# waist": "腰带",
        "# legs": "腿",
        "# feet": "脚",
        "# finger1": "戒指",
        "# trinket1": "饰品",
        "# main_hand": "主手",
        "# off_hand": "主手"      
    }
    
    def create_card_message(data: Dict[str, Dict[str, str]]) -> CardMessage:
        card = Card(
            Module.Header('你需要一起对比其他装备吗？'),
            Module.Context('如果不选择，则直接模拟当前装备')
        )

        # 对 data 进行排序
        sorted_data = sorted(data.items(), key=lambda x: x[1]['level'], reverse=True)

        for equip_name, equip_data in sorted_data:
            equip_level = equip_data['level']
            equip_attributes = equip_data['attributes']
            equip_part = equip_attributes['part']
            equip_part_chinese = part_mapping.get(equip_part, equip_part)
            equip_section = Module.Section(
                f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                Element.Button('参与模拟', '1', Types.Click.RETURN_VAL)
            )
            card.append(equip_section)            

        return CardMessage(card)

    with open('/home/liuxl/下载/gear_from_bags.json', 'r') as file:
            json_data = json.load(file)
    c = create_card_message(json_data)
    await msg.reply(c)
    
    
if __name__ == "__main__":
    bot.run()