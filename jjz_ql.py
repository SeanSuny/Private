'''
cron: 1 * * * *
new Env('进京证续期');
环境变量：export JJZ_data = "姓名|身份证号|车牌号|authorization|UA&姓名|身份证号|车牌号|authorization|UA"
'''
import os
import re
import json
import time
import random
import sqlite3
import requests
import datetime

## QYWX_AM="企业ID,Secret,userid1|userid2|userid3|xxx,AgentId,media_id"
#os.environ["QYWX_AM"] = ""

def sendMsg():
    try:
        from notify import send
        send("进京证续期通知", '\n'.join(result_list))
    except Exception as e:
        if e:
            print('发送通知消息失败！')


class AutoRenewTrafficPermit(object):

    def __init__(self):
        self.session = requests.session()
        if "JJZ_data" not in os.environ:
            print(f'你没有填入JJZ_data，咋运行？')
            exit()
        try:
            accounts = re.split('\n|&', os.environ.get('JJZ_data'))
        except Exception as e:
            print(f'{e}\n{accounts}\n请检查你的JJZ_data参数是否填写正确！')
            exit()
        result_list.append(f"获取到[{len(accounts)}]个进京证信息")
        self.accounts = []
        for account in accounts:
            try:
                user_name, user_id, vehicle, auth, UA = account.split('|')
                self.accounts.append({
                    "user_name": user_name,
                    "user_id": user_id,
                    "vehicle": vehicle,
                    "auth": auth,
                    "UA": UA
                })
            except ValueError:
                print(f"{account}\n请检查你的JJZ_data参数是否填写正确！")
                continue

    def request(self, url, account, payload=None):
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": account["UA"],
            "authorization": account["auth"],
            "Content-Type": "application/json",
            "Host": "jjz.jtgl.beijing.gov.cn:2443",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br"
        }
        res = self.session.request("POST", url, headers=headers, data=payload)
        return res.json()

    def getRemainingTime(self, account):
        state_url = "https://jjz.jtgl.beijing.gov.cn/pro/applyRecordController/stateList"
        state_result = self.request(state_url, account=account)
        state = state_result["data"]["bzclxx"]
        code = state_result["code"]
        msg = state_result["msg"]
        if code != 200:
            result_list.append(f"查询进京证信息失败：\n[{msg}]")
            return 0
        for index, state in enumerate(state):
            if state["ecbzxx"]:
                current_state = state["ecbzxx"][0]["blztmc"]
                validity_period = state["ecbzxx"][0]["yxqz"]
            else:
                current_state = state["bzxx"][0]["blztmc"]
                validity_period = state["bzxx"][0]["yxqz"]
            hpzl = state["hpzl"]
            vid = state["vId"]
            return current_state, validity_period, hpzl, vid

    def renewTrafficPermit(self, account, hpzl, vid, issuedate):
        data = {
            "vId": vid,
            "hphm": account["vehicle"],
            "hpzl": hpzl,
            "ylzsfkb": True,
            "elzsfkb": True,
            "elzqyms": "市界到六环 (含六环路、不含通州全域) 客车全年不限办理次数，每次限通行7天",
            "ylzqyms": "市界到二环 (不含二环路) 客车全年可办理12次，每次限通行7天",
            "elzmc": "进京证(六环外)",
            "ylzmc": "进京证(六环内)",
            "cllx": "01",
            "jjzzl": "02",
            "jsrxm": account["user_name"],
            "jszh": account["user_id"],
            "dabh": "",
            "txrxx": [],
            "jjrq": issuedate,
            "area": "顺义区",
            "jjdq": "010",
            "xxdz": "胜利小区",
            "jjdzgdwd": "",
            "jjdzgdjd": "",
            "jingState": "",
            "jjmd": "06",
            "jjmdmc": "其它",
            "sqdzgdjd": "116.4",
            "sqdzgdwd": "39.9",
            "sfzj": "1",
            "zjxxdz": "胜利小区",
            "zjxxdzgdjd": "116.654043",
            "zjxxdzgdwd": "40.135775",
            "jjlk": "",
            "jjlkmc": "",
            "jjlkgdjd": "",
            "jjlkgdwd": ""
        }
        url = "https://jjz.jtgl.beijing.gov.cn/pro/applyRecordController/insertApplyRecord"
        result = self.request(url, payload=json.dumps(data), account=account)
        code = result["code"]
        msg = result["msg"]
        if code == 200:
            if '正在审核' in msg or '审核中' in msg:
                time.sleep(600)
                current_state, validity_period, _, _ = self.getRemainingTime(account)
                if current_state == "审核通过(生效中)" or current_state == "审核通过(待生效)" :
                    result_list.append(f"续签进京证信息成功：\n[{current_state}]")
                    crondate = datetime.datetime.strptime(validity_period, '%Y-%m-%d')
                    schedule = f'{random.randint(1,59)} {random.randint(7,11)} {crondate.day} {crondate.month} *'
                    schedules = schedule.split(" ")
                    id, command = self.serch_cron("进京证续期")
                    self.ql_update(id, command, schedule)
                    result_list.append('*' * 35)
                    result_list.append(f"脚本下次运行时间为：\n[{crondate.year}-{schedules[3]}-{schedules[2]} {schedules[1]}:{schedules[0]}]")
                else:
                     result_list.append(f"续签进京证信息失败：\n[{current_state}]")
        else:
            result_list.append(f"续签进京证信息失败：\n[{msg}]")

    def ql_token(self):
        token_files = [
            '/ql/data/db/keyv.sqlite',
            '/ql/data/config/auth.json',
            '/ql/config/auth.json'
        ]
        
        valid_files = [f for f in token_files if os.path.exists(f)]
        if not valid_files:
            print("没有发现认证信息文件, 你这是青龙吗???")
            exit()
        latest_file = max(valid_files, key=os.path.getmtime)
        if latest_file.endswith('.sqlite'):
                conn = sqlite3.connect(f'file:{latest_file}?mode=ro', uri=True, timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM keyv WHERE key='keyv:authInfo' LIMIT 1")
                row = cursor.fetchone()
                conn.close()

                if row and row[0]:
                    auth_info = json.loads(row[0])
                    token = auth_info.get("value", {}).get("token")
                    if token:
                        return token
                print(f"❌ 数据库 {latest_file} 中未找到 token！！！")
        else:
            with open(latest_file, 'r', encoding='utf-8') as f:
                auth_info = json.load(f)
                token = auth_info.get("token")
                if token:
                    return token
                else:
                    print(f"在文件 {latest_file} 中未找到 token！！！")
        exit()
    
    def ql_api(self, method, api, body=None):
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        url = f'http://127.0.0.1:5700/{api}'
        if type(body) == dict:
            res = self.session.request(method, url=url, headers=headers, json=body).json()
        else:
            res = self.session.request(method, url=url, headers=headers, data=body).json()
        return res

    def serch_cron(self, name):
        for i in range(len(self.cronlist)):
            if name == self.cronlist[i]['name']:
                command = self.cronlist[i]['command']
                id = self.cronlist[i]["id"]
                return id, command
            else:
                continue
        print("你没有[进京证续期]这个定时任务！")
        exit()

    def get_cron(self):
        api = 'api/crons'
        res = self.ql_api("GET", api)
        if res['code'] == 401:
            print("青龙Token失效！")
            exit()
        else:
            return res['data']['data']

    def ql_update(self, id, command, schedule):
        api = 'api/crons'
        body = {'id': id, 'command': command, 'schedule': schedule}
        self.ql_api("PUT", api, body)

    def main(self):
        self.token = self.ql_token()
        self.cronlist = self.get_cron()
        return_serch = self.serch_cron("进京证续期")
        for account in self.accounts:
            result_list.append('*' * 35)
            result_list.append(f"开始处理进京证信息：\n车主[{account['user_name']}]，车牌号<{account['vehicle']}>")
            current_state, validity_period, hpzl, vid = self.getRemainingTime(account)
            if current_state == "审核通过(生效中)":
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                if validity_period == today:
                    issuedate = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                    result_list.append(f"新进京证开始时间为：\n[{issuedate}]")
                    self.renewTrafficPermit(account, hpzl, vid, issuedate)
                else:
                    result_list.append(f"查询进京证到期时间：\n进京证将于[{validity_period}]过期，无需续签！")
                    crondate = datetime.datetime.strptime(validity_period, '%Y-%m-%d')
                    schedule = f'{random.randint(1,59)} {random.randint(7,11)} {crondate.day} {crondate.month} *'
                    schedules = schedule.split(" ")
                    id, command = return_serch
                    self.ql_update(id, command, schedule)
                    result_list.append('*' * 35)
                    result_list.append(f"脚本下次运行时间为：\n[{crondate.year}-{schedules[3]}-{schedules[2]} {schedules[1]}:{schedules[0]}]")
            elif current_state == "审核通过(待生效)":
                result_list.append(f"查询进京证状态信息：\n[{current_state},无需重新申请]")
                crondate = datetime.datetime.strptime(validity_period, '%Y-%m-%d')
                schedule = f'{random.randint(1,59)} {random.randint(7,11)} {crondate.day} {crondate.month} *'
                schedules = schedule.split(" ")
                id, command = return_serch
                self.ql_update(id, command, schedule)
                result_list.append('*' * 35)
                result_list.append(f"脚本下次运行时间为：\n[{crondate.year}-{schedules[3]}-{schedules[2]} {schedules[1]}:{schedules[0]}]")
            else:
                issuedate = datetime.datetime.now().strftime("%Y-%m-%d")
                result_list.append(f"新进京证开始时间为：\n[{issuedate}]")
                self.renewTrafficPermit(account, hpzl, vid, issuedate)


if __name__ == "__main__":
    result_list = []
    autoRenew = AutoRenewTrafficPermit()
    autoRenew.main()
    sendMsg()
    
