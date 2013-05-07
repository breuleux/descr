
import sys, re
from ..rules import escape_selector, RuleTree, RuleTreeExplorer
from ..format import RuleBuilder, Formatter, descr, Printer, DescriptionProcessor
from ..html import make_joiner


textprops = dict(
    bold = 1,

    black = 30,
    red = 31,
    green = 32,
    yellow = 33,
    blue = 34,
    magenta = 35,
    cyan = 36,
    white = 37
    )


def extract_textprops(props):

    rval = list(props.get("textprops", []))

    bold = props.get("bold", False)
    if bold and bold[-1]:
        rval.append(1)

    color = props.get("color", False)
    if color:
        color = color[-1]
        if isinstance(color, str):
            rval.append(textprops[color])
        elif isinstance(color, int):
            rval.append(color)

    return rval


sgr = re.compile("(\x1b[^a-zA-Z]*m)")
sgr_end = "\x1b[0m"
def fix_sgr_nesting(s):
    # Control codes in a terminal do not nest. For instance, you can't
    # set the text color to red, then to blue, then pop blue off to
    # get back to red. This function tracks the various changes in
    # text properties and restores them every time they are "popped
    # off".
    stack = []
    strings = []
    sgrs = list(sgr.finditer(s))
    i = 0
    for m in sgrs:
        it = m.groups()[0]
        start, end = m.span()
        strings.append(s[i:start])
        i = end
        strings.append(it)
        if it == sgr_end:
            if stack:
                stack.pop()
            strings += stack
        else:
            stack.append(it)
    strings.append(s[i:])
    return "".join(strings)


# def get_widths(node):
#     if isinstance(node, str):
#         return [len(node)]
#     return node.widths()

def convert(node):
    if isinstance(node, str):
        return [node]
    return node.convert()




class Join(object):

    def __init__(self, begin, join, end, indent = True):
        self.begin = begin.split("\n")
        self.join = join.split("\n")
        self.end = end.split("\n")
        self.indent = indent

        # self.begin_widths = list(map(len, self.begin))
        # self.join_widths = list(map(len, self.join))
        # self.end_widths = list(map(len, self.end))

    # def widths(self, children):
    #     groups = [self.begin_widths]
    #     for child in children[:-1]:
    #         groups.append(get_widths(child))
    #         groups.append(self.join_widths)
    #     groups.append(get_widths(children[-1]))
    #     groups.append(self.end_widths)
    #     widths = [0]
    #     for new_widths in groups:
    #         widths[-1] += new_widths[0]
    #         widths += new_widths[1:]
    #     return widths

    def convert(self, children):
        children = children or [""]
        groups = [(True, self.begin)]
        for child in children[:-1]:
            groups.append((False, convert(child)))
            groups.append((True, self.join))
        groups.append((False, convert(children[-1])))
        groups.append((True, self.end))
        indent = 0
        lines = [""]
        for special, new_lines in groups:
            if special:
                indent = 0
            lines[-1] += new_lines[0]
            lines.extend(" " * indent + line for line in new_lines[1:])
            if self.indent:
                indent = len(lines[-1])
        return lines



class Concat(object):

    # def widths(self, children):
    #     widths = [0]
    #     for child in children:
    #         new_widths = get_widths(child)
    #         widths[-1] += new_widths[0]
    #         widths += new_widths[1:]
    #     return widths

    def convert(self, children):
        lines = [""]
        for child in children:
            cvt = convert(child)
            lines[-1] += cvt[0]
            lines.extend(cvt[1:])
        return lines


class ConcatIndent(object):

    # def widths(self, children):
    #     widths = [0]
    #     indent = 0
    #     for child in children:
    #         new_widths = get_widths(child)
    #         widths[-1] += new_widths[0]
    #         widths += [width + indent for width in new_widths[1:]]
    #         indent = widths[-1]
    #     return widths

    def convert(self, children):
        indent = 0
        lines = [""]
        for child in children:
            cvt = convert(child)
            lines[-1] += cvt[0]
            lines.extend(" " * indent + line for line in cvt[1:])
            indent = len(lines[-1])
        return lines

class Lines(object):

    def __init__(self, trail = True):
        self.trail = trail

    # def widths(self, children):
    #     rval = sum((get_widths(child) for child in children), [])
    #     if self.trail:
    #         rval.append(0)
    #     return rval

    def convert(self, children):
        rval = sum(map(convert, children), [])
        if self.trail:
            rval.append("")
        return rval



class Indented(object):

    def __init__(self, start = 0, middle = 2, end = None):
        self.start = start
        self.middle = middle
        self.end = start if end is None else end

    # def widths(self, children):
    #     widths = []
    #     for child in children[:1]:
    #         widths += [w + self.start for w in get_widths(child)]
    #     if len(children) == 1:
    #         return widths
    #     for child in children[1:-1]:
    #         widths += [w + self.middle for w in get_widths(child)]
    #     for child in children[-1:]:
    #         widths += [w + self.end for w in get_widths(child)]
    #     return widths

    def convert(self, children):
        lines = []
        for child in children[:1]:
            lines += [" " * self.start + line for line in convert(child)]
        if len(children) == 1:
            return lines
        for child in children[1:-1]:
            lines += [" " * self.middle + line for line in convert(child)]
        for child in children[-1:]:
            lines += [" " * self.end + line for line in convert(child)]
        return lines

        



layouts = {
    "concat": Concat(),
    "concat-indent": ConcatIndent(),
    "lines": Lines,
    "indented": Indented
    }




class TextNode(object):

    def __init__(self, properties, children):
        layout = properties.get("layout", [Concat()])[-1]

        if isinstance(layout, str):
            name = layout
            layout = layouts[layout]
        else:
            name = None

        if isinstance(layout, type):
            name = (name or layout.name) + "-"
            ln = len(name)
            arguments = {k[ln:].replace("-", "_"): v[-1] for k, v in properties.items()
                         if k.startswith(name) and v}
            layout = layout(**arguments)

        self.layout = layout

        self.properties = properties
        self.children = children

    def widths(self):
        return self.layout.widths(self.children)

    def convert(self):
        lines = self.layout.convert(self.children)
        textprops = extract_textprops(self.properties)
        if textprops:
            prelude = "\x1B[%sm" % ";".join(map(str, textprops))
            lines[0] = prelude + lines[0]
            lines[-1] += "\x1B[0m"
        return lines

    def __len__(self):
        return self.length

    def __str__(self):
        # result = "".join(map(str, self.children))
        # textprops = extract_textprops(self.properties)
        result = "\n".join(self.convert())
        # if textprops:
        #     result = "\x1B[%sm%s\x1B[0m" % (";".join(map(str, textprops)), result)
        return result



def generate_text(description):
    if description is None or isinstance(description, (int, float, bool)):
        description = str(description)

    if isinstance(description, str):
        node = description
    else:
        props = description.properties

        children = [generate_text(child)
                    for child in description.children]

        for f in props.get(":textreplace", ()):
            props, children = f(props, children)
        for f in props.get(":join", ())[-1:]:
            children = f(props, children)
        for f in props.get(":wrap", ()):
            children = f(props, children)

        node = TextNode(props, children)

    return node



class TerminalFormatter(Formatter):

    def __init__(self, rules):
        self._rules = rules
        self.rules = RuleTree()
        self.add_rules(rules)

    def copy(self):
        return type(self)(self._rules)

    def add_rules(self, ruleset):
        for selector, props in ruleset.rules:
            selector = escape_selector(selector)
            self.rules.register(selector, props)

    def translate(self, stream):
        expl = RuleTreeExplorer({}, [(0, False, self.rules)])
        txt = generate_text(DescriptionProcessor.process(stream, expl))
        return fix_sgr_nesting(str(txt))


term = RuleBuilder()
# term.prop(".{@list}", "color", "cyan")
# term.prop(".{@list}", "bold", True)
# term.prop(".{@tuple}", "color", "red")

term.prop(".{@list}", "layout", Join("[\n  ", ",\n  ", "\n]", True))
term.prop(".{@tuple}", "layout", Join("(\n  ", ",\n  ", ",\n)", True))
term.prop(".{@dict}", "layout", Join("{\n  ", ",\n  ", "\n}", True))
term.prop(".{assoc}", "layout", Join("", ": ", "", False))

# term.prop(".{@list}", "layout", Join("[", ",\n ", "]", True))

# term.prop(".{@list} > *", ":textreplace",
#           lambda properties, children: (dict(properties, layout =  Concat()),
#                                         [TextNode(properties, children),
#                                          ","]))

# term.prop(".{@list}", ":textreplace",
#           lambda properties, children: (dict(properties, layout =  Concat()),
#                                         [TextNode(properties, children),
#                                          ","]))

# term.prop(".{@list}", ":rearrange",
#           lambda classes, children: [({"sequence_element"}, child, ",")
#                                      for child in children])

# term.prop(".sequence", ":join", make_joiner(", "))
# term.prop(".assoc", ":join", make_joiner(": "))

# term.prop(".{@list}", ":wrap", lambda classes, children: ["["] + children + ["]"])
# term.prop(".{@tuple}", ":wrap", lambda classes, children: ["("] + children + [")"])
# term.prop(".{@dict}", ":wrap", lambda classes, children: ["{"] + children + ["}"])
# term.prop(".{@set}", ":wrap", lambda classes, children: ["{"] + children + ["}"])
# term.prop(".{@frozenset}", ":wrap", lambda classes, children: ["{"] + children + ["}"])


def std_terminal(out = sys.stdout,
                 descr = descr,
                 rules = None,
                 layout = None):

    if layout is None:
        layout = term
    if rules is not None:
        layout += rules

    pr = Printer(out,
                 descr,
                 TerminalFormatter(layout))
    return pr

