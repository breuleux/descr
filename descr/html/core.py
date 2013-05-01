
import re

from collections import OrderedDict
from ..format import (
    SimpleRules, Formatter,
    exhaust_stream, custom_merge,
    extract_sole_class, RuleBuilder
    )
from ..rules import RuleTree, RuleTreeExplorer


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
                       (" ", "&nbsp;"),
                       ("<", "&lt;"),
                       (">", "&gt;"),
                       ('"', "&quot;")]:
        s = s.replace(orig, repl)
    return s


# def generate_html(description, rules):
#     if isinstance(description, str):
#         s = "<span>" + quotehtml(description) + "</span>"
#     else:
#         classes, parts = exhaust_stream(description)
#         classes, parts = rules.premanipulate(classes, parts)
#         props = rules.get_properties(classes)

#         if props.get(":raw", False):
#             strings = map(str, parts)
#         else:
#             strings = [generate_html(part, rules) for part in parts]

#         s = rules.postmanipulate(classes, strings)
#         s = "<span class='%s'>%s</span>" % (
#             " ".join(classes),
#             s)

#     return s



def generate_html(description, rules):
    if isinstance(description, str):
        s = "<span>" + quotehtml(description) + "</span>"
    else:
        classes, parts = exhaust_stream(description)
        rules = rules.explore(classes, parts)
        parts = rules.premanipulate(parts)

        # classes, parts = rules.(classes, parts)
        # props = rules.get_properties(classes)

        raw = rules.properties.get(":raw", False)
        if raw and raw[-1]:
            strings = map(str, parts)
        else:
            strings = [generate_html(part, rules) for part in parts]

        s = rules.postmanipulate(strings)
        s = "<span class='%s'>%s</span>" % (
            " ".join(rules.classes),
            s)

    return s



class HTMLFormatter(Formatter):

    def __init__(self, rules, top = None):
        self.cssrules = OrderedDict()
        self.top = top
        # self.rules = SimpleRules([])
        self.rules = RuleTree()
        self.assimilate_rules(rules)

    # def assimilate_rules(self, rules):
    #     for selector, props in rules:
    #         raw_selector = escape_selector(selector)
    #         if self.top:
    #             selector = ".%s %s" % (self.top, raw_selector)
    #         else:
    #             selector = raw_selector
    #         cls = False
    #         orig_css = self.cssrules.get(selector, {})
    #         css = {}
    #         other = {}
    #         for k, v in props.items():
    #             if k == "!override_priority" and v and selector in self.cssrules:
    #                 del self.cssrules[selector]
    #             elif k.startswith(":"):
    #                 if cls is False:
    #                     cls = extract_sole_class(raw_selector)
    #                 if cls is None:
    #                     raise Exception("Cannot define property '%s' for selector '%s'. "
    #                                     "Properties starting with ':' must be associated "
    #                                     "to a single class selector."
    #                                     % (k, raw_selector))
    #                 other[k] = v
    #             else:
    #                 css[k] = v
    #         custom_merge(orig_css, css)
    #         self.rules.assimilate_rules([(cls, other)])
    #         self.cssrules[selector] = orig_css

    def assimilate_rules(self, rules):
        for selector, props in rules:
            raw_selector = escape_selector(selector)
            if self.top:
                selector = ".%s %s" % (self.top, raw_selector)
            else:
                selector = raw_selector
            # cls = False
            orig_css = self.cssrules.get(selector, {})
            css = {}
            other = {}
            for k, v in props.items():
                if k == "!override_priority" and v and selector in self.cssrules:
                    del self.cssrules[selector]
                elif k.startswith(":"):
                    # if cls is False:
                    #     cls = extract_sole_class(raw_selector)
                    # if cls is None:
                    #     raise Exception("Cannot define property '%s' for selector '%s'. "
                    #                     "Properties starting with ':' must be associated "
                    #                     "to a single class selector."
                    #                     % (k, raw_selector))
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
        # html = generate_html(stream, self.rules)
        html = generate_html(stream, RuleTreeExplorer({}, [(0, False, self.rules)]))
        return html


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

