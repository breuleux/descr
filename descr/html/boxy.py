
import sys
from ..format import Layout
from .core import HTMLRuleBuilder, HTMLNode, make_joiner
from ..rulesets import basic


html_boxy = Layout()

html_boxy.layout = dict(

    # Note: the classes "scalar", "sequence" and "empty" are added by
    # rules in descr.ruleset.basic, so make sure to include that
    # ruleset if you want to make your own layout with rules based on
    # these classes.

    # When the layout is applied, we add the rulesets open + close, so
    # that rules can be added to open without overriding those in
    # close. For instance classes meant for highlighting will be in
    # close so that they get priority over all the others.

    open = basic + HTMLRuleBuilder(

        # Note: a class declaration like ".toplevel" will be
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

        # For text.
        (".{text} *", {"display": "inline"}),
        (".{pre} *", {"display": "inline",
                      "white-space": "pre"
                      }),

        # scalar = @str, @int, @True, @False, ...
        (".{scalar}", {"white-space": "pre",
                       "padding": "3px",
                       "margin": "3px",
                       "max-height": "300px",
                       "overflow": "auto"
                       }),
        # we add a double quote "" before an empty string
        (".{empty}.{@str}::before", {"content": '"\\"\\""'}),

        (".{sequence}", {"padding": "3px",
                         "margin": "3px"}),
        # For empty strings we insert the symbol for an empty set and
        # we remove borders. If you wish to differentiate types of
        # sequences visually using borders, including empty ones, you
        # might need to disable the second rule, for example:
        # (".empty.sequence", {"!clear": True})
        (".{empty}.{sequence}::before", {"content": '"\\2205"'}),
        # (".{empty}.{sequence}", {"border": "0px"}),

        (".stack", {
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
                "-moz-box-align": "middle",
                "box-align": "middle",
                "-webkit-box-orient": "horizontal",
                "-moz-box-orient": "horizontal",
                "box-orient": "horizontal",
                }),

        (".vstack", {
                ":+classes": "stack",
                "-webkit-box-orient": "vertical",
                "-moz-box-orient": "vertical",
                "box-orient": "vertical",
                }),

        (".hstack", {
                ":+classes": "stack",
                "-webkit-box-orient": "horizontal",
                "-moz-box-orient": "horizontal",
                "box-orient": "horizontal",
                }),

        (".{stack} > span", {"display": "block",
                             "margin": "0px",
                             # "width": "100%"
                             }),


        # Note: to display key/value pairs horizontally you can change
        # vstack to hstack. You might have to add a :-classes
        # instruction to remove vstack if you try to do it
        # programmatically.
        (".{assoc}", {":join": make_joiner(HTMLNode({"assoc_separator"}, [])),
                      ":+classes": "vstack",
                      }),

        # Rules related to printing tracebacks

        (".{@traceback}", {":+classes": "vstack",
                           ":join": make_joiner(HTMLNode({"traceback_separator"}, []))}),
        (".{@traceback} > *", {"display": "block"}),

        (".source_excerpt", {":+classes": "vstack",
                             "width": "100%"
                             }),
        (".source_excerpt > *", {"display": "block"}),

        (".source_header", {"width": "98%"}),
                            
        (".source_header > .path, .source_header > .source_loc",
         {"display": "block", "float": "right"}),

        (".path, .source_loc, .{@frame} > .{+fname}", {":+classes": "scalar"}),

        (".{+fname} + .path::before", {"content": '"in "'}),
        (".path + .source_loc::before", {"content": '"@"',
                                         "font-weight": "normal"}),

        (".{source_code}", {":+classes": "pre"}),

        (".lineno", {"padding-right": "5px",
                     "margin-right": "10px",
                     "display": "inline-block",
                     "text-align": "right"}),

        # Quoting

        (".quote.class_set > *", {"margin-left": "3px", "margin-right": "3px"}),
        (".quote.class_set", {"padding": "3px", "margin": "3px"}),
        (".quote.description", {"padding": "3px", "margin": "3px"}),

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

        (".{hl}", {"font-weight": "bold"}),
        (".{hl1}", {"font-weight": "bold"}),
        (".{hl2}", {"font-weight": "bold"}),
        (".{hl3}", {"font-weight": "bold"}),
        (".{hlE}", {"font-weight": "bold"}),

        (".{par}", {":wrap": lambda x: HTMLNode({}, [x], tag = p)}),
        (".{line}", {":after": lambda a, b: [[{"raw"}, "<br/>"]]}),
        (".{raw}", {":raw": True}),
        ))


# Rules for a "dark" theme (a black, or nearly black background is assumed).

html_boxy.styles["dark"] = dict(
    open = HTMLRuleBuilder(

        (".{scalar}", {"background-color": "#222"}),
        (".{@True}", {"color": "#5f5"}),
        (".{@False}", {"color": "#f55"}),
        (".{@None}", {"color": "#a88"}),
        (".{@int}", {"color": "#88f"}),
        (".{@float}", {"color": "#88f"}),
        (".{@complex}", {"color": "#88f"}),
        (".{@str}", {"color": "#f88"}),
        (".{empty}", {"color": "#888"}),

        (".{sequence}", {"border": "2px solid #222"}),
        (".{empty}.{sequence}", {"border": "2px solid #000"}),
        (".{@tuple}:hover", {"border": "2px solid #888"}),
        (".{@list}:hover", {"border": "2px solid #a44"}),
        (".{@dict}:hover", {"border": "2px solid #484"}),
        (".{@set}:hover", {"border": "2px solid #44a"}),

        (".{fieldlist}", {"border-bottom": "2px solid #88f"}),

        (".assoc:hover .assoc_separator", {"border": "2px solid #fff"}),
        (".{assoc_separator}", { "border": "2px solid #888"}),

        (".{objectlabel}", {"color": "#88f", "font-weight": "bold", ":+classes": "scalar"}),
        (".{objectlabel} + .{assoc_separator}", { "border": "2px solid #88f"}),
        (".{fieldlabel}", {"color": "#f88", ":+classes": "scalar"}),

        # Traceback

        (".{@traceback}", {"border": "1px dashed #888"}),
        (".traceback_separator", {"border": "2px solid #888"}),
        (".source_header", {"background-color": "#222"}),
        (".{+fname} + .path::before", {"color": "#aaa"}),
        (".path + .source_loc::before", {"color": "#aaa"}),
        (".lineno", {"border-right": "4px solid #88f"}),

        (".{@Exception} .{objectlabel}", {"color": "#f00", "text-align": "left"}),
        (".{@Exception} .{objectlabel} + .{assoc_separator}", {"border": "2px solid #f88"}),
        (".{@Exception} .{fieldlist}", {"border-bottom": "4px solid #f88"}),
        (".exception_message", {"display": "block"}),

        # Quoting

        (".quote.class_set > *", {"background-color": "#222", "color": "blue"}),
        (".quote.class_set", {"border": "2px solid blue"}),
        (".quote.description", {"border": "2px solid #888"}),
        (".quote.description:hover", {"border": "2px solid #fff"}),

        # HTMLNode

        (".{@HTMLNode} > .{+classes}", {"background-color": "#222"}),
        (".{@HTMLNode} > .{+classes} > *", {"color": "#88f", "padding": "3px"}),

        ),
    close = HTMLRuleBuilder(
        (".{hl}", {"font-weight": "bold"}),
        (".{hl1}", {"color": "#ff8", "background-color": "#220"}),
        (".{hl2}", {"color": "#8f8", "background-color": "#020"}),
        (".{hl3}", {"color": "#88f", "background-color": "#003"}),
        (".{hlE}", {"color": "#f88", "background-color": "#300"}),

        (".hl.empty::before, .hl1.empty::before, .hl2.empty::before, .hl3.empty::before, .hlE.empty::before", {
                "content": '"\\25B6"',
                }),
        ))


# Rules for a "light" theme (a white, or nearly white background is assumed).

html_boxy.styles["light"] = dict(
    open = HTMLRuleBuilder(

        (".{scalar}", {"background-color": "#eee"}),
        (".{@True}", {"color": "#080"}),
        (".{@False}", {"color": "#f00"}),
        (".{@None}", {"color": "#555"}),
        (".{@int}", {"color": "#00a"}),
        (".{@float}", {"color": "#00a"}),
        (".{@complex}", {"color": "#00a"}),
        (".{@str}", {"color": "#a00"}),
        (".{empty}", {"color": "#888"}),

        (".{sequence}", {"border": "2px solid #eee"}),
        (".{empty}.{sequence}", {"border": "2px solid #fff"}),
        (".{@tuple}:hover", {"border": "2px solid #bbb"}),
        (".{@list}:hover", {"border": "2px solid #f88"}),
        (".{@dict}:hover", {"border": "2px solid #6a6"}),
        (".{@set}:hover", {"border": "2px solid #88f"}),

        (".{fieldlist}", {"border-bottom": "2px solid #00f"}),

        (".assoc:hover > .assoc_separator", {"border": "2px solid #000"}),
        (".{assoc_separator}", {"border": "2px solid #888"}),

        (".{objectlabel}", {"color": "#00f", "font-weight": "bold", ":+classes": "scalar"}),
        (".{objectlabel} + .{assoc_separator}", { "border": "2px solid #00f"}),
        (".{fieldlabel}", {"color": "#a00", ":+classes": "scalar"}),

        # Traceback

        (".{@traceback}", {"border": "1px dashed #888"}),
        (".traceback_separator", {"border": "2px solid #888"}),
        (".source_header", {"background-color": "#eee"}),
        (".{+fname} + .path::before", {"color": "#666"}),
        (".path + .source_loc::before", {"color": "#666"}),
        (".lineno", {"border-right": "4px solid #00f"}),

        (".{@Exception} .{objectlabel}", {"color": "#f00", "text-align": "left"}),
        (".{@Exception} .{objectlabel} + .{assoc_separator}", {"border": "2px solid #800"}),
        (".{@Exception} .{fieldlist}", {"border-bottom": "4px solid #800"}),
        (".exception_message", {"display": "block"}),

        # Quoting

        (".quote.class_set > *", {"background-color": "#eee", "color": "blue"}),
        (".quote.class_set", {"border": "2px solid blue"}),
        (".quote.description", {"border": "2px solid #aaa"}),
        (".quote.description:hover", {"border": "2px solid #000"}),

        # HTMLNode

        (".{@HTMLNode} > .{+classes}", {"background-color": "#eee"}),
        (".{@HTMLNode} > .{+classes} > *", {"color": "#00f", "padding": "3px"}),

        ),
    close = HTMLRuleBuilder(
        (".{hl}", {"font-weight": "bold"}),
        (".{hl1}", {"color": "#00f", "background-color": "#eef"}),
        (".{hl2}", {"color": "#0a0", "background-color": "#efe"}),
        (".{hl3}", {"color": "#a60", "background-color": "#efc"}),
        (".{hlE}", {"color": "#f00", "background-color": "#fee"}),
        )
    )
