
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
    # -> ({"assoc"}, ({fieldlabel}, "somelabel"), ({classes...}, parts...))

    # Automatically applied to all fields that are the immediate
    # children of a node with class "fieldlist" (ctrl+f "_pull_field"
    # to see how it's done)
    blocker = "block:field"
    if blocker in classes:
        return classes, parts

    field = [klass for klass in classes if klass.startswith("+")][0][1:]
    classes2 = (classes - {"field"}) | {blocker}
    # return [({"assoc"},
    #          ({"fieldlabel"}, field),
    #          (classes2,) + tuple(parts))]
    return ({"assoc"} | classes2,
            [({"fieldlabel"}, field),
             ({"field", "+"+field},) + tuple(parts)])

# def _rearrange_object(classes, parts, fieldlist = True):
#     # Transform a node with the "object" class so that its label,
#     # which is a class of the form "+label", is displayed, without the
#     # "+". If there is no label, the type name is used instead
#     # (e.g. "@myobj") ad verbatim (with the "@"). Then the fields are
#     # placed in a node with class "fieldlist" which will allow the
#     # rule implemented in _pull_field to trigger.

#     # ({"object", "+somelabel", classes...} parts...)
#     # -> ({"objectlabel"}, "somelabel") # if len(parts) == 0
#     # -> ({"assoc"}, ({"objectlabel"}, "somelabel"),
#     #                ({"fieldlist", "sequence"?, classes...}, parts...)) # otherwise
#     # "sequence" is added as a class only if len(parts) > 1

#     # Automatically applied to the class "object". (ctrl+f
#     # "_rearrange_object" to see how it's done)

#     possible_names = [klass for klass in classes if klass.startswith("+")]
#     if possible_names:
#         name = possible_names[0][1:]
#     else:
#         name = [klass for klass in classes if klass.startswith("@")][0]

#     classes2 = classes.difference({"object"})
#     if fieldlist:
#         classes2.add("fieldlist")
#     if len(parts) > 1:
#         classes2.add("sequence")

#     if not parts:
#         return [({"objectlabel"}, name)]
#     else:
#         return [({"assoc"},
#                  ({"objectlabel"}, name),
#                  (classes2, )
#                  + tuple(parts))]


def _replace_object(classes, parts, fieldlist = True):
    # Transform a node with the "object" class so that its label,
    # which is a class of the form "+label", is displayed, without the
    # "+". If there is no label, the type name is used instead
    # (e.g. "@myobj") ad verbatim (with the "@"). Then the fields are
    # placed in a node with class "fieldlist" which will allow the
    # rule implemented in _pull_field to trigger.

    # ({"object", "+somelabel", classes...} parts...)
    # -> ({"objectlabel"}, "somelabel") # if len(parts) == 0
    # -> ({"assoc"}, ({"objectlabel"}, "somelabel"),
    #                ({"fieldlist", "sequence"?, classes...}, parts...)) # otherwise
    # "sequence" is added as a class only if len(parts) > 1

    # Automatically applied to the class "object". (ctrl+f
    # "_replace_object" to see how it's done)

    blocker = "block:object"
    if blocker in classes:
        return classes, parts

    possible_names = [klass for klass in classes if klass.startswith("+")]
    if possible_names:
        name = possible_names[0][1:]
    else:
        name = [klass for klass in classes if klass.startswith("@")][0]

    classes2 = (classes - {"object"}) | {blocker}

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
    fname, location = parts
    rval = location
    rval.children[0].children.insert(0, fname)
    return [rval]



def _extract_locations(classes, parts):

    blocker = "block:location"
    if blocker in classes:
        return classes, parts

    filename, *specs = parts

    ctx = 0
    for k in classes:
        if k.startswith("C#"):
            ctx = int(k[2:])

    try:
        with open(filename) as f:
            text = f.read()
    except IOError:
        raise
        return classes, ["Could not read file."]
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
    # c |= {"location", blocker}
    # c |= classes
    # print(c)
    return c | {blocker}, p



# def _extract_location(classes, parts):
#     filename, (start, end) = parts
#     if end is not None:
#         raise Exception

#     ctx = 0
#     for k in classes:
#         if k.startswith("C#"):
#             ctx = int(k[2:])

#     l1, c1 = start

#     try:
#         with open(filename) as f:
#             text = f.read()
#     except IOError:
#         return ["Could not read file."]

#     source = location.Source(text, filename)
#     pos = source.fromlinecol(l1, c1)
#     line = source.lines[l1 - 1]
#     ll = len(line)
#     loc = location.Location(source, (pos + ll - len(line.strip()),
#                                      pos + ll))
#     return [location.descr_locations([(loc, {"hl1"})], 3)]



basic = RuleBuilder(

    # booleans, integers, strings, etc. will be supplemented wtih the
    # class "scalar", which is a sort of shortcut to apply the same
    # style to all of them and allowing extensions to do the same.
    (".{@True}, .{@False}, .{@None}, .{@int}, .{@str}",
     {":+classes": "scalar"}),
    
    # Ditto for "sequence":
    (".{@list}, .{@tuple}, .{@dict}, .{@set}",
     {":+classes": "sequence"}),

    # Check for empty strings and containers
    (".{@str}, .{hl}, .{hl1}, .{hl2}, .{hl3}, .{hlE}", {":+classes": _check_empty_str}),
    (".{sequence}", {":+classes": _check_empty_sequence}),

    # Rules to pretty print objects a bit like dicts
    (".{object}", {":replace": _replace_object}),
    (".{fieldlist} > .{field}", {":replace": _pull_field}),

    # Location
    (".{@frame}", {":-classes": "object",
                   ":post": _post_frame}),

    # (".{location}", {":rearrange": _extract_locations,
    #                  ":-classes": "field"}),
    (".{location}", {":replace": _extract_locations,
                     ":-classes": "field"}),

    (".{source_code}", {":+classes": "pre"}),


    )

