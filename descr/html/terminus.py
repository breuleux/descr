
import sys
from ..format import descr, Printer
from .core import HTMLFormatter, generate_html
from .boxy import html_boxy


class TerminusFormatter(HTMLFormatter):

    def wrapesc(self, x):
        if '\n' in x:
            return "\x1B[?0;7y{x}\a".format(x = x)
        else:
            return "\x1B[?0y{x}\n".format(x = x)

    def setup(self):

        lines = [self.wrapesc("+h")]
        for selector, properties in self.cssrules.items():
            s = self.wrapesc("/h style {selector} {{ {style} }}".format(
                    selector = selector,
                    style = "".join("%s: %s;" % (prop, value)
                                    for prop, value in sorted(properties.items()))))
            lines.append(s)

        return "".join(lines)

    def translate(self, stream):
        # html = generate_html(stream, self.rules)
        html = super(TerminusFormatter, self).translate(stream)
        return self.wrapesc(':h {x}'.format(x = html))


def boxy_terminus(out = sys.stdout,
                  descr = descr,
                  rules = None,
                  layout = None,
                  always_setup = False,
                  top = "pydescr"):

    if layout is None:
        layout = html_boxy["dark"]
    if rules is not None:
         layout += rules
    Pr = AlwaysSetupPrinter if always_setup else Printer
    pr = Pr(out, descr, TerminusFormatter(layout.rules, top = top), top = top)
    return pr

