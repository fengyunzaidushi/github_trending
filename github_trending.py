import os
import aiohttp
import discord
from datetime import datetime
import asyncio
import random
import hashlib
import re
import json
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.tmt.v20180321 import tmt_client, models
from bs4 import BeautifulSoup
import markdown
import requests
import base64
from dotenv import load_dotenv

load_dotenv()


async def fetch_readme_content(session, url):
    """
    异步获取 README 文件的内容。
    """
    async with session.get(url) as response:
        return await response.json()


async def get_first_paragraph_of_readme_async(git_repo_url):
    """
    异步获取指定 GitHub 仓库 README 的第一个段落。

    参数:
    git_repo_url (str): GitHub 仓库的 URL。

    返回:
    str: README 文件中的第一个段落文本。
    """
    # 从 URL 中提取用户名和仓库名
    parts = git_repo_url.split("/")
    username, repo_name = parts[-2], parts[-1]

    # 构造 GitHub API 请求 URL
    api_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"

    # 创建异步会话并发送请求
    async with aiohttp.ClientSession() as session:
        data = await fetch_readme_content(session, api_url)

    # 解码 README 内容（base64 编码）
    try:
        readme_content_encoded = data["content"]
        readme_content = base64.b64decode(readme_content_encoded).decode("utf-8")

        # 使用 markdown 库将 Markdown 转换为 HTML
        html_content = markdown.markdown(readme_content)

        # 使用 BeautifulSoup 解析 HTML，并获取第一个 <p> 元素的内容
        soup = BeautifulSoup(html_content, "html.parser")
        h1_tags = soup.find_all("h1")
        p_tags = soup.find_all("p")
        h1_tags.extend(p_tags)
        # 打印每个 <p> 标签的内容
        text = ""
        for tag in h1_tags:
            text += tag.get_text().strip()
            if text and repo_name.lower() in text.lower():
                break
        text = text.split(".")[0]
        return text
    except Exception as e:
        print(f"error is {e},git_repo_url is {git_repo_url}")
        return repo_name


def trs_batch_text(text_list, source_lang="en", target_lang="zh"):
    try:

        secret_id = os.environ.get("secret_id")
        secret_key = os.environ.get("secret_key")
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(secret_id, secret_key)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        # httpProfile = HttpProfile()
        # httpProfile.endpoint = "tmt.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        # clientProfile = ClientProfile()
        # clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = tmt_client.TmtClient(cred, "ap-shanghai")
        # client = tmt_client.TmtClient(cred, "ap-shanghai", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.TextTranslateBatchRequest()
        params = {
            "Source": source_lang,
            "Target": target_lang,
            "ProjectId": 0,
            "SourceTextList": text_list,
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个TextTranslateBatchResponse的实例，与请求对象对应
        resp = client.TextTranslateBatch(req)
        # 输出json格式的字符串回包
        return resp.TargetTextList

    except TencentCloudSDKException as err:
        print(err)


async def fetch_trending_repositories(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            # repos = soup.find_all('article', class_='Box-row')
            repos = soup.select("article.Box-row")
            data = []
            for repo in repos:
                # 提取仓库名和 URL
                name_tag = repo.select_one("h2.h3.lh-condensed a")
                name = name_tag.get_text(strip=True)
                repo_url = "https://github.com" + name_tag["href"]

                # 提取描述
                description_tag = repo.select_one("p.col-9.color-fg-muted.my-1.pr-4")
                description = (
                    description_tag.get_text(strip=True) if description_tag else ""
                )
                description = description.strip()
                if not description:
                    description = await get_first_paragraph_of_readme_async(repo_url)
                # 提取 Star 数和 Fork 数
                stars_tag = repo.select_one('a[href*="/stargazers"]')
                stars = stars_tag.get_text(strip=True) if stars_tag else ""

                forks_tag = repo.select_one('a[href*="/forks"]')
                forks = forks_tag.get_text(strip=True) if forks_tag else ""

                # 提取编程语言
                language_tag = repo.select_one('span[itemprop="programmingLanguage"]')
                language = language_tag.get_text(strip=True) if language_tag else ""

                # 提取今日 Star 数
                stars_today_tag = repo.select_one("span.d-inline-block.float-sm-right")
                stars_today = (
                    stars_today_tag.get_text(strip=True) if stars_today_tag else ""
                )

                data.append(
                    {
                        "name": name,
                        "url": repo_url,
                        "description": description if description else "no description",
                        "stars": stars,
                        "forks": forks,
                        "language": language,
                        "stars_today": stars_today,
                    }
                )

            # data 包含了所有提取的信息
        return data


def get_date():
    current_time = datetime.now()
    # 格式化时间为 "xx月xx日"
    formatted_time = current_time.strftime("%m月%d日")
    return formatted_time


def write_github_data(git_dict, date, prefix):
    key_order = [
        "zh_des",
        "url",
        "name",
        "description",
        "stars",
        "forks",
        "language",
        "stars_today",
    ]
    # 字典根据列表中列举的值进行排序
    for key, value in git_dict.items():
        sub_list = []
        for original_dict in value:
            ordered_dict = {k: original_dict[k] for k in key_order}
            # ordered_dict = OrderedDict((k, original_dict[k]) for k in key_order)
            sub_list.append(ordered_dict)
        git_dict[key] = sub_list
    os.makedirs(f"./data/github", exist_ok=True)
    # 字典写入json文件,中文不乱码
    with open(f"./data/github/{prefix}_datalist.json", "a+", encoding="utf-8") as f:
        for key in git_dict.keys():
            f.write(key + "\n")
        for item in git_dict.get(key):
            f.write("    ")
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")
        f.write("\n")
        # json文件插入一行空格

    # 字典写入json文件,中文不乱码
    with open(f"./data/github/{prefix}_data.jsonl", "a+", encoding="utf-8") as f:
        # for item in git_dict.values():
        #     json.dump(item, f, ensure_ascii=False)
        json.dump(git_dict, f, ensure_ascii=False, indent=4)
        # json文件插入一行空格
        f.write("\n")
    with open(f"./data/github/{prefix}_list.jsonl", "a+", encoding="utf-8") as f:
        json.dump(git_dict, f, ensure_ascii=False)
        f.write("\n")


# 由于 asyncio 的原因，您可能需要在异步环境下运行此函数
# 比如使用 `await fetch_trending_repositories()` 或者在异步函数中调用


def read_jsonl_to_dict(file_path):
    data = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            try:
                line_data = json.loads(line)
                data.update(line_data)
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_number}: {e}")
                print(f"Line content: {line}")
    return data


async def main():
    urls = [
        "https://github.com/trending?since=alldaily",
        "https://github.com/trending?since=weekly&s=allweekly",
        "https://github.com/trending?since=monthly&s=allmonthly",
    ]
    urls2 = [
        "https://github.com/trending/python?since=daily",
        "https://github.com/trending/python?since=weekly",
        "https://github.com/trending/python?since=monthly",
    ]
    urls3 = [
        "https://github.com/trending/typescript?since=daily&s=tsdaily",
        "https://github.com/trending/typescript?since=weekly&s=tsweekly",
        "https://github.com/trending/typescript?since=monthly&s=tsmonthly",
    ]
    urls4 = [
        "https://github.com/trending/javascript?since=daily&s=jsdaily",
        "https://github.com/trending/javascript?since=weekly&s=jsweekly",
        "https://github.com/trending/javascript?since=monthly&s=jsmonthly",
    ]
    urls5 = [
        "https://github.com/trending/jupyter-notebook?since=daily&s=jupyterdaily",
        "https://github.com/trending/jupyter-notebook?since=weekly&s=jupyterweekly",
        "https://github.com/trending/jupyter-notebook?since=monthly&s=jupytermonthly",
    ]
    urls6 = [
        "https://github.com/trending/vue?since=daily&s=vuedaily",
        "https://github.com/trending/vue?since=weekly&s=vueweekly",
        "https://github.com/trending/vue?since=monthly&s=vuemonthly",
    ]
    urls.extend(urls2)
    urls.extend(urls3)
    urls.extend(urls4)
    urls.extend(urls5)
    urls.extend(urls6)
    date = get_date()
    # 遍历列表和索引

    for idx, url in enumerate(urls):
        print(idx, url)
        separators = "/="
        split_text = re.split("[{}]".format(separators), url)
        prefix = split_text[-1]
        prefix = str(idx).zfill(2) + "_" + prefix
        if "jupyter-notebook" in url:
            continue

        try:
            repositories = await fetch_trending_repositories(url)
            if repositories:
                all_zh_des = trs_batch_text(
                    [
                        item.get("description", "do not translate")
                        for item in repositories[:]
                    ]
                )
                if all_zh_des:
                    print("all_zh_des is ok")
                    new_repositories = [
                        item.update({"zh_des": zh_des})
                        for item, zh_des in zip(repositories, all_zh_des)
                    ]
                    git_dict = {date: repositories}
                    write_github_data(git_dict, date, prefix)
        except Exception as e:
            print(e)
            pass


async def discord_callback(repositories, date, prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    token = os.environ["DISCORD_TOKEN"]
    # print(f'DISCORD_TOKEN is {token}')
    channel_id = int(os.environ["DISCORD_CHANNEL_ID"])
    async with client:
        await client.login(token)
        channel = await client.fetch_channel(channel_id)
        lines = []
        total_length = 0
        await channel.send(f"## {date}: {prefix} github")
        for idx, repo in enumerate(repositories):
            # print(f'idx {idx}')
            line = []
            line.append(f"## {idx+1}: {repo['name']} - {prefix}")
            line.append(f"    {repo['zh_des']}")
            line.append(f"    {repo['description']}")
            line.append(f"    {repo['url']}")
            line.append(f"    {repo['language']}")
            line.append(
                f"    Stars: {repo['stars']},Forks: {repo['forks']},Today's Stars: {repo['stars_today']}\n"
            )
            line_length = len("\n".join(line))
            total_length += line_length + 2
            # print(f'total lth {total_length}')
            if total_length > 2000:
                msg = "\n\n".join(lines)
                # print(f'msg lth {len(msg)}')
                await channel.send(msg[:2000])
                lines = []
                total_length = 0
                total_length += line_length
                lines.append("\n".join(line))

            else:
                lines.append("\n".join(line))

        if lines:
            await channel.send("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())
    # import fire
    # fire.Fire(main)
