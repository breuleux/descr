
import re

from collections import OrderedDict
from ..format import Formatter, exhaust_stream, RuleBuilder, DescriptionProcessor, descr
from ..rules import RuleTree, RuleTreeExplorer, custom_merge
from ..util import Assoc, Group, Raw

def generate_css(rules):
    blocks = []
    for selector, properties in rules.items():
        s = "%s {%s\n}" % (
            selector,
            "".join("\n    %s: %s;" % (prop, value)
                    for prop, value in sorted(properties.items())))
        blocks.append(s)
    return "\n\n".join(blocks)


def escape_selector(selector):
    def escape(m):
        s = m.groups()[0]
        s = "".join(("\\"+c if not c.isalnum() else c)
                    for c in s)
        return s

    return re.sub("\\{([^}]*)\\}", escape, selector)


def quotehtml(x):
    # TODO: other characters
    s = str(x)
    for orig, repl in [("&", "&amp;"),
                       ("<", "&lt;"),
                       (">", "&gt;"),
                       ('"', "&quot;")]:
        s = s.replace(orig, repl)
    return s


class HTMLNode(object):

    def __init__(self, classes, children, tag = "span"):
        self.tag = tag
        self.classes = classes
        self.children = children

    def copy(self):
        return HTMLNode(set(self.classes),
                        list(self.children),
                        self.tag)

    def __str__(self):
        return '<%s class="%s">%s</%s>' % (
            self.tag,
            " ".join(self.classes),
            "".join(map(str, self.children)),
            self.tag)

    # white-space: pre fucks this up
    # def __str__(self, indent = 0):
    #     return '%s<%s class="%s">\n%s\n%s</%s>' % (
    #         " " * indent,
    #         self.tag,
    #         " ".join(self.classes),
    #         "\n".join([child.__str__(indent + 2)
    #                    if isinstance(child, HTMLNode)
    #                    else str(child)
    #                    for child in self.children]),
    #         " " * indent,
    #         self.tag)

    def __descr__(self, recurse):
        classes = Group(map(Raw, sorted(self.classes)),
                        classes = {"field", "+classes"})
        children = Group(self.children,
                         classes = {"field", "+children"})

        if self.tag != "span":
            header = (self.tag, classes)
        elif self.classes:
            header = classes
        else:
            header = None

        if header:
            if self.children:
                proxy = Assoc(header, children, classes = {"@HTMLNode"})
            else:
                proxy = Group([header], classes = {"@HTMLNode"})
        else:
            proxy = Group([children], classes = {"@HTMLNode"})
        return recurse(proxy)


def generate_html(description, noinspect = False):
    if description is None or isinstance(description, (int, float, bool)):
        description = str(description)

    if isinstance(description, str):
        node = HTMLNode({}, [quotehtml(description)])
    else:
        props = description.properties
        inspect_this = False
        if not noinspect:
            # We check if we will inspect this node, and if
            # it is so, we block the attribute in recursive
            # calls
            for f in props.get(":inspect", ()):
                if f(description):
                    inspect_this = True
                    break

        children = [generate_html(child, inspect_this or noinspect)
                    for child in description.children]
        classes = description.classes

        for f in props.get(":htmlreplace", ()):
            classes, children = f(classes, children)
        for f in props.get(":join", ())[-1:]:
            children = f(classes, children)
        for f in props.get(":wrap", ()):
            children = f(classes, children)

        node = HTMLNode(classes, children)

        if inspect_this:
            return generate_html(
                description.process(descr(node), description.rules),
                # No inspection here
                True)

    return node



class HTMLFormatter(Formatter):

    __n = 0

    def __init__(self, rules, top = None, always_setup = False):
        self.id = HTMLFormatter.__n
        HTMLFormatter.__n += 1
        self._top = top
        if top is None:
            self.top = "pydescr" + str(self.id)
        else:
            self.top = top
        self.always_setup = always_setup

        self._rules = rules
        self.cssrules = OrderedDict()
        self.rules = RuleTree()
        self.css_rules_changed = False
        self.rules_changed = False
        self.add_rules(rules)

    __keep_top = object()
    def copy(self, top = __keep_top):
        if top is HTMLFormatter.__keep_top:
            top = self._top
        return type(self)(self._rules, top)

    def add_rules(self, ruleset):
        for selector, props in ruleset.rules:
            raw_selector = escape_selector(selector)
            if self.top:
                selector = ".%s %s" % (self.top, raw_selector)
            else:
                selector = raw_selector
            orig_css = self.cssrules.get(selector, {})
            css = {}
            other = {}
            for k, v in props.items():
                if k == "!override_priority" and v and selector in self.cssrules:
                    del self.cssrules[selector]
                elif k.startswith(":"):
                    other[k] = v
                else:
                    css[k] = v
            if css:
                self.css_rules_changed = True
            custom_merge(orig_css, css)
            if other:
                self.rules.register(selector, other)
            self.cssrules[selector] = orig_css

    def setup(self):
        s = '<style type="text/css">\n%s\n</style>' % generate_css(self.cssrules)
        return s

    def incremental_setup(self):
        if self.css_rules_changed or self.always_setup:
            self.css_rules_changed = False
            return self.setup()
        else:
            return ""

    def translate_no_setup(self, stream):
        if self.top:
            stream = ({self.top}, stream)
        expl = RuleTreeExplorer({}, [(0, False, self.rules)])
        html = generate_html(DescriptionProcessor.process(stream, expl))
        return str(html)

    def translate(self, stream):
        s = self.incremental_setup()
        s += self.translate_no_setup(stream)
        return s



class HTMLRuleBuilder(RuleBuilder):

    def hl(self, selector, when = None):
        self.pclasses(selector, {"hl"}, when)

    def hl1(self, selector, when = None):
        self.pclasses(selector, {"hl1"}, when)

    def hl2(self, selector, when = None):
        self.pclasses(selector, {"hl2"}, when)

    def hl3(self, selector, when = None):
        self.pclasses(selector, {"hl3"}, when)

    def hlE(self, selector, when = None):
        self.pclasses(selector, {"hlE"}, when)

    def htmlreplace(self, selector, value, f = None):
        return self.fprop(selector, ":htmlreplace", value, f, [])

    def join(self, selector, value, f = None):
        return self.fprop(selector, ":join", value, f, [])

    def wrap(self, selector, value, f = None):
        return self.fprop(selector, ":wrap", value, f, [])

    def __getattr__(self, attr):
        if attr.startswith("css_"):
            attribute = attr[4:].replace("_", "-")
            def f(selector, value):
                return self.rule(selector, {attribute: value})
            return f
        else:
            return RuleBuilder.__getattr__(self, attr)


def make_joiner(s):
    def join(classes, children):
        if not children:
            return children
        new_children = [children[0]]
        for child in children[1:]:
            new_children.append(s)
            new_children.append(child)
        return new_children
    return join
