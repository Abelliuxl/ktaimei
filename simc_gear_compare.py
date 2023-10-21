import json
import itertools
import re
import os
import asyncio
import subprocess
import simc

async def simc_gear_compare(simc_config, simc_json,author_id):
    
    if not os.path.exists(f'/home/liuxl/ktaimei/config/simc_caches/{author_id}'):
        os.makedirs(f'/home/liuxl/ktaimei/config/simc_caches/{author_id}')
        print("文件夹已创建")
    else:
        print("文件夹已存在")
        
    output_file_path = f'/home/liuxl/ktaimei/config/simc_caches/{author_id}'
    
    
    with open(simc_json, 'r') as file:
        json_data = json.load(file)


    chossen_items = {
        k: v for k, v in json_data.items() if v.get('attributes', {}).get('chossen')
    }





    def format_item(item):
        item_name = item[0]
        level = item[1]['level']
        attributes = item[1]['attributes']
        parts = ['='.join([str(k), str(v)]) for k, v in attributes.items() if k != 'part' and k != 'chossen']
        # Remove the '#' from the part and move the part and its attributes to a new line
        part_and_attributes = f"{attributes['part']}={','.join(parts)}"
        part_and_attributes = part_and_attributes.replace('# ', '')
        part_and_attributes = part_and_attributes.replace('id', ',id', 1)  # add a comma before the first 'id'
        return f"{item_name} ({level}){part_and_attributes}"
    
    def format_string(s):
        # Add a comma after the first "="
        s = re.sub(r'^(.*?)=', r'\1=,', s)
        # Replace multiple consecutive commas with a single one
        s = re.sub(r',+', ',', s)
        return s
    
    
    
    raw_combinations = []

    for r in range(1, len(chossen_items) + 1):
        raw_combinations.extend(itertools.combinations(chossen_items.items(), r))

# filter out combinations with duplicate parts
    combinations = []
    item_strings_lists = []
    for combo in raw_combinations:
        parts = [item[1]['attributes']['part'] for item in combo]
        if len(parts) == len(set(parts)):  # check if all parts are unique
            combinations.append({k: v for k, v in combo})
            item_strings_lists.append([format_item(item) for item in combo])
            
            

# print total number of combinations
    print(f'The total number of combinations is: {len(combinations)}')
    
    # Apply the format_string function to each item in item_strings
    formatted_item_strings_lists = [[format_string(s) for s in item_strings_list] for item_strings_list in item_strings_lists]
    
       #到这一步获取了所有的组合，接下来就是计算组合的DPS
    
    
    for item_strings_list in formatted_item_strings_lists:
        for item_string in item_strings_list:
            print(item_string)
    
    
    with open(simc_config, 'r') as file:
        text = file.read()

    
    # 检查原始文本中是否包含"### Gear from Bags"
    if "### Gear from Bags" not in text:
        raise ValueError('原始文本中没有找到"### Gear from Bags"')

    # 将原始文本分割为两部分
    pre_gear_text, post_gear_text = text.split("### Gear from Bags", 1)


    def split_data(data):
        split_data = []
        for combo in data:
            split_combo = []
            for item_string in combo:
                item_parts = item_string.split(')', 1)  # 在右括号处分割字符串
                item_parts[0] = item_parts[0] + ')'  # 将括号添加回第一部分的末尾
                split_combo.append(item_parts)
            split_data.append(split_combo)
        return split_data

    new_gear_set = split_data(formatted_item_strings_lists)
    print('下面👇这个是可用的list')
    print(new_gear_set)
    
    
    match_items = [
        'head=',
        'neck=',
        'back=',
        'chest=',
        'wrist=',
        'hands=',
        'waist=',
        'legs=',
        'feet=',
        'finger1=',
        'trinket1=',
        'main_hand=',
        'off_hand=',    
    ]      


    for i, gear_combination in enumerate(new_gear_set):
        new_str = pre_gear_text  # 创建一个新的字符串用于替换
        for gear in gear_combination:
            gear_name = gear[0]
            gear_properties = gear[1]
            for match_item in match_items:
                if gear_properties.startswith(match_item):  # 如果该装备的属性字符串的开头有匹配的字符串
                    lines = new_str.split('\n')
                    for j in range(len(lines)):  # 修改内部的遍历索引为j
                        if lines[j].startswith(match_item):
                            old_item_name = lines[j-1]  # 找到装备的名字
                            old_item = lines[j]  # 找到对应的部位的文字
                            new_str = new_str.replace(old_item_name + '\n' + old_item, gear_name + '\n' + gear_properties)  # 替换掉原始字符串中对应部位的文字，包括装备名称和属性
                            break
        # 保存到新文件
        new_config = new_str + post_gear_text  # 将新字符串与原始字符串的后半部分拼接起来
        with open(os.path.join(output_file_path, f'new_file_{i}.txt'), 'w') as f:
            f.write(new_config)


    
    
    
    
    #这里开始跑simc
    #先跑原始参数：


    config_output = await simc.get_simc_output(simc_config,author_id)  #自身的数据

    # 定义提取文本的函数
    def extract_text(input_string):
        if not isinstance(input_string, (str, bytes)):
            print(f"Error: (程序会继续运行)input_string is not a string or bytes-like object, it's a {type(input_string)}")
            return None
        pattern = r'Player(.*?)DPS-Error'
        match = re.search(pattern, input_string, re.DOTALL)
        if match:
            extracted_text = match.group(1).strip()   
            # If a match is found
            # Regular expression pattern to match the name and DPS
            pattern = r": (\S+).*\n\s*DPS=(\S+)"
            match = re.search(pattern, extracted_text)
            if match:
                # Extract the name and DPS
                name = match.group(1)
                dps = float(match.group(2))

                print(f"Name: {name}, DPS: {dps}")
                return name + ' ' + str(dps)
            else:
                print("No match found")
            
        else:
            return None

    # 调用两个函数获取提取的结果
    config_output_text = extract_text(config_output)
    config_output_text = str(config_output_text) 
    config_output_text = config_output_text + ' 原始配置'
    print(config_output_text)
    
    output_content_list = []
    output_content_list.append(config_output_text)
    
    #开始处理其他配置
    def process_file(file_path):
        with open(file_path, 'r',encoding='utf-8') as file:
            file_contents = file.read()
        # Execute your operations on the file contents here
        # In this example, we just return the file contents
        return file_contents
    
    
    def find_differences(string1, string2):
        # Convert the strings to sets of characters
        set1 = set(string1)
        set2 = set(string2)

        # Find the differences between the two sets
        differences = set1 - set2  # or set1.difference(set2)

        return differences



    async def process_all_files_in_directory(directory_path):
        # Use os.listdir() to get all files in the directory
        for i, filename in enumerate(os.listdir(directory_path), start=1):
            # Construct the full file path
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r',encoding='utf-8') as file:
                    file_contents = file.read()
                if await simc.get_simc_output(file_path,author_id):
                    file_output = await simc.get_simc_output(file_path,author_id)
                    # Pass the file contents to functionA and get string_b
                    file_output_text = extract_text(file_output)
                    if file_output_text:
                        nunber = re.search(r'\d+', filename).group()
                        gear_name_string = ""
                        print('列表的长度： ',len(new_gear_set))
                        for gearN in new_gear_set[int(nunber)]:
                            gear_name = gearN[0].replace(' ','')
                            gear_parts = gearN[1].split('=')[0]

                            gear_name_string = gear_name_string + ' ' + gear_name + '-'+ gear_parts + ' '
                        print(nunber)
                        print(gear_name_string)
                        print(gear_parts)
                        print('-------------------------------------------------')
                        file_output_text = str(file_output_text) +  ' gear' + nunber + gear_name_string# Append to file_output_text
                        output_content_list.append(file_output_text)
                        #print(file_output_text)
                 
        for filename_remove in os.listdir(directory_path):
            file_path_remove = os.path.join(directory_path, filename_remove)
            # 判断路径是否为文件
            if os.path.isfile(file_path_remove):
                # 删除文件
                os.remove(file_path_remove)
                print(f"已删除文件: {file_path_remove}")
                
        
        with open('/home/liuxl/下载/output_content_list.json', "w", encoding="utf-8") as file:
            file.write(str(output_content_list))
        return output_content_list
        
    await process_all_files_in_directory(output_file_path)
    
    
    output_content_list.sort(key=lambda x: float(x.split()[1]), reverse=True)
    print(output_content_list)
    #print(output_content_list_sorted)
    '''
    with open('/home/liuxl/下载/output_content_list_sorted.json', "w", encoding="utf-8") as file:
        file.write(output_content_list_sorted)
'''

    return output_content_list



