from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
import collections

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

def deep_update(source, overrides):
    """
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
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
