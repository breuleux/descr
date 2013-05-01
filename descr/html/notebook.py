
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

    def __init__(self, descr, formatter, setup_now = True, top = "pydescr"):
        super(NotebookPrinter, self).__init__(None, descr, formatter, setup_now, top)

    def setup(self):
        s = self.formatter.setup()
        # print(s)
        display_html(HTML(s))

    def write(self, stream):
        s = self.formatter.translate(stream)
        # print(s)
        display_html(HTML(s))



def boxy_notebook(descr = descr,
                  rules = None,
                  layout = None,
                  top = "pydescr"):

    if layout is None:
        layout = html_boxy["light"]
    if rules is not None:
        layout += rules
    pr = NotebookPrinter(descr, HTMLFormatter(layout.rules, top = top), top = top)
    return pr

