"""
cron: 15 1,9,17 * * *
new Env('同步COOKIE到HW');
环境变量添加 hw_host hw_token exclude_pt_pin(排除已禁用和指定pt_pin不同步)
"""

import requests
import json
import sys
import os
import re


class Sync():

    # Hw面板地址、Token
    def __init__(self):
        if "hw_host" in os.environ and "hw_token" in os.environ:
            self.hw_host = os.environ['hw_host']
            self.hw_token = os.environ['hw_token']
            self.exclude_pt_pin = os.environ['exclude_pt_pin'].split(',')
        else:
            print("环境变量未添加或填写不全！！！")
            sys.exit(0)
        self.ql_token = self.get_token()


    # 青龙Token
    def get_token(self):
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
            return match.group(1)
        else:
            print(f"在文件 {latest_file} 中未找到 token！！！")
            exit()


    # 获取所有的变量
    def get_all_ck(self):
        url = "http://127.0.0.1:5700/api/envs"
        headers = {"Content-Type": "application/json", 'Authorization': f'Bearer {self.ql_token}'}
        try:
            response = requests.get(url, headers=headers).json()
            if (response['code'] == 200):
                print("获取青龙面板所有的Cookie")
                cklist = response["data"]
                ptPin_list = []
                ptKey_list = []
                remarks_list = []
                for i in cklist:
                    if "pt_pin" in i["value"] and i["status"] == 0 and not any(exclude in i["value"] for exclude in (self.exclude_pt_pin or [])) :
                        ptPin_list.append(re.findall('pt_pin=(.+?);', i["value"])[0])
                        ptKey_list.append(re.findall('pt_key=(.+?);', i["value"])[0])
                        remarks_list.append(i["remarks"])
                    else:
                        print(f"获取环境变量失败：没有JD的Cookie")
                return ptPin_list, ptKey_list, remarks_list
            else:
                print(f"获取环境变量失败：{response['message']}")
        except Exception as e:
            print(f"获取环境变量失败：{str(e)}")

    # 添加和更新变量
    def update_ck(self, ptPin, ptKey, remarks):
        url = f"{self.hw_host}/openApi/addOrUpdateAccount"
        payload = json.dumps({"ptPin": ptPin, "ptKey": ptKey, "remarks": remarks})
        headers = {'Content-Type': 'application/json', 'api-token': f'{self.hw_token}'}
        try:
            print("添加和更新变量")
            response = requests.post(url, headers=headers, data=payload).json()
            if (response['code'] == 1):
                print(f"添加和更新环境变量成功！！!\n现存服务器:Cookie {response['data']['cookieCount']} 个，Wskey {response['data']['accountCount']} 个")
                return True
            else:
                print(f"添加和更新环境变量失败：{response['msg']}")
                return False
        except Exception as e:
            print(f"添加和更新环境变量失败：{str(e)}")
            return False

    # 对ck进行添加和更新
    def match_ck(self):
        ptPin, ptKey, remarks = self.get_all_ck()
        cookie = dict(zip(ptPin, zip(ptKey, remarks)))
        for key, value in cookie.items():
            print("-------------------")
            print(f"开始添加和更新 {key} 的ck")
            self.update_ck(key, value[0], value[1])


if __name__ == '__main__':
    Sync().match_ck()
