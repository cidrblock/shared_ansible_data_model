### Desired configuration:

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

### Define the data model in /group_vars/all/datamodels.yml

```
interface:
  bandwidth: False              # int
  description: technical debt   # str
  duplex: auto                  # str (auto/full/half)
  speed: auto                   # int (10/100/1000 etc)
  type: False                   # str (l2/l3)
  switchport:
    mode: False                 # str (access/trunk)
    trunk_allowed_vlan: False   # str (1,2,5,10)
    trunk_encapsulation: False  # str (dot1q)
    trunk_native_vlan: False    # int (5)
  ip_address:
      ip: False                 # str (10.5.1.1)
      mask: False               # str (255.255.255.0)
```

### Define the profiles in /group_vars/all/interfaces.yml

```
interface_routed:
  inherit_from: interface
  type: routed

interface_uplink:
  inherit_from: interface
  switchport:
    mode: dynamic desirable
    trunk_encapsulation: dot1q
  type: uplink
```

### Define the device specific values in host_vars:

```
os: ios

interfaces:
  - bandwidth: 100000
    description: device2-gi3/5-device-gi0/2
    inherit_from: interface_routed
    ip:
      address: 10.0.250.20
      netmask: 255.255.255.240
    name: GigabitEthernet0/2
  - description: device3-gi5/1-device-gi0/3
    inherit_from: interface_uplink
    switchport:
      trunk_allowed_vlan: 1,2,903-905,915-917,925,926,961,971,980,990-996
      trunk_native_vlan: 5
    name: GigabitEthernet0/3
```

### Using a custom lookup we can handle the recursive inheritance:

```
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
import collections

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

def deep_update(source, overrides):
    for key, value in overrides.iteritems():
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source

def add_defaults(entry, defaults):
    default = defaults[entry['inherit_from']].copy()
    if 'inherit_from' in default:
        default = add_defaults(default, defaults)
    deep_update(default, entry)
    return default

class LookupModule(LookupBase):
    def run(self, entries, variables=None, **kwargs):
        result = []
        for entry in entries[0]:
            if 'inherit_from' in entry:
                result.append(add_defaults(entry, entries[1]).copy())
            else:
                result.append(entry.copy())
        return result
```

### Before updating the device, update each interface with the profile and global defaults

```
- name: Update the interface with their parents
  set_fact:
    interfaces: "{{ lookup('add_defaults', interfaces, hostvars[inventory_hostname] ) }}"
```

### Render each interface based on the OS and interface type:

```
- name: Switch to OS specific files and templates
  include: "{{ '%s-interface.yml' % os }}"
  with_items: "{{ interfaces }}"
---
- name: Render the interfaces based on their os and type
  set_fact:
    interface_parent: "{{ 'interface %s' % item['name'] }}"
    interface_lines: "{{ lookup('template', '%s-%s.j2' % (os, item['type'])) }}"
```

### jinja templates exist for different profiles to keep the dry and free of complex logic:

```
# ios-routed.j2

{% for line in ['description', 'bandwidth', 'speed', 'duplex'] %}
{% if item[line] %}
{{ line }} {{ item[line] }}
{% endif %}
{% endfor %}
no switchport
ip address {{ item['ip']['address'] }} {{ item['ip']['netmask'] }}

---
# ios-uplink.j2

{% for line in ['description', 'bandwidth', 'speed', 'duplex'] %}
{% if item[line] %}
{{ line }} {{ item[line] }}
{% endif %}
{% endfor %}
switchport trunk encapsulation {{ item['switchport']['trunk_encapsulation'] }}
switchport trunk native vlan {{ item['switchport']['trunk_native_vlan'] }}
switchport trunk allowed vlan {{ item['switchport']['trunk_allowed_vlan'] }}
switchport mode {{ item['switchport']['mode'] }}
```

Run and profit:

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
