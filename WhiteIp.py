# cron: 5 */3 * * *
# new Env('IP地址池白名单');

import time
import hashlib
import requests
from notify import send

result_list = []

def checkip():
    url = 'http://api.xiequ.cn/VAD/OnlyIp.aspx?yyy=123'
    response = requests.get(url).text
    return response


def md5String(str):
    if (len(str) > 0):
        md5 = hashlib.md5()
        md5.update(str.encode(encoding="utf-8"))
        return md5.hexdigest()
    else:
        return "N/A"


def xiequ():
    url = 'http://op.xiequ.cn/IpWhiteList.aspx?uid=126244&ukey=7C4B6F4BF696311B9AB961F253184A20&act=del&ip=all'
    response = requests.get(url)
    url = 'http://op.xiequ.cn/IpWhiteList.aspx?uid=126244&ukey=7C4B6F4BF696311B9AB961F253184A20&act=add&ip=' + checkip()
    response = requests.get(url).text
    if "success" in response:
        result_list.append(f"携趣：白名单更新成功！IP地址：" + checkip())
    else:
        result_list.append(f"携趣：白名单更新失败！")


def juliang():
    data = 'new_ip=' + checkip() + '&reset=1&trade_no=1260663963325477'
    sign = md5String(data + '&key=1ea276146ccb4149bf96f1cfcee1973a')
    url = 'http://v2.api.juliangip.com/dynamic/replaceWhiteIp?' + data + '&sign=' + sign
    response = requests.get(url).json()
    if response['msg'] == '请求成功':
        result_list.append(f"巨量：白名单更新成功！IP地址：" + checkip())
    else:
        result_list.append(f"巨量：白名单更新失败！")


if __name__ == '__main__':
    xiequ()
    time.sleep(5)
    # juliang()
    result_str = '\n'.join(result_list)
    send('IP地址池白名单', result_str)
