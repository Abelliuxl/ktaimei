我的报错:
```
Traceback (most recent call last):
  File "/home/liuxl/.local/lib/python3.10/site-packages/khl/client.py", line 112, in safe_handler
    await handler(msg)
  File "/home/liuxl/.local/lib/python3.10/site-packages/khl/bot/bot.py", line 142, in handler
    await event_handler(self, event)
  File "/home/liuxl/ktaimei/bot.py", line 259, in update_simc_card
    output = await simc_gear_compare(simc_config, simc_json,author_id)
  File "/home/liuxl/ktaimei/simc_gear_compare.py", line 231, in simc_gear_compare
    await process_all_files_in_directory(output_file_path)
  File "/home/liuxl/ktaimei/simc_gear_compare.py", line 228, in process_all_files_in_directory
    file_output_text = file_output_text + differences  # Append to file_output_text
TypeError: can only concatenate tuple (not "str") to tuple
```

我的完整代码：
```
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
                return name,dps
            else:
                print("No match found")
            
        else:
            return None

    # 调用两个函数获取提取的结果
    config_output_text = extract_text(config_output)
    print(config_output)
    
    output_content_list = []
    output_content_list.append(config_output_text)
    
    #开始处理其他配置
    def process_file(file_path):
        with open(file_path, 'r') as file:
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
                with open(file_path, 'r') as file:
                    file_contents = file.read()
                if await simc.get_simc_output(file_path,author_id):
                    file_output = await simc.get_simc_output(file_path,author_id)
                    # Pass the file contents to functionA and get string_b
                    file_output_text = extract_text(file_output)
                    if file_output_text:
                        differences_set = find_differences(file_contents, simc_config)
                        if isinstance(differences_set, (str, bytes)):
                            differences = ','.join(differences_set)
                            print(f"Error: (程序会继续运行)input_string is not a string or bytes-like object, it's a {type(differences)}")
                            return None
                        differences = ','.join(differences_set)
                        file_output_text = file_output_text + differences  # Append to file_output_text
                        output_content_list.append(file_output_text)
    
    await process_all_files_in_directory(output_file_path)
```