'''
cron: 12 9 */7 * *
new Env('进京证续期');
环境变量：export JJZ_data=['姓名|身份证号|车牌号|authorization|source']
'''
import os
import json
import time
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
            user_name, user_id, vehicle, auth, source = account.split('|')
            self.accounts.append({"user_name": user_name, "user_id": user_id, "vehicle": vehicle, "auth": auth, "source": source})

    def request(self, url, payload, account):
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.8",
            "User-Agent": "okhttp-okgo/jeasonlzy",
            "source": account["source"],
            "authorization": account["auth"],
            "Content-Type": "application/json;charset=utf-8",
            "Host": "jjz.jtgl.beijing.gov.cn",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        res = requests.request("POST", url, headers=headers, data=payload)
        return res.json()

    def getRemainingTime(self, account):
        data = {"v": "3.4.0", "sfzmhm": account["user_id"], "s-source": "bjjj-android", "timestamp": int(round(datetime.datetime.now().timestamp() * 1000))}
        state_url = "https://jjz.jtgl.beijing.gov.cn/pro/applyRecordController/stateList"
        state_result = self.request(state_url, payload=data, account=account)
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
            if '正在审核' in msg:
                time.sleep(1200)
                current_state, _, _, _ = self.getRemainingTime(account)
                result_list.append(f"续签进京证信息成功：\n[{current_state}]")
        else:
            result_list.append(f"续签进京证信息失败：\n[{msg}]")

    def main(self):
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
            elif current_state == "审核通过(待生效)":
                result_list.append("查询进京证状态信息：\n审核通过(待生效),无需重新申请")
            else:
                hour = int(datetime.datetime.now().strftime("%H"))
                if hour > 11:
                    issuedate = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    issuedate = datetime.datetime.now().strftime("%Y-%m-%d")
                result_list.append(f"新进京证开始时间为：\n[{issuedate}]")
                self.renewTrafficPermit(account, hpzl, vid, issuedate)


if __name__ == "__main__":
    result_list = []
    autoRenew = AutoRenewTrafficPermit()
    autoRenew.main()
    sendMsg()
