
import re
import sys
import itertools
from collections import defaultdict, OrderedDict
from functools import partial

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


def extract_sole_class(selector):
    m = re.match("^\\.([^ ]*)$", selector)
    if m:
        escaped = False
        s = ""
        for c in m.groups()[0]:
            if escaped:
                s += c
                escaped = False
            elif c.isalnum() or c == "-" or c == "_":
                s += c
            elif c == "\\":
                escaped = True
            else:
                return None
        return s
    else:
        return None



# def custom_merge(orig, new):
#     additions = {}
#     for k, v in new.items():
#         if k == "!clear" and v:
#             orig.clear()
#         elif v is None and k in orig:
#             del orig[k]
#         else:
#             additions[k] = v
#     orig.update(additions)
#     return orig


def custom_merge(orig, new, merge = None):
    additions = {}
    for k, v in new.items():
        if k == "!clear" and v:
            orig.clear()
        elif v is None and k in orig:
            del orig[k]
        else:
            additions[k] = v
    if merge is None:
        orig.update(additions)
        return orig
    else:
        return merge(orig, additions)

def _merge_to_lists(a, b):
    for k, v in b.items():
        a[k].append(v)
    return a

def _merge_lists(a, b):
    for k, v in b.items():
        a[k].extend(v)
    return a


class SimpleRules:

    def __init__(self, rules):
        self.i = 0
        self.priorities = {}
        self.rules = defaultdict(lambda: defaultdict(list))
        self.assimilate_rules(rules)

    # def assimilate_rules(self, rules):
    #     i = self.i
    #     for name, props in rules:
    #         self.priorities[name] = i
    #         custom_merge(self.rules[name], props)
    #         i += 1
    #     self.i = i

    def assimilate_rules(self, rules):
        i = self.i
        for name, props in rules:
            self.priorities[name] = i
            # orig = self.rules[name]
            # try:
            #     clear = props["!clear"]
            #     props = dict(props)
            #     props.pop("!clear")
            #     orig.clear()
            # except KeyError:
            #     pass
            # for k, v in props.items():
            #     if v is None:
            #         orig[k][:] = None
                
            custom_merge(self.rules[name], props, _merge_to_lists)
            i += 1
        self.i = i

    def get_properties(self, classes):
        properties = defaultdict(list)
        for i, props in sorted((self.priorities[klass], self.rules[klass])
                               for klass in classes
                               if klass in self.priorities):
            properties = custom_merge(properties, props, _merge_lists)
            # properties.update(props)
        return properties

    def call(self, f, c, p):
        # if hasattr(f, "with_classes"):
        #     return f.with_classes(c, p)
        # return f(*p)
        return f(c, p)

    def premanipulate(self, classes, parts):

        this = self.premanipulate
        props = self.get_properties(classes)

        for prop, combine in [(":classes", lambda x, y: y),
                              (":+classes", lambda x, y: x | y),
                              (":-classes", lambda x, y: x.difference(y)),
                              (":&classes", lambda x, y: x & y)]:
            for new_classes in props.get(prop, ()):
                if callable(new_classes):
                    new_classes = self.call(new_classes, classes, parts)
                if isinstance(new_classes, str):
                    new_classes = {new_classes}
                if new_classes:
                    new_classes = combine(classes, new_classes)
                    if new_classes != classes:
                        return this(new_classes, parts)

        for rearrange in props.get(":rearrange", ()):
            if callable(rearrange):
                parts = self.call(rearrange, classes, parts)
            elif isinstance(rearrange, str):
                parts = (rearrange,)
            elif rearrange is not None:
                parts = rearrange

        before_acc = []
        for before in props.get(":before", ()):
            if callable(before):
                before_acc = list(self.call(before, classes, parts)) + before_acc
            if isinstance(before, str):
                before_acc = [before] + before_acc

        after_acc = []
        for after in props.get(":after", ()):
            if callable(after):
                after_acc += list(self.call(after, classes, parts))
            if isinstance(after, str):
                after_acc += [after]

        if before_acc or after_acc:
            parts = itertools.chain(before_acc, parts, after_acc)

        return classes, parts

    def postmanipulate(self, classes, parts):

        props = self.get_properties(classes)

        joiner = props.get(":join", None)
        joiner = joiner[0] if joiner else "".join
        if isinstance(joiner, str):
            joiner = joiner.join

        s = joiner(parts)

        for wrapper in props.get(":wrap", ()):
            s = wrapper(s)

        return s


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


