
from bisect import bisect_right
from functools import reduce
from .highlight import highlight_lines


class Source(object):

    def __init__(self, text, url = None):
        self.url = url
        self.lines = text.split("\n")
        self.linepos = [0]
        i = 0
        for line in self.lines:
            i += len(line) + 1
            self.linepos.append(i)

    def linecol(self, pos):
        if 0 <= pos < self.linepos[-1]:
            line = bisect_right(self.linepos, pos) - 1
            return (line + 1, pos - self.linepos[line] + 1)
        else:
            raise IndexError(dict(pos = pos, source = self))

    def fromlinecol(self, line, col):
        line -= 1
        col -= 1
        if line >= len(self.lines):
            raise IndexError(dict(line = line, col = col, source = self))
        text = self.lines[line]
        if col > len(text):
            raise IndexError(dict(line = line, col = col, source = self))
        return self.linepos[line] + col


def linecolstr(start, end):
    (l1, c1), lc2 = start, end
    if lc2 is not None:
        l2, c2 = lc2
    if lc2 is None or l1 == l2 and c1 == c2:
        return ("%s:%s" % (l1, c1)) + ("<" if lc2 is None else "")
    elif l1 == l2:
        return "%s:%s-%s" % (l1, c1, c2)
    else:
        return "%s:%s-%s:%s" % (l1, c1, l2, c2)


class Location(object):
    """
    Location object - meant to represent some code excerpt. It
    contains a pointer to the source and a (start, end) tuple
    representing the extent of the excerpt in the source.

    Methods are provided to get line/columns for the excerpt, raw or
    formatted.
    """
    def __init__(self, source, span, tokens = []):
        self.source = source
        self.span = span
        self.start = span[0]
        self.end = span[1]
        self.tokens = tokens
        self._linecol = None

    def __len__(self):
        return self.span[1] - self.span[0]

    def linecol(self):

        def helper(source, start, end, promote_zerolength = False):
            end -= 1 # end position is now inclusive
            l1, c1 = source.linecol(start)
            if start > end:
                return ((l1, c1), (l1, c1) if promote_zerolength else None)
            l2, c2 = source.linecol(end)
            return ((l1, c1), (l2, c2))

        if self._linecol is not None:
            return self._linecol

        self._linecol = helper(self.source, self.start, self.end)
        return self._linecol

    def ref(self):
        """
        Returns a string representing the location of the excerpt. If
        the excerpt is only one character, it will format the location
        as "line:column". If it is on a single line, the format will
        be "line:colstart-colend". Else,
        "linestart:colstart-lineend:colend". In the special case where
        the excerpt is a token not in the source text (e.g. one that
        was inserted by the parser), "<" will be appended to the end.
        """
        lc1, lc2 = self.linecol()
        return linecolstr(lc1, lc2)

    def __descr__(self):
        return descr_locations([self])

    def at_start(self):
        return Location(self.source, (self.start, self.start))

    def at_end(self):
        return Location(self.source, (self.end, self.end))

    def __add__(self, loc):
        return merge_locations([self, loc])

    def __radd__(self, loc):
        return merge_locations([loc, self])

    def __gt__(self, loc):
        return loc.start < self.start

    def __lt__(self, loc):
        return loc.start > self.start

    def __ge__(self, loc):
        return loc.start <= self.start

    def __le__(self, loc):
        return loc.start >= self.start

    def __str__(self):
        return self.ref()

    def __repr__(self):
        return self.ref()


def descr_locations(specs, context = None):

    aggregate = merge_locations([l for l, _ in specs])
    source = aggregate.source

    header = [{"source_header"},
              ({"path", "+path", "field"}, source.url or "<string>")]
    header += [({"source_loc"}, hl, l.ref()) for l, hl in specs]

    if context is None or context < 0:
        return [{"source_excerpt"}, header, []]
    else:
        locations = []
        for loc, hl in specs:
            locations.append((loc.start, loc.end, hl))

    (l1, c1), end = aggregate.linecol()
    (l2, c2) = end or (l1, c1)
    l1 -= 1
    l2 -= 1
    c1 -= 1
    c2 -= 1
    l1 = max(l1 - context, 0)
    l2 = min(l2 + context + 1, len(source.lines))

    hl = [{"source_code"}]
    hl += highlight_lines(source.lines[l1:l2],
                          locations,
                          l1 + 1, source.linepos[l1])

    return [{"source_excerpt"}, header, hl]


def merge_locations(locations):
    """
    Handy function to merge *contiguous* locations. (note: assuming
    that you gave a, b, c in the right order, merge_locations(a, b, c)
    does the same thing as merge_locations(a, c). However, a future
    version of the function might differentiate them, so *don't do
    it*)

    TODO: it'd be nice to have a class for discontinuous locations, so
    that you could highlight two tokens on the same line that are not
    next to each other. Do it if a good use case arise.
    """
    locations = list(sorted(loc for loc in locations))
    if not locations:
        raise Exception("You must merge at least one location!")
    loc1, loc2 = locations[0], locations[-1]
    # locations should be in the same source
    assert all(loc1.source is l.source for l in locations[1:])
    return Location(source = loc1.source,
                    span = (loc1.span[0], loc2.span[1]),
                    tokens = reduce(list.__add__,
                                    (list(l.tokens) for l in locations
                                     if l.tokens is not None), []))

