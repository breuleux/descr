
from . import location
from .format import RuleBuilder, exhaust_stream
from .highlight import highlight_lines


# Class enrichment functions. The return value is a set of classes to
# add upon meeting the conditions specified.

# Used with property ":+classes" on the appropriate selector.

def _check_empty_str(classes, parts):
    # We may display empty strings differently.
    # ({"@str"}, "") -> ({"@str", "empty"}, "")
    if parts[0] == "":
        return {"empty"}
    else:
        return {}

def _check_empty_sequence(classes, parts):
    # We may display empty sequences differently.
    # ({"sequence"},) -> ({"sequence", "empty"},)
    if parts:
        return {}
    else:
        return {"empty"}


# Functions to reorganize nodes with specific classes.

# Used with property ":replace" on the appropriate selector.

# Note: the return value of these functions must be a set of classes
# and a list of new children for the node. These children cannot
# contain sets.

def _pull_field(classes, parts):
    # Changes a field node into a node that will display its label
    # (any class that starts with "+") and its contents like a
    # key->value pair of a dict.

    # ({"field", "+somelabel", classes...}, parts...)
    # -> ({"assoc", classes...},
    #     ({fieldlabel}, "somelabel"),
    #     ({"field", "+somelabel"}, parts...))

    # Automatically applied to all fields that are the immediate
    # children of a node with class "fieldlist" (ctrl+f "_pull_field"
    # to see how it's done)

    pfield = [klass for klass in classes if klass.startswith("+")][0]
    field = pfield[1:]
    classes2 = classes - {"field", pfield}
    return ({"assoc"} | classes2,
            [({"fieldlabel"}, field),
             ({"field", pfield},) + tuple(parts)])


def _replace_object(classes, parts, fieldlist = True):
    # Transform a node with the "object" class so that its label,
    # which is a class of the form "+label", is displayed, without the
    # "+". If there is no label, the type name is used instead
    # (e.g. "@myobj") ad verbatim (with the "@"). Then the fields are
    # placed in a node with class "fieldlist" which will allow the
    # rule implemented in _pull_field to trigger.

    # ({"object", "+somelabel", classes...} parts...)
    # -> ({"objectlabel", classes...}, "somelabel") # if len(parts) == 0
    # -> ({"assoc"}, ({"objectlabel"}, "somelabel"),
    #                ({"fieldlist", "sequence"?}, parts...)) # otherwise
    # "sequence" is added as a class only if len(parts) > 1

    # Automatically applied to the class "object". (ctrl+f
    # "_replace_object" to see how it's done)

    blocker = "object:done"
    if blocker in classes:
        return classes, parts

    possible_names = [klass for klass in classes if klass.startswith("+")]
    if possible_names:
        name = possible_names[0][1:]
    else:
        name = [klass for klass in classes if klass.startswith("@")][0]

    classes2 = classes | {blocker}

    if not parts:
        return {"objectlabel"} | classes2, [name]
    else:
        flclasses = set()
        if fieldlist:
            flclasses.add("fieldlist")
        if len(parts) > 1:
            flclasses.add("sequence")
        return ({"assoc"} | classes2,
                [({"objectlabel"}, name),
                 (flclasses,) + tuple(parts)])


def _post_frame(classes, parts):
    # This is run after the children of a @frame object are processed
    # in order to squeeze the function name into the header with the
    # filename and line number. It's not very pretty.
    # fname and location are descr.format.DescriptionProcessor objects.
    fname, location = parts
    rval = location
    rval.children[0].children.insert(0, fname)
    return [rval]


def _extract_locations(classes, parts):
    # Does the dirty job of taking a file number and a few line and
    # column numbers, reading the file and formatting what they refer
    # to.

    # ({"location"}, filename, ((l1, c1)|startpos, (l2, c2)|endpos|None|"line"|"stripline")...)
    # ->
    # Something like this:
    # [[{'source_header'},
    #   ({'field', '+path', 'path'}, 'test.py'),
    #   ({'source_loc'}, {'hl1'}, '146:5-7')],
    #  [{'source_code'},
    #   ({'L#144', 'W#3', 'lineno'}, ''), (set(), '\n'), ({'L#145', 'W#3', 'lineno'}, ''), (set(), 'try:\n'), ({'W#3', 'L#146', 'lineno'}, ''), (set(), '    '), ({'hl1'}, 'f()'), (set(), '\n'), ({'W#3', 'L#147', 'lineno'}, ''), (set(), '    # pr.write(object())\n'), (set(), ''), ({'W#3', 'L#148', 'lineno'}, ''), 'except:']]

    blocker = "block:location"
    if blocker in classes:
        return classes, parts

    filename, specs = parts[0], parts[1:]

    ctx = 0
    for k in classes:
        if k.startswith("C#"):
            ctx = int(k[2:])

    try:
        f = open(filename)
        text = f.read()
        f.close()
    except IOError:
        return (classes,
                [[{'source_header'},
                  ({'field', '+path', 'path'}, filename),
                  ({'source_loc'}, {'hl1'}, "???")],
                 [{'source_code'}, "Could not read file."]])

    source = location.Source(text, filename)

    locs = []

    for spec in specs:
        classes1, (start, end) = exhaust_stream(spec)

        if isinstance(start, tuple):
            l1, c1 = start
            start = source.fromlinecol(l1, c1)
        else:
            l1, c1 = source.linecol(start)

        if end is None:
            end = start
        elif end == "line":
            line = source.lines[l1 - 1]
            end = start + len(line)
        elif end == "stripline":
            line = source.lines[l1 - 1]
            ll = len(line)
            end = start + len(line.rstrip())
            start = start + ll - len(line.lstrip())
        elif isinstance(end, tuple):
            end = source.fromlinecol(*end)

        loc = location.Location(source, (start, end))
        locs.append((loc, classes1))

    rval = location.descr_locations(locs, ctx)
    c, p = exhaust_stream(rval)
    return c | {blocker}, p


def _insert_lineno(c, d):
    n, width = "", 3
    for cls in c:
        if cls.startswith("L#"):
            n = cls[2:]
        elif cls.startswith("W#"):
            width = max(width, int(cls[2:]))
    return [n.rjust(width)]


basic = RuleBuilder(

    # Check for empty strings and containers
    (".{@str}, .{hl}, .{hl1}, .{hl2}, .{hl3}, .{hlE}", {":+classes": _check_empty_str}),
    (".{sequence}", {":+classes": _check_empty_sequence}),

    # Rules to pretty print objects a bit like dicts
    (".{object}", {":replace": _replace_object}),
    (".{fieldlist} > .{field}", {":replace": _pull_field}),

    # Location
    (".{@traceback}, .{@frame}", {":-classes": "object"}),
    (".{@frame}", {":post": _post_frame}),
    (".{location}", {":replace": _extract_locations,
                     ":-classes": "field"}),
    (".lineno", {":before": _insert_lineno}),
    )

