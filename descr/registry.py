
from types import FunctionType, MethodType
NoneType = type(None)


def classes(*classes):
    classes = frozenset(classes)
    def f(datum, _):
        return (classes, str(datum))
    return f

def str_with_classes(*classes):
    classes = frozenset(classes)
    def f(datum, _):
        return (classes, str(datum))
    return f

def str_with_classes_and_itself(*classes):
    classes = frozenset(classes)
    def f(datum, _):
        s = str(datum)
        return (classes, {"@"+s}, s)
    return f

def iter_with_classes(*classes):
    classes = frozenset(classes)
    def f(datum, recurse):
        return (classes,) + tuple(map(recurse, datum))
    return f

types_registry = {
    tuple: iter_with_classes("@tuple"),
    list: iter_with_classes("@list"),
    set: iter_with_classes("@set"),
    dict: lambda d, recurse: ((frozenset({"@dict"}),)
                              + tuple(({"assoc"}, recurse(k), recurse(v))
                                      for k, v in d.items())),
    bool: str_with_classes_and_itself("@bool"),
    int: str_with_classes("@int"),
    float: str_with_classes("@float"),
    str: str_with_classes("@str"),

    NoneType: classes("@None"),
}
