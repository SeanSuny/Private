"""
cron: 5 1,9,17 * * *
new Env('检测JD_COOKIE');
"""

import requests
import random
import time
import json
import os
import re


class Check():

    # 青龙Token
    def __init__(self):
        token_files = [
            '/ql/data/db/keyv.sqlite',
            '/ql/data/config/auth.json',
            '/ql/config/auth.json'
        ]
        valid_files = [file_path for file_path in token_files if os.path.exists(file_path)]
        if not valid_files:
            print("没有发现认证信息文件, 你这是青龙吗???")
            exit()
        latest_file = max(valid_files, key=os.path.getmtime)
        with open(latest_file, 'rb') as f:
            auth_config = f.read().decode('utf-8', errors='ignore')
        match = re.search(r'"token":"([^"]*)"(?!.*"token":)', auth_config)
        if match:
            self.token = match.group(1)
        else:
            print(f"在文件 {latest_file} 中未找到 token！！！")
            exit()

    # 检测ck
    def check_ck(self, ck, pin):
        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
        headers = {
            'Cookie': ck,
            'Referer': 'https://home.m.jd.com/myJd/home.action',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; M2102K2C Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 Mobile Safari/537.36'
        }
        try:
            time.sleep(random.randint(1,5))
            res = requests.get(url=url, headers=headers, timeout=10, allow_redirects=False)
        except Exception as err:
            print("JD接口错误 请重试或者更换IP")
            exit()
        else:
            if res.status_code == 200:
                try:
                    code = int(json.loads(res.text)['retcode'])
                except Exception as err:
                    print("JD接口风控, 建议更换IP或增加间隔时间")
                    exit()
                if code == 0:
                    print(f"{str(pin)}的ck:\033[1;32m [✔] \033[0m")
                    return True
                else:
                    print(f"{str(pin)}的ck:\033[1;31m [×] \033[0m")
                    return False
            else:
                print(f"JD接口错误码: {str(res.status_code)}")
                exit()

    # 获取所有的变量
    def get_all_ck(self):
        url = "http://127.0.0.1:5700/api/envs"
        headers = {"Content-Type": "application/json", 'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get(url, headers=headers).json()
            if (response['code'] == 200):
                print("获取青龙面板所有的Cookie")
                cklist = response["data"]
                id_list = []
                ck_list = []
                status_list = []
                for i in cklist:
                    if "pt_pin" in i["value"]:
                        ck_list.append(i["value"])
                        id_list.append(i["id"])
                        status_list.append(i["status"])
                    else:
                        print(f"获取环境变量失败：没有JD的Cookie")
                return ck_list, id_list, status_list
            else:
                print(f"获取环境变量失败：{response['message']}")
        except Exception as e:
            print(f"获取环境变量失败：{str(e)}")

    # 禁用变量
    def disable_ck(self, id, pin):
        url = "http://127.0.0.1:5700/api/envs/disable"
        list = []
        list.append(id)
        payload = json.dumps(list)
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        try:
            print("-------------------")
            print(f"禁用{str(pin)}的青龙ID：{payload}")
            response = requests.put(url, headers=headers, data=payload).json()
            if (response['code'] == 200):
                print(f"禁用{str(pin)}的青龙ID：{payload} 成功")
            else:
                print(f"禁用{str(pin)}的青龙ID：{payload} 失败：{response['message']}")
        except Exception as e:
            print(f"禁用{str(pin)}的青龙ID：{payload} 失败：{str(e)}")

    # 对ck进行检测和禁用
    def match_ck(self):
        ck, id, status = self.get_all_ck()
        cookie = dict(zip(id, zip(ck, status)))
        for key, value in cookie.items():
            pt_pin = str(re.findall(r"pt_pin=(.+?);", value[0])[0])
            ck = value[0]
            id = key
            status = value[1]
            if status == 0:
                print("-------------------")
                print(f"开始检测 {pt_pin} 的ck")
                if not self.check_ck(ck, pt_pin):
                    self.disable_ck(id, pt_pin)


if __name__ == '__main__':
    Check().match_ck()
