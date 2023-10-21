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
from khl.card    import CardMessage, Card, Module, Element, Types, Struct
from typing import Dict, Union, List
from simc_gear_from_bags import gear_bag_saved
from simc_cardmessage import generate_simc_card_message
import tracemalloc
from khl import api, Message
from simc_gear_compare import simc_gear_compare
from upload_html import upload_files_async
import simc_state
import time
from fuzzywuzzy import fuzz
from heapq import nlargest


tracemalloc.start()



current_time = datetime.datetime.now()


async def upd_msg(msg_id: str, content, target_id=None, channel_type: Union[ChannelPrivacyTypes, str] = 'public', bot=bot):
        print(f"Updating message with msg_id: {msg_id}, content: {content}, target_id: {target_id}, channel_type: {channel_type}")  # Debug line
        if not isinstance(content,str):    
            content = json.dumps(content)
        data = {'msg_id': msg_id, 'content': content}
        if target_id is not None:
            data['temp_target_id'] = target_id
        if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
            result = await bot.client.gate.request('POST', 'message/update', data=data)
        else:
            result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
        print(f"Update result: {result}")  # Debug line
        return result


def save_to_file(new_card_message, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(new_card_message, f, indent=4, ensure_ascii=False)



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

# Function to 
# the API request
def make_request(content_q: str): #chatGPT通讯的实现函数
    data = {
        "model": "gpt-3.5-turbo-0613",
        "messages": [
            {"role": "system", "content": "一个暴躁、尖酸刻薄的资深魔兽世界玩家，做助手汇报工作完成任务很专业"},
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

# the translate request
def translate_request(content_q: str): #chatGPT通讯的实现函数
    data = {
        "model": "gpt-3.5-turbo-0613",
        "messages": [
            {"role": "system", "content": "Whenever I send you a message, you need to translate the sentence for me. If the sentence is in Chinese, translate it into English; if it's in English, translate it into Chinese. if it is not English or Chinese, translate it into English and Chinese. The translation must be accurate and natural, without any other extra irrelevant content."},
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


#按/tf和GPT交流
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

def find_best_match(content: str, data: list):
    best_match = None
    best_ratio = 0

    for item in data:
        journal_name = item.get("Journal name")
        if journal_name is not None:
            ratio = fuzz.ratio(process_journal_name(journal_name), process_journal_name(content))
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = item

    return best_match, best_ratio

def process_journal_name(name: str):
    name = name.lower().strip()
    name = name.replace("&", "").replace("and", "")
    return name

async def search_journal(msg: Message, content: str):
    current_time = datetime.datetime.now()
    logger.info(f"{current_time} - 📖： {content}")

    try:
        # 打开并读取json文件
        with open('/home/liuxl/journal_data/JCR_2023.json', 'r') as f:
            data = json.load(f)

        # 设置一个标识，用来检查是否找到了匹配项
        found = False

        # 使用find_best_match函数来找到最佳匹配
        best_match, best_ratio = find_best_match(content, data)

        if best_ratio > 80:  # you can adjust this threshold
            print(best_match)
            output = f"期刊名：{best_match.get('Journal name')}，影响因子：{best_match.get('2022 JIF')}"
            found = True
            await msg.reply(output)

        # 如果没有找到匹配项，打印一个消息
        if not found:
            print("未找到匹配的准确期刊名，开始搜索缩写")
            # 打开并读取json文件
            with open('/home/liuxl/journal_data/swapped_data.json', 'r') as f:
                swap_data = json.load(f)
            # 初始化一个列表来存储匹配度和对应的条目
            matches = []
            # 遍历数据中的每一个字典
            for item in swap_data:
                for k, v in item.items():
                    # 计算键与content_q的匹配度
                    key_ratio = fuzz.ratio(process_journal_name(k), process_journal_name(content))
                    # 计算值与content_q的匹配度
                    value_ratio = fuzz.ratio(process_journal_name(v), process_journal_name(content))
                    # 将匹配度和条目添加到列表中
                    matches.append(((key_ratio, value_ratio), (k, v)))

            # 找到匹配度最高的5个条目
            top_5_matches = nlargest(5, matches, key=lambda x: max(x[0]))

            # 打印结果
            for match in top_5_matches:
                print(f"Match: {match[1]}, Max Ratio: {max(match[0])}")
            output_list = []
            for match in top_5_matches:
            # 从JCR_2023.json文件中找到对应的'2022 JIF'值
                for item in data:
                    if item.get('Journal name') == match[1][1]:
                    # 将结果添加到output变量中
                        output_list.append(f"期刊名：{item.get('Journal name')}，影响因子：{item.get('2022 JIF')}")
                        break
            
            for result in output_list:
                print(result)
            
            output = '\n'.join(output_list)
            # await msg.reply(output_list)
            await msg.reply(output)
                
        logger.info(f"{current_time} - 🙃回答： {output}")

    except Exception as e:
        logger.info(f"{current_time} - 发生异常：{e}")
        await msg.reply("鸡你太美")

#查询影响因子/if
@bot.command(regex='(?s)/[iI][fF](.+)', case_sensitive=False)
async def check_journal_if(msg: Message,content_q: str):
    await search_journal(msg, content_q)

#自主发信息
@bot.on_message(MessageTypes.SYS) #鸡你太美、@回复
async def handle_text_mention(msg: RawMessage):
    content_mention = msg.content
    author_id = msg.author_id
    print('频道ID',msg.target_id)
    
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
                
    else:
        keywords = ['tf', 'moni', 'gf', 'cs', 'tm', 'mnsx']
        pattern = re.compile('|'.join(keywords), re.IGNORECASE)

        #在特定频道查询影响因子
        if msg.target_id == "3739936040444264":
            await search_journal(msg, content_mention)

        #在特定频道进行翻译
        if msg.target_id == "9446829885813673":
            logger.info(f"{current_time} - ❓提问： {content_mention}")

            try:
                # Make the API request
                content = translate_request(content_mention)

                # Send the model's output back to the chat
                await msg.reply(content['choices'][0]['message']['content'])
                logger.info(f"{current_time} - 🙃回答： {content['choices'][0]['message']['content']}")

            except Exception as e:
                logger.info(f"{current_time} - 发生异常：{e}")
                await msg.reply("鸡你太美")


        elif random.randint(1, 100) > 90 and not pattern.search(msg.content):
            content = msg.content
            logger.info(f"{current_time} - ❓提问： {content}")
            content_extend = """你是一个暴躁易怒，尖酸刻薄的人，偶尔看到了群里有人发了这个消息，你觉得非常烦，于是很刻薄地回复他/她，但是不要超过50个字，他的消息是：""" + content
            output = make_request(content_extend)
            comments = output['choices'][0]['message']['content']
            logger.info(f"{current_time} - 🙃回答： {comments}")
            await msg.reply('(met)' + author_id + '(met)' + comments)
                
#DPS模拟      
@bot.command(regex=r'(?is)/moni(.+)', case_sensitive=False)
async def simc_single(msg: Message,content:str):
    if msg.ctx.channel.id in ["8611282625041719", "8907901392281511"]: #只在指定频道生效
        content_q = content.replace("/moni", "").strip()    
        content_q_modified = content_q.replace("\\", "")

        file_name = f"{msg.author_id}.txt"  # 把字符串保存为以author_id.txt为文件名
        file_path = os.path.join("/home/liuxl/ktaimei/config/simc_caches", file_name)
        with open(file_path, "w") as file:
            file.write(content_q_modified)
        await gear_bag_saved(("/home/liuxl/ktaimei/config/simc_caches/" + f"{msg.author_id}.txt"),msg.author_id) #保存背包内的装备信息到author_id.json
        json_saved = "/home/liuxl/ktaimei/config/simc_caches/" + f"{msg.author_id}.json"
        simc_cardmessage = await generate_simc_card_message(json_saved, f"{msg.author_id}")
        logger.info(simc_cardmessage)
        await msg.reply(simc_cardmessage) #生成卡片

        '''
        output = await simc.get_simc_output(content_q_modified)# 传入原始字符串
        logger.info(output)
        answer = process_input_string(output)
        await msg.reply(answer)
        '''
    else:
        await msg.reply("请在指定频道使用模拟器,太长了，撑不住的")
        
        
#倒计时国服完蛋
@bot.command(name="gf")
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
    
#获取职业天赋
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
    
    
#点击卡片按钮事件
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def update_simc_card(bot:Bot,e:Event):
    msg_id = e.body['msg_id']
    target_id = e.body['target_id']
    value = e.body['value']
    author_id = e.body['user_id']
    channel = await bot.client.fetch_public_channel(e.body['target_id'])
    
    
    if value == "cancel":
        cancel_card = CardMessage(
            Card(Module.Header('已取消模拟')))
        await upd_msg(msg_id, cancel_card, "", channel_type='public', bot=bot)
        
        return
    
    if value == "start":
        await bot.client.send(channel, "正在模拟，请稍等")
        simc_config = "/home/liuxl/ktaimei/config/simc_caches/" + f"{author_id}.txt"
        simc_json = "/home/liuxl/ktaimei/config/simc_caches/" + f"{author_id}.json"
        with open(simc_json, 'r') as file:
                json_data = json.load(file)
                
        all_chossen_false = True
        for simc_name, simc_data in json_data.items():
            if simc_data['attributes']['chossen'] == True:
                all_chossen_false = False
                break
            
        if all_chossen_false:
            output = await simc.get_simc_output(simc_config,author_id)
            answer = process_input_string(output)
            http_link = """https://claymoreindex-1320217912.cos.ap-shanghai.myqcloud.com/""" + author_id + "/index.html"
            print(http_link)
            await upload_files_async("/home/liuxl/ktaimei/config/simc_caches/"+ author_id, '/')
            card_answer = CardMessage(
                Card(Module.Header('模拟结果如下'),
                     Module.Divider(),
                     Module.Section(answer),
                     Module.Section('  '),
                     Module.Divider(),
                     Module.Section(
                         '详细的内容点击右侧链接查看',
                         Element.Button('link', http_link, Types.Click.LINK, theme='primary'))))
            await bot.client.send(channel, card_answer)
        
        else:
            output = await simc_gear_compare(simc_config, simc_json,author_id)
            await bot.client.send(channel, '久等，模拟完成，等待结果')
            output_string = str(output)
            GPT_output_string = """这是一个simulationcraft装备组合模拟DPS的结果，根据结果汇报报告的内容：
            1.严格汇报格式：名字作为标题，装备按照DPS高低报告装备组合的DPS，gear序号或原始配置，展示每一个组合内的所有装备、装等、装备部位，不要原模原样放数据，要有格式
            2.最后附上一句风趣幽默的总结，要求不超过100字，除此之外不得有任何多余的文字
             报告：  """ + output_string
            answer_request = GPT_output_string + output_string
            
            answer = make_request(answer_request)
            comments = answer['choices'][0]['message']['content']
            card_comments = CardMessage(
                Card(Module.Header('模拟结果如下'),
                     Module.Divider(),
                     Module.Section(comments),
                     Module.Section('  '),
                     Module.Divider()))
            await bot.client.send(channel, card_comments)
        
    
    def create_card_message(file_path:str) -> CardMessage:
        with open(file_path, 'r') as file:
            data = json.load(file)
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

        card = Card(
            Module.Header('你需要一起对比其他装备吗？'),
            Module.Context('如果不选择，则直接模拟当前装备'),
            Module.Context(author_id)
        )

        sorted_data = sorted(data.items(), key=lambda x: x[1]['level'], reverse=True)
        

        for equip_name, equip_data in sorted_data:
            
            with open(file_path, 'r') as file:
                data_intime = json.load(file)
            
            
            equip_level = equip_data['level']
            equip_attributes = equip_data['attributes']
            equip_part = equip_attributes.get('part')  # 使用get方法获取部位属性，避免出现KeyError异常
            equip_part_chinese = part_mapping.get(equip_part, equip_part)
            
            if not equip_part_chinese:
                raise ValueError(f"装备 {equip_name} 的部位属性 {equip_part} 无效")  # 抛出错误报告
            else:
                if equip_name != value and data_intime.get(equip_name, {}).get("attributes", {}).get("chossen") == False:
                    equip_section = Module.Section(
                            f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                            Element.Button('参与模拟', equip_name, Types.Click.RETURN_VAL, theme='primary')
                        )    
                    card.append(equip_section)
                    data_intime[equip_name]['attributes']['chossen'] = False
                
                elif  equip_name != value and data_intime.get(equip_name, {}).get("attributes", {}).get("chossen") == True:
                    equip_section = Module.Section(
                    f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                        Element.Button('参与模拟', equip_name, Types.Click.RETURN_VAL, theme='secondary')
                    )    
                    card.append(equip_section)
                    data_intime[equip_name]['attributes']['chossen'] = True
                    
                elif  equip_name == value and data_intime.get(equip_name, {}).get("attributes", {}).get("chossen") == False:
                    equip_section = Module.Section(
                    f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                        Element.Button('参与模拟', equip_name, Types.Click.RETURN_VAL, theme='secondary')
                    )    
                    card.append(equip_section)
                    data_intime[equip_name]['attributes']['chossen'] = True
                
                elif  equip_name == value and data_intime.get(equip_name, {}).get("attributes", {}).get("chossen") == True:
                    equip_section = Module.Section(
                    f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                        Element.Button('参与模拟', equip_name, Types.Click.RETURN_VAL, theme='primary')
                    )    
                    card.append(equip_section)
                    data_intime[equip_name]['attributes']['chossen'] = False
            
            save_to_file(data_intime, file_path)                
        
        card.append(Module.Divider())
        card.append(
            Module.ActionGroup(
                Element.Button('开始', 'start', Types.Click.RETURN_VAL,theme='primary'),
                Element.Button('取消', 'cancel', Types.Click.RETURN_VAL,theme='danger')
            )
        )        

        return CardMessage(card)
    
    file_path = "/home/liuxl/ktaimei/config/simc_caches/" + f"{author_id}.json"
    cm = create_card_message(file_path)
    
    content = cm
    await upd_msg(msg_id, content, "", channel_type='public', bot=bot)
    
    
    
@bot.on_event(EventTypes.JOINED_CHANNEL)
async def joined_attrack(bot:Bot,e:Event):
    logging.info("Event triggered: JOINED_CHANNEL")

    send_channel_id_list = ["8099606056795106","4932665341111852"] #我希望在这些频道里面发消息
    channel = await bot.client.fetch_public_channel(e.body['channel_id'])
    logging.info(f"Channel fetched: {channel} channel_id: {e.body['channel_id']}")
   
    user_id = e.body['user_id'] #加入频道的用户id
    logging.info(f"User ID: {user_id}")

    guild_list = await bot.client.fetch_guild_list() #获取这个机器人加入的所有公会
    logging.info(f"Fetched guild list: {guild_list}")

    guild_id = channel.guild_id
    guild = await bot.client.fetch_guild(guild_id)
    guild_channel_list = await guild.fetch_channel_list() #获取公会的频道列表
    logging.info(f"Fetched channels for guild: {guild_channel_list}")
    for guild_channel in guild_channel_list: #遍历公会的频道列表
        if guild_channel.id in send_channel_id_list: #如果这个频道在我希望发送的频道列表里面
            send_channel_id = guild_channel.id #获取这个频道的id
            logging.info(f"Matched send channel in guild: {send_channel_id}")
            #这里是我希望发送的消息
            content = "你是一个心胸狭窄的憨憨，人菜脾气大，有个比你厉害比你优秀比你帅的来游戏语音频道了，你很不服气，准备了一番话对他阴阳怪气（不超过150字），你说道：" 
            GPT_output = make_request(content) #调用GPT3.5
            comments = GPT_output['choices'][0]['message']['content'] #提取GPT3.5的回复
            logging.info(f"GPT generated message: {comments}")
            respond_channel = await bot.client.fetch_public_channel(send_channel_id) #获取发送消息的频道
            await bot.client.send(respond_channel,'(met)'+user_id+'(met)'+ comments) #发送消息
            logging.info(f"Message sent to channel {send_channel_id}")
                

@bot.on_event(EventTypes.EXITED_CHANNEL)
async def exit_attrack(bot:Bot,e:Event):
    logging.info("Event triggered: EXITED_CHANNEL")

    send_channel_id_list = ["8099606056795106","4932665341111852"] #我希望在这些频道里面发消息
    channel = await bot.client.fetch_public_channel(e.body['channel_id'])
    logging.info(f"Channel fetched: {channel} channel_id: {e.body['channel_id']}")
   
    user_id = e.body['user_id'] #加入频道的用户id
    user = await bot.client.fetch_user(user_id)
    user_name = user.username
    logging.info(f"User name: {user_name}")
    logging.info(f"User ID: {user_id}")

    guild_list = await bot.client.fetch_guild_list() #获取这个机器人加入的所有公会
    logging.info(f"Fetched guild list: {guild_list}")

    guild_id = channel.guild_id
    guild = await bot.client.fetch_guild(guild_id)
    guild_channel_list = await guild.fetch_channel_list() #获取公会的频道列表
    logging.info(f"Fetched channels for guild: {guild_channel_list}")
    for guild_channel in guild_channel_list: #遍历公会的频道列表
        if guild_channel.id in send_channel_id_list: #如果这个频道在我希望发送的频道列表里面
            send_channel_id = guild_channel.id #获取这个频道的id
            logging.info(f"Matched send channel in guild: {send_channel_id}")
            #这里是我希望发送的消息
            content = "你是一个心胸狭窄的憨憨，人菜脾气大，有个比你厉害比你优秀比你帅的人，叫"+user_name+",打完游戏离开游戏语音频道了，你看他走了你来劲了，准备了一番话在公屏上阴阳怪气,并调侃他的名字（不超过150字），你说道：" 
            GPT_output = make_request(content) #调用GPT3.5
            comments = GPT_output['choices'][0]['message']['content'] #提取GPT3.5的回复
            logging.info(f"GPT generated message: {comments}")
            respond_channel = await bot.client.fetch_public_channel(send_channel_id) #获取发送消息的频道
            await bot.client.send(respond_channel,'\n \n' +comments) #发送消息
            logging.info(f"Message sent to channel {send_channel_id}")
                
                

                            

                            

@bot.command(regex=r'(?is)/mnsx(.+)', case_sensitive=False)
async def simc_single_stats(msg: Message, content: str):
    if msg.ctx.channel.id in ["8611282625041719", "8907901392281511"]: #只在指定频道生效
        print('content=',content)
        content_q = content.replace("/mnsx", "").strip()    
        print('content_q=',content_q)
        content_q_modified = content_q.replace("\\", "")
        print('content_q_modified=',content_q_modified)

        file_name = f"{msg.author_id}.txt"  # 把字符串保存为以author_id.txt为文件名
        file_path = os.path.join("/home/liuxl/ktaimei/config/simc_caches", file_name)
        with open(file_path, "w") as file:
            file.write(content_q_modified)
        await msg.reply('属性模拟真的很慢，又烧CPU，基本上都要1-2分钟左右，等等吧')
        output = await simc_state.get_simc_output_stats(file_path,msg.author_id)# 传入原始字符串
        with open('/home/liuxl/file.txt', 'w') as file:
            file.write(output)
        funny_phrases = [
            "跳皮筋",
            "吹泡泡",
            "抱大树",
            "唱小曲",
            "跑步道",
            "捏鼻子",
            "啃苹果",
            "撒豆子",
            "戳气球",
            "画图形",
            "读童话",
            "看星星",
            "拍皮球",
            "打雪仗",
            "扔飞盘",
            "捉迷藏",
            "喝冰茶",
            "蹦跳床",
            "滑滑板",
            "挥羽毛球",
            "吸吸管",
            "摸石头",
            "捡贝壳",
            "打篮球",
            "养小鸟",
            "种向日葵",
            "演木偶戏",
            "挤泡泡",
            "扇扇子",
            "搭积木",
            "捡石头",
            "蹦蹦床"]

        # 从列表中随机抽取一个元素
        await msg.reply('等不及可以啃地瓜')
        print("Wait for 4 second...")
        time.sleep(1)  # Pause execution for 1 second
        await msg.reply('或者也可以'+random.choice(funny_phrases))
        
        def extract_text(original_text):
            # 找到最后一个 "Scale Factors:" 的位置
            start = original_text.rfind("Scale Factors:")
            # 找到 "text report took" 的位置
            end = original_text.find("text report took")
            # 如果找不到这两个字符串，返回空字符串
            if start == -1 or end == -1:
                return ""
            # 截取 "Scale Factors:" 和 "text report took" 之间的内容
            extracted_text = original_text[start:end].strip()
            return extracted_text
        
        def replace_words_with_json(filename, original_text):
            # 读取 JSON 文件
            with open(filename, 'r') as f:
                translations = json.load(f)
            # 为每个词汇创建一个正则表达式并替换匹配项
            replaced_text = original_text
            for word, translation in translations.items():
                replaced_text = re.sub(r'\b' + word + r'\b', translation, replaced_text)
            return replaced_text
        print(extract_text(output))
        print(replace_words_with_json('/home/liuxl/ktaimei/config/en_cn_wow.json',extract_text(output)))
        final_text = """这是一个simulationcraft的各个属性对DPS影响的模拟结果，
        数字代表每提升相同份额的属性，DPS能提高的程度，括号内是误差，
        充分理解这几个数据，只保留他们数值的小数点后2位然后把它们排好版设计好格式发给我，
        并给出专业准确的评价，废话不要多"""+replace_words_with_json('/home/liuxl/ktaimei/config/en_cn_wow.json',extract_text(output))
        print(final_text)
        GTP_output = make_request(final_text)
        comments = GTP_output['choices'][0]['message']['content']
        http_link = """https://claymoreindex-1320217912.cos.ap-shanghai.myqcloud.com/""" + msg.author_id + "/index.html"
        comments_card = CardMessage(
            Card(
                Module.Header('模拟结果如下'),
                Module.Divider(),
                Module.Section(comments),
                Module.Section('  '),
                Module.Divider(),
                Module.Section(
                         '详细的内容点击右侧链接查看',
                         Element.Button('link', http_link, Types.Click.LINK, theme='primary'))
            ))
        await upload_files_async("/home/liuxl/ktaimei/config/simc_caches/"+ msg.author_id, '/')
        await msg.reply(comments_card)
                
        #logger.info(simc_cardmessage)
        #await msg.reply(simc_cardmessage) #生成卡片

    else:
        await msg.reply("跟你说了别在这儿搞啊？咋回事????去指定频道搞啊？")
    
    
    

    
    
if __name__ == "__main__":
    bot.run()
    
    
    #这个是叠了很多循环的写法，不是很对，但是可以用
# @bot.on_event(EventTypes.JOINED_CHANNEL) 
# async def joined_attrack(bot:Bot,e:Event):
#     logging.info("Event triggered: JOINED_CHANNEL")

#     send_channel_id_list = ["8099606056795106","4932665341111852"] #我希望在这些频道里面发消息
#     channel = await bot.client.fetch_public_channel(e.body['channel_id'])
#     logging.info(f"Channel fetched: {channel} channel_id: {e.body['channel_id']}")
   
#     user_id = e.body['user_id'] #加入频道的用户id
#     logging.info(f"User ID: {user_id}")

#     guild_list = await bot.client.fetch_guild_list() #获取这个机器人加入的所有公会
#     logging.info(f"Fetched guild list: {guild_list}")

#     for guild in guild_list: #遍历所有公会
#         guild_channel_list = await guild.fetch_channel_list() #获取公会的频道列表
#         logging.info(f"Fetched channels for guild: {guild_channel_list}")

#         for guild_channel in guild_channel_list: #遍历公会的频道列表
#             print(guild_channel.id)
#             if guild_channel.id == e.body['channel_id']: #如果在其中找到了用户加入的频道，说明现在这个就是他的公会
#                 logging.info(f"Matched channel in guild: {guild_channel.id}")
                
#                 for send_channel_id in send_channel_id_list: #遍历我希望发送消息的频道列表
#                     print("发送消息的频道",send_channel_id)
#                     send_channel = await bot.client.fetch_public_channel(send_channel_id)
#                     print("发送消息的频道",send_channel)
#                     for new_guild_channel in guild_channel_list: #遍历公会的频道列表
#                         if send_channel_id == new_guild_channel.id: #如果我希望发送消息的频道在这个公会的频道列表里面
#                             logging.info(f"Matched send channel in guild: {send_channel_id}")

#                             #这里是我希望发送的消息
#                             content = "你是一个心胸狭窄的憨憨，人菜脾气大，有个比你厉害比你优秀比你帅的来游戏语音频道了，你很不服气，准备了一番话讽刺他（不超过150字），你说道：" 
#                             GPT_output = make_request(content) #调用GPT3.5
#                             comments = GPT_output['choices'][0]['message']['content'] #提取GPT3.5的回复
#                             logging.info(f"GPT generated message: {comments}")
#                             respond_channel = await bot.client.fetch_public_channel(send_channel_id) #获取发送消息的频道
#                             await bot.client.send(respond_channel,'(met)'+user_id+'(met)'+ comments) #发送消息
#                             logging.info(f"Message sent to channel {send_channel_id}")




# #成员上下线的信息太慢了，所以暂时不用了
# #成员上线 
# @bot.on_event(EventTypes.GUILD_MEMBER_OFFLINE)
# async def offline_attrack(bot:Bot,e:Event):
#     guilds = e.body['guilds'] #guids 是一个列表,上线成员的所有公会ID
#     print(guilds)
#     channel_list = ["8099606056795106","4932665341111852"]#我希望在这些频道里面发消息
#     for guild_id in guilds:#遍历上线成员的所有公会
#         guild = bot.client.fetch_guild(guild_id) #提取公会这个元素
#         guild_channel_list = guild.fetch_channel_list() #提取公会的频道列表
#         for guild_channel in guild_channel_list:#遍历公会的频道列表
#     #这里要改的，fetch的频道是实体，不是字符串       if guild_channel in channel_list:#如果频道在我希望的频道列表里面
#                 target_id = guild_channel
#                 user_id = e.body['user_id']
#                 content = "你看不惯的家伙又来语音频道了，游戏又菜又喜欢指点江山，每天都很烦他，看到他终于从频道离线了，你准备在频道讽刺他，你说道："
#                 output = make_request(content)
#                 comments = output['choices'][0]['message']['content']
#                 channel = bot.client.fetch_public_channel(target_id)
#                 await bot.client.send(channel,'(met)'+user_id+'(met)'+ comments)

# #成员上线
# @bot.on_event(EventTypes.GUILD_MEMBER_ONLINE)
# async def offline_attrack(bot:Bot,e:Event):
#     guilds = e.body['guilds'] #guids 是一个列表,上线成员的所有公会ID
#     print(guilds)
#     channel_list = ["8099606056795106","4932665341111852"]#我希望在这些频道里面发消息
#     for guild_id in guilds:#遍历上线成员的所有公会
#         guild = bot.client.fetch_guild(guild_id) #提取公会这个元素
#         guild_channel_list = guild.fetch_channel_list() #提取公会的频道列表
#         for guild_channel in guild_channel_list:#遍历公会的频道列表
#             if guild_channel in channel_list:#如果频道在我希望的频道列表里面
#                 target_id = guild_channel
#                 user_id = e.body['user_id']
#                 content = "你看不惯的家伙又来语音频道了，游戏又菜又喜欢指点江山，每天都很烦他，看到他又来上线了，你准备在频道讽刺他，你说道："
#                 output = make_request(content)
#                 comments = output['choices'][0]['message']['content']
#                 channel = bot.client.fetch_public_channel(target_id)
#                 await bot.client.send(channel,'(met)'+user_id+'(met)'+ comments)