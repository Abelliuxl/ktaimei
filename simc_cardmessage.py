import json
from typing import Dict
from khl.card import CardMessage, Card, Module, Element, Types

async def generate_simc_card_message_process(file_path: str, author_id: str) -> CardMessage:
    def create_card_message(data: Dict[str, Dict[str, str]]) -> CardMessage:
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
            equip_level = equip_data['level']
            equip_attributes = equip_data['attributes']
            equip_part = equip_attributes.get('part')  # 使用get方法获取部位属性，避免出现KeyError异常
            equip_part_chinese = part_mapping.get(equip_part, equip_part)
            if not equip_part_chinese:
                raise ValueError(f"装备 {equip_name} 的部位属性 {equip_part} 无效")  # 抛出错误报告
            equip_section = Module.Section(
                f'{equip_part_chinese} + {equip_name} + 装等: {equip_level}',
                Element.Button('参与模拟', equip_name, Types.Click.RETURN_VAL)
            )
            card.append(equip_section)
        card.append(Module.Divider())
        card.append(
            Module.ActionGroup(
                Element.Button('开始', 'start', Types.Click.RETURN_VAL,theme='primary'),
                Element.Button('取消', 'cancel', Types.Click.RETURN_VAL,theme='danger')
            )
        )

        return CardMessage(card)

    with open(file_path, 'r') as file:
        json_data = json.load(file)
    simc_card_message = create_card_message(json_data)
    return simc_card_message

async def generate_simc_card_message(file_path: str, author_id: str):
    return await generate_simc_card_message_process(file_path, author_id)