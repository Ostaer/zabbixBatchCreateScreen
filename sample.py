# -*- coding:utf-8 -*-
'''
Created on 2017/5/16
@author: banbanqiu
'''
from zabbix_request import ZabbixRequest
import ConfigParser

cfgFN = "sample.cfg"
required_ops = [("Base", "url"), ("Base", "username"), ("Base", "password")]
parser = ConfigParser.ConfigParser()
parser.read(cfgFN)
for sec,op in required_ops:
    if not parser.has_option(sec, op):
        sys.stderr.write("ERROR: need (%s, %s) in %s.\n" % (sec,op,cfgFN))
        sys.stderr.write("Read README to get help inforamtion.\n")
        sys.exit(1)

url = parser.get("Base", "url")
username = parser.get("Base", "username")
password = parser.get("Base", "password")

z1 = ZabbixRequest(url, username, password)
# 获取版本信息
print z1.version
# 直接调用底层request 获取所有主机列表
#print z1.do_request('host.get', {"output": ["hostid","status","host"], "selectInterfaces": ["interfaceid", "ip" ]})

# 获取所有的主机信息
#print z1.get_hosts()
# search获取主机信息,模糊匹配
#print z1.search_host("zabbix")
# search获取主机信息，精确匹配
#print z1.search_host("Zabbix server", exactly=1)

# 获取主机的所有监控项
#print z1.get_items("monitor-1-c")
# search指定监控项 模糊匹配name
#print z1.search_item("zabbix", "system", search_field="name")
# search指定监控项 模糊匹配key 指定输出内容 默认输出所有
#print z1.search_item("zabbix", "system.cpu.util[,idle]", search_field="key_", output_info=["itemid","name","key_","state","status","lastvalue","hostid"])

# 获取最新的监控项的值
#print z1.get_item_lastvalue("zabbix", "system.cpu.util[,idle]",search_field="key_")

# 获取最近1小时内的数据
#print z1.get_specific_items_history_data("zabbix", "system.cpu.util[,idle]", hours=1)



if __name__ == '__main__':
    # 对zabbix主机组 下的所有主机的 cpu使用情况 system.cpu.util[,idle]创建screen
    # 主机组名称 Zabbix servers
    # 监控项的key system.cpu.util[,idle]

    host_group = "Zabbix servers"
    _key = "system.cpu.util[,idle]"
    try:
        host_list = []
        _r = z1.search_host_with_group(host_group)
        if _r['success']:
            host_list = _r['results']
            #print host_list
    except Exception as e:
        print str(e)

    all_graph_info = []

    for _h in host_list[0]['hosts']:
        hostname,hostid = _h['host'],_h['hostid']
        #print hostname,hostid
        items = z1.search_item(hostname, _key, search_field="key_",
                       output_info=["itemid", "name", "key_", "state", "status", "lastvalue", "hostid"])
        if items['success']:
            try:
                itemid = items['results'][0]['itemid']
                graph_info = z1._get_graphid_from_hostid_and_itemid(hostid,itemid)
                all_graph_info.append(graph_info)
            except Exception as e:
                print str(e)
                continue
        else:
            continue

    # 定义screen名字
    screen_name = "xxxxxxx"
    # 定义每行三张图
    hsize = 3

    # 计算行数量
    total_graph_num = len(all_graph_info)
    if total_graph_num % hsize != 0:
        vsize = len(all_graph_info) / hsize + 1
    else:
        vsize = len(all_graph_info) / hsize

    # screen的item列表
    screenitems = []
    pos_tag = 0
    for _g in all_graph_info:
        x = pos_tag % hsize
        y = pos_tag / hsize
        screenitems.append({"resourcetype": 0,
                             "resourceid": _g['graphid'],
                             "dynamic": 1,
                             "rowspan": 1,
                             "colspan": 1,
                             "x": x,
                             "y": y
                            })
        pos_tag += 1
    # 创建screen
    _screen_attr = z1._create_screen(screen_name, hsize, vsize, screenitems)
    print _screen_attr