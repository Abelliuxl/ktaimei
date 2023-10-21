import re
from datetime import datetime

def process_input_string(input_string):#作用是输入simc的结果，返回chatgpt的评论
    import bot
    # 定义提取文本的函数
    def extract_text(input_string):
        pattern = r'Player(.*?)DPS-Error'
        match = re.search(pattern, input_string, re.DOTALL)
        if match:
            extracted_text = match.group(1).strip()
            return extracted_text
        else:
            return None

    # 定义提取内容的函数
    def extract_content(input_string):
        pattern = r'Actions:(.*?)Constant Buffs:'
        match = re.search(pattern, input_string, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            return extracted_content
        else:
            return None

    # 调用两个函数获取提取的结果
    text_result = extract_text(input_string)
    content_result = extract_content(input_string)
    current_datetime = str(datetime.now())

    # 结合两个结果到一个字符串变量
   # combined_result = f'模拟结果: {text_result}\n输出技能结果: {content_result}'
    combined_result = f'模拟结果: {text_result}'
    combined_question = """这是一个simulationcraft的部分结果，分析下列的数据，按格式提取以下关键信息：
    1.时间日期；
    2.测试角色的名称，等级，种族
    3.最后模拟出的dps数值,保留两位小数
    把提取出的信息使用设计排版好,不允许直接放原始数据，要有格式，最后并附上一句风趣幽默的评价,发送给我不要有任何多余的信息:"""
    combined_message = current_datetime + combined_question + combined_result  # 生成最终的字符串

    # 使用bot模块的make_request函数发送请求
    response = bot.make_request(combined_message)
    comments = response['choices'][0]['message']['content']

    # 返回评论
    return comments