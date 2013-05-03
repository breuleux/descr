
import traceback
from types import FunctionType, MethodType, TracebackType
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

def format_traceback(tb, recurse):
    elements = [{"@traceback", "+traceback", "object"}]
    while tb is not None:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        code = frame.f_code
        fname = code.co_name
        filename = code.co_filename
        tb = tb.tb_next
        elements.append(
            ({"@frame", "object"},
             ({"+fname", "field"},
              fname),
             ({"+location", "field", "location"},
              filename,
              ({"hl1"}, (lineno, 1), "stripline"))))
    return elements


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

    TracebackType: format_traceback,
}
