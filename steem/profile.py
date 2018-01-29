import json
import collections


class DotDict(dict):
    def __init__(self, *args):
        """ This class simplifies the use of "."-separated
            keys when defining a nested dictionary:::

                >>> keys = ['profile.url', 'profile.img']
                >>> values = ["http:", "foobar"]
                >>> print(Profile(keys, values))

                {"profile": {"url": "http:", "img": "foobar"}}

        """
        if len(args) == 2:
            for i, item in enumerate(args[0]):
                t = self
                parts = item.split('.')
                for j, part in enumerate(parts):
                    if j < len(parts) - 1:
                        t = t.setdefault(part, {})
                    else:
                        t[part] = args[1][i]
        elif len(args) == 1 and isinstance(args[0], dict):
            for k, v in args[0].items():
                self[k] = v
        elif len(args) == 1 and isinstance(args[0], str):
            for k, v in json.loads(args[0]).items():
                self[k] = v


class Profile(DotDict):
    """ This class is a template to model a user's on-chain
        profile according to

            * https://github.com/adcpm/steemscript
    """

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)

    def __str__(self):
        return json.dumps(self)

    def update(self, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                self.setdefault(k, {}).update(v)
            else:
                self[k] = u[k]

    def remove(self, key):
        parts = key.split(".")
        if len(parts) > 1:
            self[parts[0]].pop(".".join(parts[1:]))
        else:
            super(Profile, self).pop(parts[0], None)


if __name__ == '__main__':
    keys = ['profile.url', 'profile.img']
    values = ["http:", "foobar"]
    print(Profile(keys, values))
    print(Profile({"foo": "bar"}))
