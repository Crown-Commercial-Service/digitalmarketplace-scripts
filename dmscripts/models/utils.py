import operator


def process_collection(rules, collection):
    if not rules:
        return collection

    for c in collection:
        for k, v in rules.items():
            if c.get(k):
                c[k] = v(c[k])


def return_filtered_collection(rules, collection):
    if not rules:
        return collection

    # `contains` would be trickier to include because it switches the argument order
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq
    }

    for key, op, to_compare in rules:
        collection = list(filter(lambda x: ops[op](x[key], to_compare), collection))

    return collection


def return_sorted_collection(_key, collection):
    return sorted(collection, key=lambda x: x[_key]) if _key else collection
