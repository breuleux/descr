
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


class DescriptionProcessor(object):

    @classmethod
    def process(cls, obj, parent_rules):
        if isinstance(obj, (str, int, float)):
            return obj
        elif isinstance(obj, (set, frozenset)):
            raise ValueError("Not expecting a set here.", obj)
        else:
            return cls(obj, parent_rules)

    def __init__(self, description, parent_rules):
        classes, children = exhaust_stream(description)
        rules, children = parent_rules.explore(classes, children)
        self.rules = rules
        self.classes = rules.classes
        self.properties = rules.properties
        self.children = children
        self.phase1()
        self.phase2()
        self.phase3()

    def phase1(self):

        props = self.properties

        for f in props.get(":hide", ()):
            if f(self.classes, self.children):
                self.classes = {}
                self.children = []
                return

        for f in props.get(":rearrange", ()):
            self.children = f(self.classes, self.children)

        before_acc = []
        for f in props.get(":before", ()):
            before_acc = [f(self.classes, self.children)] + before_acc

        after_acc = []
        for f in props.get(":after", ()):
            after_acc += [f(self.classes, self.children)]

        if before_acc or after_acc:
            self.children = list(itertools.chain(before_acc, self.children, after_acc))

    def phase2(self):
        raw = self.properties.get(":raw", False)

        if raw and raw[-1]:
            self.children = list(map(str, parts))
        else:
            self.children = [self.process(child, self.rules)
                             for child in self.children]

    def phase3(self):

        props = self.properties

        for f in props.get(":post", ()):
            self.children = f(self.classes, self.children)



class Formatter(object):
    pass


class RawFormatter(Formatter):

    def setup(self):
        return ""

    def translate(self, stream):
        return str(stream)



class Printer(object):

    def __init__(self, port, descr, formatter):
        self.port = port
        self.descr = descr
        self.formatter = formatter

    def translate(self, stream, rules = None):
        if rules is not None:
            formatter = self.formatter.copy()
            formatter.add_rules(rules)
        else:
            formatter = self.formatter
        return formatter.translate(stream)

    def write(self, stream, rules = None):
        s = self.translate(stream, rules)
        self.port.write(s)

    def pr(self, *objects, **kwargs):
        if "descr" in kwargs:
            descr = kwargs.pop("descr")
        else:
            descr = self.descr
        d = [descr(obj) for obj in objects]
        self.write(d, **kwargs)

    __call__ = pr



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

    def fprop(self, selector, prop, value, f = None, elsevalue = None):
        if f is not None:
            v = lambda c, d: value if f(c, d) else elsevalue
        elif callable(value):
            v = value
        elif value is None:
            v = None
        else:
            v = lambda c, d: value
        return self.rule(selector, {prop: v})

    def rule(self, selector, props1 = {}, **props2):
        self.add_rule(selector, props1, **props2)
        return self

    def rules(self, *rules):
        self.add_rules(*rules)
        return self

    def classes(self, selector, cls, f = None):
        return self.fprop(selector, ":classes", cls, f)

    def pclasses(self, selector, cls, f = None):
        return self.fprop(selector, ":+classes", cls, f)

    def mclasses(self, selector, cls, f = None):
        return self.fprop(selector, ":-classes", cls, f)

    def pmclasses(self, selector, p, m):
        return self.rule(selector, {":+classes": p,
                                    ":-classes": m})

    def replace(self, selector, value, f = None):
        return self.fprop(selector, ":replace", value, f, [])

    def rearrange(self, selector, value, f = None):
        return self.fprop(selector, ":rearrange", value, f, [])

    def before(self, selector, value, f = None):
        return self.fprop(selector, ":before", value, f, [])

    def after(self, selector, value, f = None):
        return self.fprop(selector, ":after", value, f, [])

    def hide(self, selector, f = None):
        if f is None:
            f = lambda c, p: True
        return self.fprop(selector, ":hide", f)

    def inspect(self, selector, f = None):
        if f is None:
            f = lambda node: True
        return self.fprop(selector, ":inspect", f)

    def post(self, selector, value, f = None):
        return self.fprop(selector, ":post", value, f, [])

    def strip_fields(self, name, *fields):
        for field in fields:
            if field == name:
                self.mclasses(".{%s}" % name, "object")
            else:
                self.mclasses(".{%s} .{+%s}" % (name, field.strip()), "field")
        return self

    def __getattr__(self, attr):
        if attr.startswith("prop_"):
            attribute = attr[5:]
            def f(selector, value):
                return self.rule(selector, {attribute: value})
            return f
        else:
            return getattr(super(RuleBuilder, self), attr)


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


