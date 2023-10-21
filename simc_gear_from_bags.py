import re
import json
from collections import OrderedDict
import asyncio

async def process_gear_from_bags(input_file, author_id):
    output_file = f"/home/liuxl/ktaimei/config/simc_caches/{author_id}.json"
    gear_from_bags = {}

    with open(input_file, "r", encoding="utf-8") as file:
        input_string = file.read()

    pattern = r"### Gear from Bags\n(#[\s\S]*?)(?=\n\n|\n###)"
    match = re.search(pattern, input_string)

    if match:
        gear_from_bags_text = match.group(1)

        pattern_item = r"^\s*#\s*(.+?)\s+\((\d+)\)\s*\n(.+?)=(.*?)(?=\n#|\n###|\s*$)"
        matches_item = re.findall(pattern_item, gear_from_bags_text, flags=re.MULTILINE | re.DOTALL)

        for item_name, item_level, item_part, item_attributes_text in matches_item:
            item_level = int(item_level)

            item_attributes = OrderedDict()

            # 添加装备部位信息
            item_attributes["part"] = item_part.strip()

            # 添加id属性
            id_match = re.search(r"id=(\d+)", item_attributes_text)
            if id_match:
                item_attributes["id"] = int(id_match.group(1))

            # 特殊处理enchant_id
            enchant_id_match = re.search(r"enchant_id=(\d+)", item_attributes_text)
            if enchant_id_match:
                item_attributes["enchant_id"] = int(enchant_id_match.group(1))

            # 特殊处理gem_id
            gem_id_match = re.search(r"gem_id=(.*?(?=\s*\w+=|\s*$))", item_attributes_text)
            if gem_id_match:
                item_attributes["gem_id"] = gem_id_match.group(1).strip()

            # 特殊处理bonus_id
            bonus_id_match = re.search(r"bonus_id=(.*?(?=\s*\w+=|\s*$))", item_attributes_text)
            if bonus_id_match:
                item_attributes["bonus_id"] = bonus_id_match.group(1).strip()

            # 特殊处理crafted_stats
            crafted_stats_match = re.search(r"crafted_stats=(.*?(?=\s*\w+=|\s*$))", item_attributes_text)
            if crafted_stats_match:
                item_attributes["crafted_stats"] = crafted_stats_match.group(1).strip()

            # 特殊处理crafting_quality
            crafting_quality_match = re.search(r"crafting_quality=(.*?(?=\s*\w+=|\s*$))", item_attributes_text)
            if crafting_quality_match:
                item_attributes["crafting_quality"] = crafting_quality_match.group(1).strip()
                
            item_attributes['chossen']=False

            gear_from_bags[item_name] = {
                "level": item_level,
                "attributes": item_attributes
            }

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(gear_from_bags, file, indent=4, ensure_ascii=False)

    print(f"提取的物品已存储到 {output_file} 文件中。")

# 调用异步函数进行处理
async def gear_bag_saved(input_file, author_id): #作为一个函数能在其他py文件中被调用
    return await process_gear_from_bags(input_file, author_id)