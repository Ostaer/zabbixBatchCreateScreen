# zabbix Batch Create Screen
zabbix batch create screen script

Create screen for an item of all hosts in an hostgroup

For example:

HostGroup: "Zabbix servers"

Item Key: "system.cpu.util[,idle]"

### configure file

----
>sample.cfg zabbix config file

### Run 

```
python sample.py
```
