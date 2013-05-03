
import re

from collections import OrderedDict
from ..format import Formatter, exhaust_stream, RuleBuilder, DescriptionProcessor
from ..rules import RuleTree, RuleTreeExplorer, custom_merge


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



def generate_html(description):
    if description is None or isinstance(description, (int, float, bool)):
        description = str(description)

    if isinstance(description, str):
        node = HTMLNode({}, [quotehtml(description)])
    else:
        nodes = [generate_html(child)
                   for child in description.children]
        node = HTMLNode(description.classes, nodes)
        props = description.properties
        for f in props.get(":shuffle", ()):
            node = f(node)
        for f in props.get(":join", ()):
            node = f(node)
        for f in props.get(":wrap", ()):
            node = f(node)

    return node




# def generate_html(description, rules):
#     if description is None or isinstance(description, (int, float, bool)):
#         description = str(description)

#     if isinstance(description, str):
#         # s = "<span>" + quotehtml(description) + "</span>"
#         s = HTMLNode({}, [quotehtml(description)])
#     else:
#         classes, parts = exhaust_stream(description)
#         rules = rules.explore(classes, parts)
#         parts = rules.premanipulate(parts)

#         raw = rules.properties.get(":raw", False)
#         if raw and raw[-1]:
#             children = map(str, parts)
#         else:
#             children = [generate_html(part, rules) for part in parts]

#         # children = rules.postmanipulate(rules.classes, children)
#         s = HTMLNode(rules.classes, children)
#         s = rules.postmanipulate(s)

#         # s = rules.postmanipulate(strings)
#         # s = "<span class='%s'>%s</span>" % (
#         #     " ".join(rules.classes),
#         #     s)

#     return s



class HTMLFormatter(Formatter):

    def __init__(self, rules, top = None):
        self.cssrules = OrderedDict()
        self.top = top
        self.rules = RuleTree()
        self.assimilate_rules(rules)

    def assimilate_rules(self, rules):
        for selector, props in rules:
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
            custom_merge(orig_css, css)
            if other:
                self.rules.register(selector, other)
            self.cssrules[selector] = orig_css

    def setup(self):
        s = '<style type="text/css">\n%s\n</style>' % generate_css(self.cssrules)
        return s

    def translate(self, stream):
        # html = generate_html(stream, RuleTreeExplorer({}, [(0, False, self.rules)]))
        html = generate_html(DescriptionProcessor.process(stream,
                                                          RuleTreeExplorer({}, [(0, False, self.rules)])))
        return str(html)


class HTMLRuleBuilder(RuleBuilder):

    def hl(self, selector, when = None):
        hlc = frozenset({"hl"})
        if when:
            f = lambda *p: hlc if when(*p) else {}
        else:
            f = hlc
        return self.rule(selector, {":+classes": f})

    def __getattr__(self, attr):
        if attr.startswith("css_"):
            attribute = attr[4:].replace("_", "-")
            def f(selector, value):
                return self.rule(selector, {attribute: value})
            return f
        else:
            return getattr(super(HTMLRuleBuilder, self), attr)


def make_joiner(s):
    def join(node):
        if not node.children:
            return node
        children = [node.children[0]]
        for child in node.children[1:]:
            children.append(s)
            children.append(child)
        node.children = children
        return HTMLNode(node.classes, children, node.tag)
    return join
