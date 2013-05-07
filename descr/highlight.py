


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

    leftmost = min(start for start, end, attribute in specifications)
    rightmost = max(end for start, end, attribute in specifications)

    spans = [[leftmost, rightmost, []]]
    for spec in specifications:
        insert_span(spans, spec)

    return spans


def highlight(text, locations, offset = 0, compound_classes = False):

    locations = morsel(locations)
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

