# Ktaimei机器人

## 简介

这是一个基于Khl库开发的kook聊天机器人,具有以下主要功能:

1. 和用户进行自然语言交互,可以回答问题等
2. 提供魔兽世界游戏相关信息查询,如天赋点分配等
3. 进行魔兽世界角色装备组合DPS模拟
4. 对用户加入和退出语音频道进行检测,并作出反应
5. 查询jcr杂志影响因子
6. 全语言翻译

## 主要代码结构

1. 导入必要的库和模块
2. 加载配置文件config.json
3. 初始化Khl Bot对象
4. 定义OpenAI交互函数make_request()
5. 定义日志记录器
6. 定义针对不同指令的处理函数,如天赋查询/tf、DPS模拟/moni等
7. 定义根据事件触发的处理函数,如成员加入退出频道等
8. 在主函数中启动Bot

## 关键功能详解

1. 自然语言交互
   
   使用OpenAI GPT-3.5 API实现,在handle_text_msg函数中定义

2. 魔兽世界信息查询
   
   通过调用raider_talents模块实现天赋查询

3. DPS模拟

   使用simc模块,在simc_single函数中实现

4. 成员加入退出检测

   使用JOINED_CHANNEL和EXITED_CHANNEL事件实现

## 配置和运行

需要配置config.json,填入机器人token等关键信息
token需要自行在config文件夹内配置json文件

启动方式:

```
python bot.py 
```

## 参考资料

Khl库:https://khl.sh
OpenAI API:https://openai.com/api/
