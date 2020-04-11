import sys

import sql
import requests
import json
import time
from selenium.webdriver import Chrome, ChromeOptions
import re


def get_tencent_data():
    """

    :return: 返回历史数据和当日详细数据
    """
    tencent_news_other = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_other"
    tencent_news_h5 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/80.0.3987.163 Safari/537.36 "
    }

    other_r = requests.get(tencent_news_other, headers=headers)
    other_res = json.loads(other_r.text)
    data_all = json.loads(other_res['data'])

    h5_r = requests.get(tencent_news_h5, headers=headers)
    h5_res = json.loads(h5_r.text)
    data_all2 = json.loads(h5_res['data'])

    history = {}

    # 获取历史数据
    for i in data_all['chinaDayList']:
        ds = '2020.' + i['date']
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)  # 改变日期格式，不然插入数据库会报错，数据库是datetime类型
        confirm = i['confirm']
        suspect = i['suspect']
        heal = i['heal']
        dead = i['dead']
        history[ds] = {
            "confirm": confirm,
            "suspect": suspect,
            "heal": heal,
            "dead": dead
        }

    # 获取当日最新数据
    for i in data_all['chinaDayAddList']:
        ds = '2020.' + i['date']
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)  # 改变日期格式，不然插入数据库会报错，数据库是datetime类型
        confirm = i['confirm']
        suspect = i['suspect']
        heal = i['heal']
        dead = i['dead']
        history[ds].update({
            "confirm_add": confirm,
            "suspect_add": suspect,
            "heal_add": heal,
            "dead_add": dead
        })

    detail = []  # 当日详细数据
    update_time = data_all2['lastUpdateTime']
    data_country = data_all2['areaTree']
    data_province = data_country[0]['children']

    for pro_infos in data_province:
        province = pro_infos['name']
        for city_infos in pro_infos['children']:
            city = city_infos['name']
            confirm = city_infos['total']['confirm']
            confirm_add = city_infos['today']['confirm']
            heal = city_infos['total']['heal']
            dead = city_infos['total']['dead']
            detail.append([update_time, province, city, confirm, confirm_add, heal, dead])

    return history, detail


def get_baidu_hot():
    option = ChromeOptions()
    option.add_argument("--headless")
    option.add_argument("--no-sandbox")
    browser = Chrome(options=option)
    browser.get("https://voice.baidu.com/act/virussearch/virussearch?from=osari_map&tab=0&infomore=1")

    but = browser.find_element_by_css_selector(
        '#ptab-0 > div > div.VirusHot_1-5-5_32AY4F.VirusHot_1-5-5_2RnRvg > section > div')
    but.click()  # 点击展开
    time.sleep(1)  # 等待1秒

    c = browser.find_elements_by_xpath('//*[@id="ptab-0"]/div/div[2]/section/a/div/span[2]')
    content = [i.text for i in c]
    browser.close()
    # print(content)
    return content


if __name__ == '__main__':
    l = len(sys.argv)
    if l == 1:
        s = """
        请输入参数
        参数说明：
        up_his  更新历史记录表
        up_hot  更新实时热搜
        up_det  更新详细表
        """
        print(s)
    else:
        order = sys.argv[1]
        if order == "up_his":
            sql.update_history(get_tencent_data())
        elif order == "up_det":
            sql.update_details(get_tencent_data())
        elif order == "up_hot":
            sql.update_hotsearch(get_baidu_hot())
    # sql.update_history(get_tencent_data())
    # sql.update_details(get_tencent_data())
    # sql.update_hotsearch(get_baidu_hot())