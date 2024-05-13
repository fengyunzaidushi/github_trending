import json
import os

# 读取jsonl文件
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.readlines()
    return data


if __name__ == '__main__':

    #遍历文件夹下所有文件
    directory = '/mnt/sda/github/02yue/github_daily/data/github'
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_list.jsonl'):
                # 读取jsonl文件
                file_path = os.path.join(root, file)
                data = read_jsonl(file_path)
                print(len(data))
                # print(data[0])
                all_dic = {}
                for item in data[:]:
                    dic = json.loads(item)

                    for repo in list(dic.values())[0]:
                        # print(repo)
                        num = repo['stars'].replace(',', '')
                        # 三元表达式判断num是否为空
                        repo['stars'] = int(num) if num else 0
        
                        if repo['name'] not in all_dic:
                            all_dic[repo['name']] = repo
                        else:
                            if repo['stars'] > all_dic[repo['name']]['stars']:
                                all_dic[repo['name']] = repo
                
                # 字典根据键stars排序   
                all_dic = dict(sorted(all_dic.items(), key=lambda x: x[1]['stars'], reverse=True))

                # 字典写入jsonl文件
                with open(f'./data/order/jsonl/{file}.jsonl', 'w', encoding='utf-8') as f:
                    json.dump(all_dic, f, ensure_ascii=False, indent=4)

                # 字典写入json文件,中文不乱码
                with open(f'./data/order/merge/{file}_order.json', 'w', encoding='utf-8') as f:
                    for item in all_dic.values():
                        f.write('    ')
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
