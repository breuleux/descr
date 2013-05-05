
from .boxy import html_boxy
from .core import HTMLFormatter
from ..format import Printer, descr


def ierr(msg):
    def f(*args):
        raise ImportError(msg)
    return f

try:
    from IPython.core.display import HTML, display_html
except ImportError:
    HTML = ierr("Could not import HTML from IPython.core.display")
    display_html = ierr("Could not import display_html from IPython.core.display")


class NotebookPrinter(Printer):

    def __init__(self, descr, formatter):
        super(NotebookPrinter, self).__init__(None, descr, formatter)

    def write(self, stream, rules = None):
        s = self.translate(stream, rules)
        display_html(HTML(s))



def boxy_notebook(descr = descr,
                  rules = None,
                  layout = None,
                  top = None,
                  always_setup = False):

    if layout is None:
        layout = html_boxy["light"]
    if rules is not None:
        layout += rules
    pr = NotebookPrinter(descr, HTMLFormatter(layout, top = top,
                                              always_setup = always_setup))
    return pr

