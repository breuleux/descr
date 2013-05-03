
def insert_lineno(c, d):
    n, width = "", 3
    for cls in c:
        if cls.startswith("L#"):
            n = cls[2:]
        elif cls.startswith("W#"):
            width = int(cls[2:])
    return [n.rjust(width)]


def morsel(specifications):

    if not specifications:
        return []

    specifications = list(sorted(specifications,
                                 key = lambda spec: (spec[0], -spec[1])))

    def insert_span(spans, new):
        start, end, attribute = new
        attribute = [attribute]
        i = 0
        while i < len(spans):
            other = spans[i]
            start2, end2, attribute2 = other
            if start2 == end2:
                i += 1
                continue
            if start2 <= start < end2:
                if start == start2 and start2 < end2:
                    insertion_point = i
                    spans.pop(i)
                else:
                    other[1] = start
                    insertion_point = i + 1

                insert = []
                if start == end:
                    insert.append([start, end, attribute2 + attribute])
                else:
                    m = min(end, end2)
                    if start != m:
                        insert.append([start, m, attribute2 + attribute])

                if end2 > end:
                    insert.append([end, end2, attribute2])
                elif end > end2:
                    insert.append([end2, end, attribute])

                spans[insertion_point:insertion_point] = insert
                break
            i += 1
        else:
            spans.append([end2, start, []])
            spans.append([start, end, attribute])



    # def insert_span(spans, new):
    #     start, end, attribute = new
    #     attribute = [attribute]
    #     for i, other in enumerate(spans):
    #         start2, end2, attribute2 = other
    #         if start2 == end2:
    #             continue
    #         if start2 <= start < end2:
    #             other[1] = start
    #             i += 1
    #             if start == end:
    #                 spans.insert(i, [start, end, attribute2 + attribute])
    #                 i += 1
    #             else:
    #                 m = min(end, end2)
    #                 if start != m:
    #                     spans.insert(i, [start, m, attribute2 + attribute])
    #                     i += 1

    #             if end2 > end:
    #                 spans.insert(i, [end, end2, attribute2])
    #             elif end > end2:
    #                 spans.insert(i, [end2, end, attribute])

    #             break
    #     else:
    #         spans.append([end2, start, []])
    #         spans.append([start, end, attribute])


    leftmost = min(start for start, end, attribute in specifications)
    rightmost = max(end for start, end, attribute in specifications)

    spans = [[leftmost, rightmost, []]]
    for spec in specifications:
        insert_span(spans, spec)

    return spans


def highlight(text, locations, offset = 0, compound_classes = False):

    locations = morsel(locations)
    # pr(locations)
    results = []
    i = 0
    lt = len(text)

    for start, end, attributes in locations:
        start -= offset
        if start < 0: start = 0
        end -= offset
        if end > lt: end = lt
        if start > end:
            continue
        if i < start:
            results.append(text[i:start])
        a = set()
        if compound_classes:
            for attr in attributes:
                a |= attr
        elif attributes:
            a = attributes[-1]
        results.append((a, text[start:end]))
        i = end

    if i < len(text):
        results.append(text[i:])

    return results


def highlight_lines(lines, locations, lineno = 0, offset = 0, **kwargs):

    i = offset
    k = lineno
    width = len(str(k + len(lines)))
    for line in lines:
        locations.append((i, i, {"lineno", "L#%s"%k, "W#%s"%width}))
        i += len(line) + 1
        k += 1

    return highlight("\n".join(lines), locations, offset, **kwargs)







# def standardize_location(filename, locations):
#     try:
#         with open(filename) as f:
            



def lc_to_pos(lines, l_offset, l, c):
    l -= l_offset
    return sum(map(len(lines[:l]))) + c


def _extract_location(classes, parts):
    filename, (start, end) = parts
    if end is not None:
        raise Exception

    ctx = 0
    for k in classes:
        if k.startswith("C#"):
            ctx = int(k[2:])

    l1, c1 = start
    # loc = lc_to_pos(lines, l1, 

    try:
        with open(filename) as f:
            lines = f.read().split("\n")
            return [[{"pre"},
                     highlight_lines(lines[l1-ctx-1:l1+ctx], [], l1, 0)
                     ]]
    except IOError:
        return ["Could not read file."]


