"""
cron: 15 2 * * *
new Env('备份青龙环境变量');
"""

import os
import re
import json
import requests
import datetime

class QL:
    def __init__(self): #初始化
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

    def getEnvs(self):  #获取全部环境变量
        url = 'http://127.0.0.1:5700/api/envs'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        try:
            rjson = requests.get(url, headers=headers).json()
            if (rjson['code'] == 200):
                return rjson['data']
            else:
                print(f"处理中>>>获取环境变量失败：{rjson['message']}")
                exit()
        except Exception as e:
            print(f"处理中>>>获取环境变量失败：{str(e)}")
            exit()

if __name__ == "__main__":
    ql = QL()
    print("开始处理>>>【备份】环境变量")
    envs = ql.getEnvs()
    file = open('/ql/data/config/backup/envs_' + datetime.datetime.now().strftime('%Y-%m-%d') + '.json', 'w', encoding='utf-8')
    file.write(json.dumps(envs, ensure_ascii=False, indent=4))
    file.close()
    print("处理完成>>>环境变量备份成功")
