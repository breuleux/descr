
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
        (".{scalar}", {"text-align": "center",
                       "padding": "3px",
                       "margin": "3px"}),
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
        (".{empty}.{sequence}", {"border": "0px"}),


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

        (".{@traceback}", {":+classes": "vstack",
                # "display": "inline-box",
                # " display": "-moz-inline-box",
                # "  display": "-webkit-inline-box",
                # "-webkit-box-align": "middle",
                # "-moz-box-align": "middle",
                # "box-align": "middle",
                # "-webkit-box-orient": "horizontal",
                # "-moz-box-orient": "horizontal",
                # "box-orient": "horizontal",
                # ":+classes": "stack",
                # "-webkit-box-orient": "vertical",
                # "-moz-box-orient": "vertical",
                # "box-orient": "vertical",
                           # "border": "10px solid red"
                           }),

        (".{@traceback} > *", {"display": "block",
                           # "border": "10px solid green"
                               }),

        # (".{@traceback} > * > *", {"display": "block",
        #                    # "border": "10px solid blue"
        #                            }),


        (".source_excerpt", {":+classes": "vstack",
                             "width": "100%"}),
        (".source_excerpt > *", {"display": "block"}),

        # # (".source_header", {":+classes": "hstack"}),
        (".source_header", {#"display": "inline-block",
                            "width": "98%",
                            "background-color": "#222",
                            }),
        (".source_header > .path, .source_header > .source_loc",
         {"display": "block", "float": "right"}),

        (".squash", {"border": "2px solid #888"}),
 
        (".{@traceback}", {":join": make_joiner(HTMLNode({"squash"}, [])),
                           "border": "1px dashed #888"}),
        # (".source_excerpt", {"border": "2px solid #444"}),
        # (".source_header", {"border-bottom": "1px solid #888"}),

        (".{@frame} > .{+fname}", {":+classes": "scalar"}),
        (".path, .source_loc, .source_header > .{+fname}", {":+classes": "scalar"}),
        (".source_header > .{+fname}", {":+classes": "hl"}),
        (".path", {"color": "#fff"}),
        (".{+fname} + .path::before", {"content": '"in "',
                                       "color": "#aaa"}),
        (".path + .source_loc::before", {"content": '"@"',
                                         "color": "#aaa",
                                         "font-weight": "normal"}),

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
        (".{hl1}", {"color": "#ff8", "background-color": "#220", "font-weight": "bold"}),
        (".{hl2}", {"color": "#8f8", "background-color": "#020", "font-weight": "bold"}),
        (".{hl3}", {"color": "#88f", "background-color": "#004", "font-weight": "bold"}),
        (".{hlE}", {"color": "#f88", "font-weight": "bold"}),

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
        (".{@str}", {"color": "#a00"}),
        (".{empty}", {"color": "#888"}),

        (".{sequence}", {"border": "2px solid #eee",
                         "border-bottom": "2px solid #888"}),
        (".{fieldlist}", {"border-bottom": "2px solid #00f"}),

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
