# -*- coding:utf-8 -*-
import urllib2
import json
import timehandler

class ZabbixRequestException(Exception):
    '''
    zabbix exception
    '''
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class ZabbixRequest():
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.id = 1
        self.version = self.do_request("apiinfo.version", [], 0)['results']
        self.auth = self.auth()

    ###############################################
    # 基础部分
    ###############################################
    def do_request(self, method, params=None, auth=1):
        '''
        zabbix 请求基础操作
        :param method:zabbix api支持的方法
        :param params: zabbix api支持的参数
        :param auth: 是否是认证擦欧总
        :return:
        '''
        if auth:
            data = json.dumps({
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": "{}".format(self.id),
                "auth": self.auth
            })
        else:
            data = json.dumps({
                "jsonrpc":"2.0",
                "method": method,
                "params": params,
                "id": "{}".format(self.id),
            })
        def _r():
            self.id += 1
            req = urllib2.Request(self.url, data, {'Content-Type': 'application/json-rpc'})
            _response = urllib2.urlopen(req, data, timeout=20)
            response = json.loads(_response.read())

            if "error" in response:
                return self.response_format(0,response)
            else:
                return self.response_format(1,response)

        try:
            return _r()
        except Exception as err:
            try:
                return _r()
            except Exception as e:
                raise ZabbixRequestException("Zabbux request failed! {}".format(e))

    def response_format(self, successed, response):
        '''
        全局通用响应格式
        :param successed:
        :param response:
        :return:
        '''
        response_dict = {}
        response_dict['success'] = bool(successed)
        if successed:
            response_dict['results'] = response['result']
        else:
            response_dict['error'] = response['error']
        return response_dict

    def auth(self):
        '''
        认证操作
        :return:
        '''
        method = 'user.login'
        params = {
            'user': self.username,
            'password': self.password
        }

        try:
            r = self.do_request(method, params, auth=0)
            if r['success']:
                return r['results']
        except Exception as e:
            raise ZabbixRequestException("Auth failed! {}".format(e))
    ###############################################
    # 自定义请求方法部分
    ###############################################
    def get_hosts(self):
        '''
        获取所有的host
        :return:
        '''
        method = "host.get"
        params = {
            "output": ["hostid", "status", "host"],
            "selectInterfaces": ["interfaceid", "ip"]
        }
        return self.do_request(method, params)

    def search_host(self, hostname, exactly=0):
        '''
        搜索host
        :param hostname:
        :param exactly: 是否精确匹配主机名
        :return:
        '''
        method = "host.get"
        if exactly:
            params =  {
                    "output": ["hostid", "status", "host"],
                    "selectInterfaces": ["interfaceid", "ip"],
                    "filter":{
                              "host":[hostname]
                        }
                }
        else:
            params = {
                "output": ["hostid", "status", "host"],
                "selectInterfaces": ["interfaceid", "ip"],
                "search": {
                    "host": [hostname]
                }
            }
        return self.do_request(method, params)

    def get_items(self, hostname):
        '''
        搜索主机名的所有item
        :param hostname:
        :return:
        '''
        hostid = self._get_hostid_from_hostname(hostname)
        method = 'item.get'
        params = {
                    "output": ["itemid","name","key_","state","status","lastvalue","hostid"],
                    "hostids":hostid,
                    "webitems": True,
                    "sortfield": "name",
                    }
        return self.do_request(method,params)

    def search_item(self, hostname, item, search_field="name", output_info="extend"):
        '''
        搜索指定主机的指定item
        :param hostname:
        :param item: item的名字
        :param search_field: 可选name _key等
        :param output_info: 输出的信息
        :return:
        '''
        hostid = self._get_hostid_from_hostname(hostname)
        method = 'item.get'
        params = {
            "output": output_info,
            "hostids": hostid,
            "webitems": True,
            "search": {
                search_field: item
            },
            "sortfield": search_field,
        }
        return self.do_request(method, params)
    def get_item_lastvalue(self, hostname, item, search_field="name"):
        '''
        获取指定item的最新的监控的值
        :param hostname:
        :param item:
        :param search_field:
        :return:
        '''
        _items = self.search_item(hostname, item, search_field=search_field, output_info=["itemid","name","key_","state","status","lastvalue", "lastclock","hostid"])
        if _items['success']:
            if len(_items['results']) == 1:
                return _items['results'][0]['lastvalue']
            else:
                raise ZabbixRequestException("Mulple item Found!")
        else:
            raise ZabbixRequestException("Zabbix get last value field!")



    def search_host_with_group(self, groupname):
        '''
        根据组名搜索主机名
        :param groupname:
        :return:
        '''
        method = "hostgroup.get"
        params = {
            #"output": ["hostid", "status", "host"],
            "selectHosts": ["host","hostid"],
            "filter":{
                "name":groupname,
            }
        }
        return self.do_request(method, params)

    def _get_hostnameid_from_groupname(self,groupname):
        '''
        根据组名搜索主机id
        :param groupname:
        :return:
        '''
        _result = self.search_host_with_group(groupname)
        if _result['success']:
            hosts = _result['results'][0]['hosts']
        else:
            raise ZabbixRequestException("Zabbux get host failed!")
        return hosts

    def _get_hostid_from_hostname(self, hostname):
        '''
        根据hostname搜索hostid
        :param hostname:
        :return:
        '''
        _hosts = self.search_host(hostname)
        if _hosts['success']:
            hostid = _hosts['results'][0]['hostid']
        else:
            raise ZabbixRequestException("Zabbux get host failed!")
        return hostid
    def _match_hostid_from_hostname(self, hostname):
        '''
        模糊搜索主机id
        :param hostname:
        :return:
        '''
        _hosts = self.search_host(hostname)
        hostid_list = []
        if _hosts['success']:
            for i in _hosts['results']:
                hostid_list.append((i['hostid'],i['host']))
        else:
            raise ZabbixRequestException("Zabbux get host failed!")
        return hostid_list
    def _get_itemid_from_item(self, hostid, item, search_field="key_"):
        '''
        根据item搜索itemid
        :param hostid:
        :param item: 名字或者key
        :param search_field: name 或者 _key
        :return:
        '''
        method = 'item.get'
        params = {
            "output": ["itemid","name","key_","state","status","lastvalue","hostid"],
            "hostids": hostid,
            "webitems": True,
            "filter": {
                "key_": item
            },
            "sortfield": search_field,
        }
        _items = self.do_request(method, params)
        if _items['success']:
            itemid = _items['results'][0]['itemid']
        else:
            raise ZabbixRequestException("Zabbux get item failed!")
        return itemid
    def _get_graphid_from_hostid_and_itemid(self,hostid,itemid):
        '''
        获取graphid
        :param hostid: 属于该hostid的graph
        :param itemid: 包含改itemid的graph
        :return:
        '''
        method = "graph.get"
        params = {
            "output": ["graphid","name","width","height"],
            "hostids": hostid,
            "itemids": itemid,
            "sortfield": "name"
        }
        _graphs = self.do_request(method, params)
        if _graphs['success']:
            result = _graphs['results'][0]
        else:
            raise ZabbixRequestException("Zabbux get graphid failed!")
        return result

    def _create_screen(self,screen_name, hsize, vsize, screenitems=[]):
        '''
        简单的创建screen
        :param screen_name:
        :param hsize:
        :param vsize:
        :param screenitems:
        :return:
        '''
        method = "screen.create"
        params = {
                  "name": screen_name,
                  "hsize": hsize,
                  "vsize": vsize,
                  "screenitems": screenitems,
                  }
        create_screen = self.do_request(method, params)
        if create_screen['success']:
            result = create_screen['results']
        else:
            print create_screen
            raise ZabbixRequestException("Zabbux create screen failed!")
        return result

    def _create_screenitem(self, params={}):
        '''
        为已经存在的screen增加item
        :param params:
        :return:
        '''
        method = "screenitem.create"

        screenitem = self.do_request(method, params)
        if screenitem['success']:
            result = screenitem['results']
        else:
            print screenitem
            raise ZabbixRequestException("Zabbux create screenitem failed!")
        return result

    def get_item_history_data(self, hostname, item, start_time, end_time, search_field="key_"):
        '''
        获取历史健康数据
        :param hostname:
        :param item:
        :param start_time: 时间戳
        :param end_time: 时间戳
        :param search_field:
        :return:
        '''
        hostid = self._get_hostid_from_hostname(hostname)
        itemid = self._get_itemid_from_item(hostid, item, search_field=search_field)
        method = 'history.get'
        params = {
                "output": "extend",
                "hostids": hostid,
                'itemids': itemid,
                "webitems": True,
                "sortfield": "clock",
                "sortorder": "DESC",
                # "limit":10,
                'time_from': start_time,
                'time_till': end_time,
            }
        return self.do_request(method, params)

    def get_specific_items_history_data(self, hostname, item, days=0, hours=0, minutes=0, seconds=0, search_field="key_"):
        '''
        获取指定item的历史数据 一段时间内
        :param hostname:
        :param item:
        :param days:
        :param hours:
        :param minutes:
        :param seconds:
        :param search_field:
        :return:
        '''
        start_time = timehandler.timedeltahandler(days=days, hours=hours, minutes=minutes, seconds=seconds)
        end_time = timehandler.currenttimestamp()
        return self.get_item_history_data(hostname, item, start_time, end_time, search_field=search_field)

    def get_all_items_history_data(self, hostname, item, search_field="key_"):
        '''
        获取指定item的所有历史数据
        :param hostname:
        :param item:
        :param search_field:
        :return:
        '''
        start_time = "0"
        end_time = timehandler.currenttimestamp()
        return self.get_item_history_data(hostname, item, start_time, end_time, search_field=search_field)
