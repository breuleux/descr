
import sys
from ..format import Layout
from .core import HTMLRuleBuilder
from ..rulesets import basic


html_boxy = Layout()

html_boxy.layout = dict(

    open = basic + HTMLRuleBuilder(

        # Note that a class declaration like ".toplevel" will be
        # inserted before every selector below, so that the rules'
        # effect cannot "leak" outside of what we are displaying.  So
        # in effect, "" -> ".toplevel", ".{@str} > span" ->
        # ".toplevel .{@str} > span", and so on.

        # The following will therefore match the top level span:

        ("", {"display": "block"}),

        # And this will match all spans inside that:
        ("span", {"display": "inline-block",
                  "vertical-align": "middle",
                  "font-family": "monospace"}),

        # Text must flow.
        (".{text} span", {"display": "inline"}),

        (".{scalar}", {"text-align": "center",
                       "padding": "3px",
                       "margin": "3px"}),
        (".{empty}.{@str}::before", {"content": '"\\"\\""'}),

        (".{sequence}", {"padding": "3px",
                         "margin": "3px"}),
                         # ":before": lambda c, d: (({"raw"}, "&#x2205;"),) if not d else ()}),
        (".{empty}.{sequence}::before", {"content": '"\\2205"'}),
        (".{empty}.{sequence}", {"border": "0px"}),

        (".{assoc}", {":join": '<span class="assoc_separator"></span>',
                      "margin": "3px",
                      # Whitespace before "display" is a trick to have
                      # several entries for it in the CSS (since
                      # whitespace is significant here but not in the
                      # stylesheet). firefox and webkit will only see
                      # this property when prefixed with -moz- or
                      # -webkit-
                      "display": "inline-box",
                      " display": "-moz-inline-box",
                      "  display": "-webkit-inline-box",
                      "-webkit-box-align": "middle",
                      "-webkit-box-orient": "vertical",
                      "-moz-box-align": "middle",
                      "-moz-box-orient": "vertical",
                      "box-align": "middle",
                      "box-orient": "vertical",
                      }),
        (".{assoc} > span", {"display": "block",
                             "margin": "0px"}),

        ),

    close = HTMLRuleBuilder(
        (".{bold}", {"font-weight": "bold"}),
        (".{black}", {"color": "#000"}),
        (".{red}", {"color": "#f88"}),
        (".{green}", {"color": "#8f8"}),
        (".{yellow}", {"color": "#ff8"}),
        (".{blue}", {"color": "#88f"}),
        (".{magenta}", {"color": "#f8f"}),
        (".{cyan}", {"color": "#8ff"}),
        (".{white}", {"color": "#fff"}),

        (".{par}", {":wrap": lambda x: "<p>%s</p>" % x}),
        (".{line}", {":after": [[{"raw"}, "<br/>"]]}),
        (".{raw}", {":raw": True}),
        ))


html_boxy.styles["dark"] = dict(
    open = HTMLRuleBuilder(

        (".{scalar}", {"background-color": "#222"}),
        (".{@True}", {"color": "#5f5"}),
        (".{@False}", {"color": "#f55"}),
        (".{@None}", {"color": "#a88"}),
        (".{@int}", {"color": "#88f"}),
        (".{@str}", {"color": "#f88"}),
        (".{empty}", {"color": "#888"}),

        (".{sequence}", {"border": "2px solid #222",
                         "border-bottom": "2px solid #888"}),
        (".{fieldlist}", {"border-bottom": "2px solid #88f"}),

        (".{assoc_separator}", { "border": "2px solid #fff"}),

        (".{objectlabel}", {"color": "#88f", "font-weight": "bold", ":+classes": "scalar"}),
        (".{objectlabel} + .{assoc_separator}", { "border": "2px solid #88f"}),
        (".{fieldlabel}", {"color": "#f88", ":+classes": "scalar"}),

        ),
    close = HTMLRuleBuilder(
        (".{hl}", {"font-weight": "bold"}),
        (".{hl1}", {"color": "#88f", "font-weight": "bold"}),
        (".{hl2}", {"color": "#8f8", "font-weight": "bold"}),
        (".{hl3}", {"color": "#ff8", "font-weight": "bold"}),
        (".{hlE}", {"color": "#f88", "font-weight": "bold"}),
        ))


html_boxy.styles["light"] = dict(
    open = HTMLRuleBuilder(

        (".{scalar}", {"background-color": "#eee"}),
        (".{@True}", {"color": "#080"}),
        (".{@False}", {"color": "#f00"}),
        (".{@None}", {"color": "#555"}),
        (".{@int}", {"color": "#00a"}),
        (".{@str}", {"color": "#a00"}),
        (".{empty}", {"color": "#888"}),

        (".{sequence}", {"border": "2px solid #eee"}),
        (".{sequence} > .{sequence}", {"border-bottom": "2px solid #"}),

        (".{assoc_separator}", {"border": "2px solid #000"}),

        (".{objectlabel}", {"color": "#00f", "font-weight": "bold", ":+classes": "scalar"}),
        (".{objectlabel} + .{assoc_separator}", { "border": "2px solid #00f"}),
        (".{fieldlabel}", {"color": "#a00", ":+classes": "scalar"}),

        ),
    close = HTMLRuleBuilder(
        (".{hl}", {"font-weight": "bold"}),
        (".{hl1}", {"color": "#00f", "font-weight": "bold"}),
        (".{hl2}", {"color": "#0a0", "font-weight": "bold"}),
        (".{hl3}", {"color": "#a60", "font-weight": "bold"}),
        (".{hlE}", {"color": "#f00", "font-weight": "bold"}),
        )
    )
