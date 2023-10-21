import aiohttp
import json

async def fetch_talent_loadouts(spec_simple):
    # 读取raider_name.json文件
    with open('/home/liuxl/ktaimei/config/Abbreviations.json') as f:
        raider_names = json.load(f)

    # 查询目标职业和专精
    target_class = None
    target_spec = None

    # 遍历raider_names字典，查找匹配的职业和专精
    for class_name, specs in raider_names.items():
        for spec, aliases in specs.items():
            if spec_simple.lower() in [alias.lower() for alias in aliases]:
                target_class = class_name
                target_spec = spec
                break
        if target_class is not None and target_spec is not None:
            break

    if target_class is None or target_spec is None:
        return None
    
    print(target_class,target_spec)

    # 读取player_info.json文件
    with open('/home/liuxl/raider_data/player_info.json') as f:
        player_info = json.load(f)

    # 存储提取的结果
    result_list = []

    # 遍历每个角色信息
    for info in player_info:
        if info.get("class") == target_class and info.get("spec") == target_spec:
            region = info.get("region")
            realm = info.get("realm")
            name = info.get("name")

            # 构建API请求
            url = 'https://raider.io/api/v1/characters/profile'
            print(region,realm,name)
            params = {
                'region': region,
                'realm': realm,
                'name': name,
                'fields': 'talents'
            }

            async with aiohttp.ClientSession() as session:
                # 发送异步API请求
                async with session.get(url, params=params) as response:
                    # 检查API响应状态码
                    if response.status == 200:
                        # 解析API响应的JSON数据
                        result = await response.json()

                        # 提取所需字段
                        talent_loadout = result.get("talentLoadout", {})
                        loadout_text = talent_loadout.get("loadout_text", "")

                        extracted_result = {
                            "name": result.get("name"),
                            "race": result.get("race"),
                            "faction": result.get("faction"),
                            "region": region,
                            "realm": realm,
                            "loadout_text": loadout_text
                        }

                        # 添加到结果列表
                        result_list.append(extracted_result)
                    else:
                        print(f"角色 {name} 的API请求失败")

    # 读取en_cn_wow.json文件
    with open('/home/liuxl/ktaimei/config/en_cn_wow.json', 'r', encoding='utf-8') as f:
        translation_data = json.load(f)

    # 定义一个函数，用于将英文文本转换为中文
    def translate_text(text):
        return translation_data.get(text.lower(), text)

    # 将结果整理为字符串格式
    result_string = "## raider.io上 {} {} 的天赋如下：\n\n".format(translate_text(target_spec), translate_text(target_class))

    for index, result in enumerate(result_list, start=1):
        result_string += "{}. **角色名**：{}，**种族**：{}，**阵营**：{}，**地区**：{}\n".format(index, translate_text(result["name"]), translate_text(result["race"]), translate_text(result["faction"]), result["region"])
        result_string += "**天赋代码**：{}\n\n".format(result["loadout_text"])
    
    # 在最后增加一条：详细数据访问url
    detailed_url = f"https://raider.io/mythic-plus-spec-rankings/season-df-2/world/{target_class}/{target_spec}"
    result_string += "详细数据访问Raider.io官网：{}\n".format(detailed_url)
    
    return result_string