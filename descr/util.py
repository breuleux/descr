


class Descriptor(object):

    __classes__ = frozenset({})

    def __init__(self, classes):
        if classes:
            self.classes = classes | self.__classes__
        else:
            self.classes = self.__classes__


class Raw(Descriptor):

    def __init__(self, x):
        self. x = x

    def __descr__(self, recurse):
        return self.x


class Assoc(Descriptor):

    __classes__ = frozenset({"assoc"})

    def __init__(self, key, value, classes = None):
        super(Assoc, self).__init__(classes)
        self.key = key
        self.value = value

    def __descr__(self, recurse):
        return [self.classes, recurse(self.key), recurse(self.value)]


class Group(Descriptor):

    __classes__ = frozenset({})

    def __init__(self, elements, classes = None):
        super(Group, self).__init__(classes)
        self.elements = elements

    def __descr__(self, recurse):
        return [self.classes] + list(map(recurse, self.elements))


class Table(Descriptor):

    __classes__ = frozenset({"table"})

    def __init__(self,
                 elements,
                 classes = None,
                 row_classes = None,
                 column_classes = None):
        super(Table, self).__init__(classes)
        if isinstance(elements, dict):
            elements = list(elements.items())

        if not row_classes:
            row_classes = [set()]
        elif isinstance(row_classes, set):
            row_classes = [row_classes]
        if len(row_classes) < len(elements):
            row_classes = row_classes + [row_classes[-1]] * (len(elements) - len(row_classes))

        if not column_classes:
            column_classes = [set()]
        elif isinstance(column_classes, set):
            column_classes = [column_classes]

        self.elements = []
        for i, (row, rc) in enumerate(zip(elements, row_classes)):
            if len(column_classes) < len(row):
                cclasses = column_classes + [column_classes[-1]] * (len(row) - len(column_classes))
            else:
                cclasses = column_classes
            newrow = []
            for j, (column, cc) in enumerate(zip(row, cclasses)):
                newrow.append(Group([column],
                                    classes = {"C#"+str(j),
                                               "C#"+("odd" if j%2 else "even")}|cc))

            self.elements.append(Group(newrow,
                                       classes = {"R#"+str(i),
                                                  "R#"+("odd" if i%2 else "even")}|rc))

    def __descr__(self, recurse):
        return [self.classes] + list(map(recurse, self.elements))



class Object(Descriptor):

    __classes__ = frozenset({"object"})

    def __init__(self,
                 classname,
                 label = None,
                 elements = [],
                 fields = {},
                 field_ordering = None,
                 classes = None,
                 **kw):

        super(Object, self).__init__(classes)

        self.classname = classname
        self.label = label
        self.elements = elements
        if kw:
            fields = dict(fields, **kw)
        self.fields = fields
        if field_ordering:
            self.field_ordering = field_ordering
        else:
            self.field_ordering = list(sorted(self.fields.keys()))
        self.classes |= {"@" + classname}
        if label is not None:
            self.classes |= {"+" + label}

    def __descr__(self, recurse):
        results = [self.classes]
        for element in self.elements:
            results.append(recurse(element))
        for field in self.field_ordering:
            results.append(({"field", "+" + field},
                            recurse(self.fields[field])))
        return results


class Description(Descriptor):

    __classes__ = frozenset({"quote"})

    def __init__(self, description, classes = None):
        super(Description, self).__init__(classes)
        self.description = description

    def __descr__(self, recurse):
        d = self.description
        if isinstance(d, (str, int, float)):
            return recurse(d)
        elif isinstance(d, (set, frozenset)):
            return ([{"class_set"} | self.classes]
                    + list(sorted(d)))
        else:
            return ([{"description"} | self.classes]
                    + [Description(child).__descr__(recurse)
                       for child in d])

class Quote(Descriptor):

    __classes__ = frozenset({})

    def __init__(self, description):
        self.description = description

    def __descr__(self, recurse):
        return recurse(Description(recurse(self.description)))
