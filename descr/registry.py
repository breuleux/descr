
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


# Adapted from traceback.py
def _iter_chain(exc, custom_tb=None, seen=None):
    if seen is None:
        seen = set()
    seen.add(exc)
    its = []
    cause = getattr(exc, '__cause__', None)
    if cause is not None and cause not in seen:
        its.append(_iter_chain(cause, None, seen))
    else:
        context = getattr(exc, '__context__', None)
        if context is not None and context not in seen:
            its.append(_iter_chain(context, None, seen))
    its.append([(exc, custom_tb or getattr(exc, '__traceback__', None))])
    # itertools.chain is in an extension module and may be unavailable
    for it in its:
        for x in it:
            yield x

def _list_frames(tb):
    elements = []
    while tb is not None:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        code = frame.f_code
        fname = code.co_name
        filename = code.co_filename
        tb = tb.tb_next
        framedata = [{"@frame", "object"},
                     ({"+fname", "field"},
                      fname),
                     ({"+location", "field", "location"},
                      filename,
                      ({"hl1"}, (lineno, 1), "stripline"))]
        elements.append(framedata)
    return elements

def format_traceback(tb, recurse):
    elements = [{"@traceback", "+traceback", "object"}]
    return elements + _list_frames(tb)


def format_exception(exc, recurse):
    name = type(exc).__name__
    elements = [{"@Exception", "@"+name, "+"+name, "object"}]

    try:
        args = exc.args
    except AttributeError:
        elements.append(repr(exc))
        return elements

    if len(args) == 0:
        return elements
    else:
        message = args[0]
        rest = args[1:]
        elements.append([{"exception_message"}, recurse(message)])
        if rest:
            elements.extend(map(recurse, rest))
        return elements

def format_traceback_from_exception(orig_exc, recurse):
    elements = [{"@traceback", "+traceback", "object"}]
    for exc, tb in _iter_chain(orig_exc):
        elements += _list_frames(tb)
        elements.append(format_exception(exc, recurse))
    return elements


types_registry = {
    tuple: iter_with_classes("@tuple", "sequence"),
    list: iter_with_classes("@list", "sequence"),
    set: iter_with_classes("@set", "sequence"),
    frozenset: iter_with_classes("@set", "@frozenset", "sequence"),
    dict: lambda d, recurse: ((frozenset({"@dict", "sequence"}),)
                              + tuple(({"assoc"}, recurse(k), recurse(v))
                                      for k, v in d.items())),
    bool: str_with_classes_and_itself("@bool", "scalar"),
    int: str_with_classes("@int", "scalar"),
    float: str_with_classes("@float", "scalar"),
    complex: str_with_classes("@complex", "scalar"),
    str: str_with_classes("@str", "scalar"),
    NoneType: classes("@None", "scalar"),

    Exception: format_traceback_from_exception,
    TracebackType: format_traceback,
}
