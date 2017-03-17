Let's say you want to generate these two interface configurations:

```
interface GigabitEthernet0/2
 description device2-gi3/5-device-gi0/2
 no switchport
 bandwidth 100000
 ip address 10.0.250.20 255.255.255.240
!
interface GigabitEthernet0/3
 description device3-gi5/1-device-gi0/3
 switchport trunk encapsulation dot1q
 switchport trunk native vlan 5
 switchport trunk allowed vlan 1,2,903-905,915-917,925,926,961,971,980,990-996
 switchport mode dynamic desirable
```

Playbook run:

```
➜  /working ansible-playbook -i inventory.txt site.yml

PLAY [all] *********************************************************************

TASK [interface : Update the interface with their parents] *********************
ok: [device.company.net]

TASK [interface : Render the interfaces based on their os and type] ************
included: /working/roles/interface/tasks/ios-interface.yml for device.company.net
included: /working/roles/interface/tasks/ios-interface.yml for device.company.net

TASK [interface : Render the interfaces based on their os and type] ************
ok: [device.company.net]

TASK [interface : Show the interface parent] ***********************************
ok: [device.company.net] => {
    "interface_parent": "interface GigabitEthernet0/2"
}

TASK [interface : Show the interface context lines] ****************************
ok: [device.company.net] => {
    "msg": [
        "description device2-gi3/5-device-gi0/2",
        "bandwidth 100000",
        "speed auto",
        "duplex auto",
        "no switchport",
        "ip address 10.0.250.20 255.255.255.240"
    ]
}

TASK [interface : Render the interfaces based on their os and type] ************
ok: [device.company.net]

TASK [interface : Show the interface parent] ***********************************
ok: [device.company.net] => {
    "interface_parent": "interface GigabitEthernet0/3"
}

TASK [interface : Show the interface context lines] ****************************
ok: [device.company.net] => {
    "msg": [
        "description device3-gi5/1-device-gi0/3",
        "speed auto",
        "duplex auto",
        "switchport trunk encapsulation dot1q",
        "switchport trunk native vlan 5",
        "switchport trunk allowed vlan 1,2,903-905,915-917,925,926,961,971,980,990-996",
        "switchport mode dynamic desirable"
    ]
}

PLAY RECAP *********************************************************************
device.company.net         : ok=9    changed=0    unreachable=0    failed=0
```
