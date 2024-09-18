"""
cron: 15 2 * * *
new Env('备份青龙环境变量');
"""

import os
import json
import requests
import datetime

class QL:
    def __init__(self): #初始化
        path = '/ql/data/config/auth.json'
        if not os.path.exists('/ql/data/config/backup'):
            os.makedirs('/ql/data/config/backup', exist_ok=True)
        if os.path.isfile(path):
            with open(path, "r") as file:
                auth = file.read()
                file.close()
            auth = json.loads(auth)
            self.token = auth["token"]
        else:
            print("没有发现auth文件, 你这是青龙吗???")
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
        except Exception as e:
            print(f"处理中>>>获取环境变量失败：{str(e)}")

if __name__ == "__main__":
    ql = QL()
    print("开始处理>>>【备份】环境变量")
    envs = ql.getEnvs()
    file = open('/ql/data/config/backup/envs_' + datetime.datetime.now().strftime('%Y-%m-%d') + '.json', 'w', encoding='utf-8')
    file.write(json.dumps(envs, ensure_ascii=False, indent=4))
    file.close()
    print("处理完成>>>环境变量备份成功")
