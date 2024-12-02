'''
cron: 1 * * * *
new Env('进京证续期');
环境变量：export JJZ_data=['姓名|身份证号|车牌号|authorization|UA']
'''
import os
import json
import time
import random
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
        accounts = os.getenv("JJZ_data")
        if accounts is None:
            print(f'你没有填入JJZ_data，咋运行？')
            exit()
        try:
            accounts = json.loads(accounts.replace("'", '"'))
        except Exception as e:
            print(f'{e}\n{accounts}\n请检查你的JJZ_data参数是否填写正确！')
            exit()
        result_list.append(f"获取到[{len(accounts)}]个进京证信息")
        self.accounts = []
        for account in accounts:
            user_name, user_id, vehicle, auth, UA = account.split('|')
            self.accounts.append({"user_name": user_name, "user_id": user_id, "vehicle": vehicle, "auth": auth, "UA": UA})

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
        res = requests.request("POST", url, headers=headers, data=payload)
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
            "hphm": account["vehicle"],
            "hpzl": hpzl,
            "vId": vid,
            "jjdq": "顺义区",
            "jjlk": "00606",
            "jjlkmc": "其他道路",
            "jjmd": "06",
            "jjmdmc": "其它",
            "jjrq": issuedate,
            "jjzzl": "02",
            "jsrxm": account["user_name"],
            "jszh": account["user_id"],
            "sfzmhm": account["user_id"],
            "xxdz": "胜利小区",
            "sqdzbdjd": 116.660824,
            "sqdzbdwd": 40.142141
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

    def ql_login(self):
        path = '/ql/data/config/auth.json'
        if os.path.isfile(path):
            with open(path, "r") as file:
                auth = file.read()
                file.close()
            auth = json.loads(auth)
            token = auth["token"]
            url = 'http://127.0.0.1:5700/api/user'
            headers = {'Authorization': f'Bearer {token}'}
            res = requests.get(url=url, headers=headers)
            if res.status_code == 200:
                return token
            else:
                return False
        else:
            print("没有发现auth文件, 你这是青龙吗???")
            exit()

    def ql_api(self, method, api, body=None):
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        url = 'http://127.0.0.1:5700/' + api
        if type(body) == dict:
            res = self.ql_session.request(method, url=url, headers=headers, json=body).json()
        else:
            res = self.ql_session.request(method, url=url, headers=headers, data=body).json()
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
        return res['data']['data']

    def ql_update(self, id, command, schedule):
        api = 'api/crons'
        body = {'id': id, 'command': command, 'schedule': schedule}
        self.ql_api("PUT", api, body)

    def main(self):
        self.ql_session = requests.session()
        self.token = self.ql_login()
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
            else:
                issuedate = datetime.datetime.now().strftime("%Y-%m-%d")
                result_list.append(f"新进京证开始时间为：\n[{issuedate}]")
                self.renewTrafficPermit(account, hpzl, vid, issuedate)


if __name__ == "__main__":
    result_list = []
    autoRenew = AutoRenewTrafficPermit()
    autoRenew.main()
    sendMsg()
