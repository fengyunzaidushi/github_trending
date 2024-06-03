import json
import os
import time
# 读取jsonl文件
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.readlines()
    return data


if __name__ == '__main__':

    #遍历文件夹下所有文件
    directory = r'E:\share\github\02yue\github_daily\data'
    total_dict = {}
    for root, dirs, files in os.walk(directory):
        
        if 'github' in root:
            print('root:', root)
            for file in files:
                if file.endswith('_list.jsonl'):
                    # 读取jsonl文件
                    file_path = os.path.join(root, file)
                    data = read_jsonl(file_path)
                    print(len(data))
                    # print(data[0])
                    file_dic = {}
                    for item in data[:]:
                        dic = json.loads(item)

                        for repo in list(dic.values())[0]:
                            # print(repo)
                            num = repo['stars'].replace(',', '')
                            # 三元表达式判断num是否为空
                            repo['stars'] = int(num) if num else 0
            
                            if repo['name'] not in file_dic:
                                file_dic[repo['name']] = repo
                                total_dict[repo['name']] = repo
                            else:
                                if repo['stars'] > file_dic[repo['name']]['stars']:
                                    file_dic[repo['name']] = repo
                                    total_dict[repo['name']] = repo
                    
                    # 字典根据键stars排序   
                    # file_dic = dict(sorted(file_dic.items(), key=lambda x: x[1]['stars'], reverse=True))

                    # 字典写入jsonl文件
                    # with open(f'./data/order/jsonl/{file}.jsonl', 'w', encoding='utf-8') as f:
                    #     json.dump(file_dic, f, ensure_ascii=False, indent=4)
                    #
                    # # 字典写入json文件,中文不乱码
                    # with open(f'./data/order/merge/{file}_order.json', 'w', encoding='utf-8') as f:
                    #     for item in file_dic.values():
                    #         f.write('    ')
                    #         json.dump(item, f, ensure_ascii=False)
                    #         f.write('\n')

    # 字典根据键stars排序
    total_dict = dict(sorted(total_dict.items(), key=lambda x: x[1]['stars'], reverse=True))
    print(len(total_dict))
    # 字典写入jsonl文件
    # with open(f'./data/order/total/total0603.jsonl', 'w', encoding='utf-8') as f:
    #     json.dump(total_dict, f, ensure_ascii=False, indent=4)

    # # 字典写入json文件,中文不乱码
    # with open(f'./data/order/total/total_order0603.json', 'w', encoding='utf-8') as f:
    #     for item in total_dict.values():
    #         f.write(str(item['stars']))
    #         json.dump(item, f, ensure_ascii=False)
    #         f.write('\n')
    

        # Classify content by language
    classified_data = {}
    for key, value in total_dict.items():
        language = value.get("language", "Unknown")
        if language not in classified_data:
            classified_data[language] = []
        classified_data[language].append(value)

    # Write content by language into separate JSONL files
    file_paths = {}
    # get time day
    time_day = time.strftime("%Y%m%d", time.localtime())
    for language, items in classified_data.items():
        num = str(len(items)).zfill(4)
        file_name = f"./data/order/classified/divide/{num}_{language if language else 'Unknown'}.jsonl"
        with open(file_name, "w", encoding="utf-8") as file:
            for item in items:
                json_line = json.dumps(item, ensure_ascii=False)
                file.write(json_line + "\n")
        file_paths[language] = file_name

        file_name2 = f"./data/order/classified/merge/{num}_{language if language else 'Unknown'}.jsonl"
        with open(file_name2, 'a+', encoding='utf-8') as f:
            sub_dict = {language: items}
            json.dump(sub_dict, f, ensure_ascii=False, indent=4)
            # json文件插入一行空格
            f.write('\n')