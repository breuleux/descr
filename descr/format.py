
import re
import itertools
from .registry import types_registry


def exhaust_stream(stream):
    classes = set()
    parts = []
    distribute = []

    for entry in stream:
        if isinstance(entry, (set, frozenset)):
            classes.update(entry)
        elif isinstance(entry, dict):
            for klass in entry.get(True, ()):
                classes.add(klass)
            for klass in entry.get(False, ()):
                classes.remove(klass)
            if "distribute" in entry:
                distribute.append(entry["distribute"])
        else:
            parts.append(entry)

    if distribute:
        parts = [distribute + [part] if isinstance(part, str)
                 else itertools.chain(distribute, part)
                 for part in parts]

    return classes, parts


class Formatter(object):
    pass


class RawFormatter(Formatter):

    def setup(self):
        return ""

    def translate(self, stream):
        return str(stream)



class Printer(object):

    def __init__(self, port, descr, formatter, setup_now = True, top = "pydescr"):
        self.port = port
        self.descr = descr
        self.formatter = formatter
        self.top = top
        if setup_now:
            self.setup()

    def setup(self):
        self.port.write(self.formatter.setup())

    def write(self, stream):
        s = self.formatter.translate(stream)
        self.port.write(s)

    def pr(self, obj):
        d = self.descr(obj)
        if self.top:
            d = ({self.top}, d)
        self.write(d)

    __call__ = pr


class AlwaysSetupPrinter(Printer):

    def write(self, stream):
        self.setup()
        self.write(stream)


class dict2(dict):

    __equiv = dict("C: P+ M- T~ A& B!".split())
    __sub = re.compile("([CPMTAB])__")

    def __init__(self, d1, **d2):
        self.update(d1)
        def repl(m):
            letter = m.groups()[0]
            return self.__equiv[letter]
        for k, v in d2.items():
            self[self.__sub.sub(repl, k).replace("_", "-")] = v


class RulesRegistry(object):

    def __init__(self, *rules):
        self.rules = list(rules)

    def copy(self):
        r = type(self)()
        r.add_rules_from(self.rules)
        return r

    def get_rules(self):
        return list(self.rules)

    def add_rule(self, selector, props1 = {}, **props2):
        self.rules.append((selector, dict2(props1, **props2)))

    def add_rules(self, *rules):
        self.add_rules_from(rules)

    def add_rules_from(self, rules):
        self.rules.extend(rules)

    def __radd__(self, other):
        r = type(self)()
        r.add_rules_from(other.rules)
        r.add_rules_from(self.rules)
        return r

    def __add__(self, other):
        ts, to = type(self), type(other)
        if to is not ts and issubclass(to, ts):
            return other.__radd__(self)
        r = self.copy()
        r.add_rules_from(other.rules)
        return r


class RuleBuilder(RulesRegistry):

    def builder_for(self, selector):
        class C:
            def __getattr__(_, attr):
                part = getattr(self, attr)
                def f(*args, **kwargs):
                    part(selector, *args, **kwargs)
                    return this
                return f
        this = C()
        return this

    def prop(self, selector, prop, value):
        return self.rule(selector, {prop: value})

    def rule(self, selector, props1 = {}, **props2):
        self.add_rule(selector, props1, **props2)
        return self

    def rules(self, *rules):
        self.add_rules(*rules)
        return self

    def pclasses(self, selector, f):
        return self.rule(selector, {":+classes": f})

    def mclasses(self, selector, f):
        return self.rule(selector, {":-classes": f})

    def pmclasses(self, selector, p, m):
        return self.rule(selector, {":+classes": p,
                                    ":-classes": m})

    def before(self, selector, f):
        return self.rule(selector, {":before": f})

    def after(self, selector, f):
        return self.rule(selector, {":after": f})

    def join(self, selector, f):
        return self.rule(selector, {":join": f})

    def rearrange(self, selector, f):
        return self.rule(selector, {":rearrange": f})

    def strip_fields(self, name, *fields):
        for field in fields:
            if field == name:
                self.mclasses(".{%s}" % name, "object")
            else:
                self.mclasses(".{%s} .{+%s}" % (name, field.strip()), "field")
        return self


class Layout(object):

    def __init__(self):
        self.styles = {}
        self.layout = None

    def __getitem__(self, name):
        style = self.styles[name]
        rb = (self.layout["open"]
              + style["open"]
              + style["close"]
              + self.layout["close"])
        return rb

    def copy(self):
        rval = Layout()
        rval.styles = {style: {k: builder.copy() for k, builder in overlay.items()}
                       for style, overlay in self.styles.items()}
        rval.layout = {k: builder.copy() for k, builder in overlay.items()}



def descr(datum, recurse = None):
    recurse = recurse or descr

    try:
        # I believe this is what str() and repr() do otherwise
        # representation of class objects wouldn't be customizable
        f = type(datum).__descr__
    except AttributeError:
        for t in type(datum).__mro__:
            if t in types_registry:
                return types_registry[t](datum, recurse)
        else:
            return str(datum)
    else:
        # Executed only if there was a __descr__ and won't mask
        # exceptions.
        return f(datum, recurse)


def augment_with_idclass(descr):
    def descr2(obj):
        d = descr(obj, descr2)
        if not isinstance(d, str):
            d = itertools.chain([{"#"+str(id(obj))}], d)
        return d
    return descr2


