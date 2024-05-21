import json
import os

# 读取jsonl文件
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.readlines()
    return data


if __name__ == '__main__':

    #遍历文件夹下所有文件
    directory = r'E:\share\github\02yue\github_daily\data\github0506'
    for root, dirs, files in os.walk(directory):
        total_dict = {}
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

        # 字典写入jsonl文件
        with open(f'./data/order/total/total.jsonl', 'w', encoding='utf-8') as f:
            json.dump(total_dict, f, ensure_ascii=False, indent=4)

        # 字典写入json文件,中文不乱码
        with open(f'./data/order/total/total_order.json', 'w', encoding='utf-8') as f:
            for item in total_dict.values():
                f.write(str(item['stars']))
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')