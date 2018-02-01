import collections


def common_iterable(obj):
    """
    Offers a single iterator for a dictionary or list.
    Based on : to https://stackoverflow.com/questions/12325608/iterate-over-a-dict-or-list-in-python
    :param obj: dictionary or list
    :return: iterator
    """
    if isinstance(obj, dict):
        return ((value, obj[value], index) for index, value in enumerate(obj.keys()))
    else:
        return ((index, value, index) for index, value in enumerate(obj))


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    From: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9 (adapted python 3.6)
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def map_recursively(dct, value):
    mapped_dct = {}
    for k, v in dct.items():
        if k in dct and isinstance(dct[k], dict):
            mapped_dct[k] = map_recursively(dct[k], value)
        else:
            mapped_dct[k] = value
    return mapped_dct


def is_str(s):
    """
    Checks if a variable if a string
    :param s: a string
    :return: boolean
    """
    return isinstance(s, str)


def to_dict(*kwargs):
    print(kwargs)
    for key, value in kwargs:
        print(key, value)
