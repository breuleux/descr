
import itertools
from collections import defaultdict
import cssselect as cs

# from descr import boxy_terminus
# pr = boxy_terminus()


def custom_merge(orig, new, merge = None):
    additions = {}
    for k, v in new.items():
        if k == "!clear" and v:
            orig.clear()
        elif v is None and k in orig:
            del orig[k]
        else:
            additions[k] = v
    if merge is None:
        orig.update(additions)
        return orig
    else:
        return merge(orig, additions)

def _merge_to_lists(a, b):
    for k, v in b.items():
        a[k].append(v)
    return a

def _merge_lists(a, b):
    for k, v in b.items():
        a[k].extend(v)
    return a


class RuleTree(object):

    __id = 0

    def __init__(self):
        self.here = defaultdict(list)
        self.immediate = defaultdict(RuleTree)
        self.under = defaultdict(RuleTree)
        self.id = RuleTree.__id
        RuleTree.__id += 1

    def search(self, selector):
        return [self._search(selector, sel.parsed_tree)
                for sel in cs.parse(selector)]

    def check_element(self, strselector, element):
        if not isinstance(element, cs.parser.Element):
            raise TypeError("Expected element",
                            {"selector": element,
                             "selector_string": strselector})

        name = element.element
        if name != None:
            raise TypeError("Rules do not acknowledge specific tags such as '%s'" % name,
                            {"selector": element,
                             "selector_string": strselector})

    def _search(self, strselector, selector):

        if isinstance(selector, cs.parser.Element):
            self.check_element(strselector, selector)
            return self.under[True]

        elif isinstance(selector, cs.parser.Class):
            self.check_element(strselector, selector.selector)
            return self.under[selector.class_name]

        elif isinstance(selector, cs.parser.CombinedSelector):
            left = self._search(strselector, selector.selector)
            combinator = selector.combinator
            subselector = selector.subselector

            if isinstance(subselector, cs.parser.Element):
                self.check_element(strselector, subselector)
                entry = True
            elif isinstance(subselector, cs.parser.Class):
                entry = subselector.class_name
            else:
                raise TypeError("Subselector must be '*' or '.classname'",
                                {"selector": selector,
                                 "selector_string": strselector})

            if combinator == ' ':
                target = left.under[entry]
            elif combinator == '>':
                target =  left.immediate[entry]
            else:
                raise TypeError("Rules do not acknowledge the combinator '%s'" % combinator,
                                {"selector": selector,
                                 "selector_string": strselector})

            return target

        else:
            raise TypeError("Rules do not acknowledge '%s'" % type(selector).__name__,
                            {"selector": selector,
                             "selector_string": strselector})

    def register(self, selector, properties):
        targets = self.search(selector)
        for target in targets:
            custom_merge(target.here, properties, _merge_to_lists)


def accumulate_candidates(classes, trees):
    # classes: set of classes to filter the candidates with
    # trees: list of (depth, hadit, ruletree)
    # returns: list of (depth, hasit, ruletree)

    #   depth: higher depth = higher priority
    #          essentially this is the number of elements/classes in the
    #          css selector, e.g. ".a .b > .c *" has depth 4
    #          This does not match the CSS specification exactly
    #          because "*" would have lower priority than ".x" in CSS
    #          but this is good enough for most practical purposes.
    #   hadit: (for input) whether the tree contained rules for the
    #          layer right before this one
    #   hasit: (in return value) whether the tree contains rules for
    #          the classes specified. The tree might contain rules
    #          that will match for children of the node that has these
    #          classes even if there are no rules at this specific level.
    #   ruletree: a RuleTree with rules in .here, and more RuleTrees
    #          in .immediate (next class must match) or .under (some
    #          class may match a few layers down)

    newtrees = set()
    def add_maybe(catalog, what, depth):
        val = catalog.get(what, None)
        if val is not None:
            newtrees.add((depth, True, val))

    for depth, hadit, tree in trees:
        dp1 = depth + 1
        if hadit:
            # If the tree did not match the previous layer then
            # we can't match through .immediate
            add_maybe(tree.immediate, True, dp1)
        add_maybe(tree.under, True, dp1)
        if tree.under:
            # Might not have the classes, but we want to keep looking
            # for future calls to accumulate_candidates, because
            # matches might be several layers deep. hasit is set to
            # False to avoid the rules in tree.here from being used
            # and to prevent rules like ".a > .b" from matching in
            # the next call
            newtrees.add((depth, False, tree))
        for klass in classes:
            if hadit:
                add_maybe(tree.immediate, klass, dp1)
            add_maybe(tree.under, klass, dp1)

    newtrees = list(newtrees)
    newtrees.sort(key = lambda x: (x[0], x[2].id))
    return newtrees


def consult(trees):

    results = defaultdict(list)
    for _, hasit, tree in trees:
        if hasit:
            custom_merge(results, tree.here, _merge_lists)

    return results


class RuleTreeExplorer(object):

    def __init__(self, classes, candidates):
        self.classes = classes
        self.candidates = candidates
        self.properties = consult(candidates)

    def explore(self, classes, *info):
        new = RuleTreeExplorer(classes, accumulate_candidates(classes, self.candidates))
        for prop, combine in [(":classes", lambda x, y: y),
                              (":+classes", lambda x, y: x | y),
                              (":-classes", lambda x, y: x.difference(y)),
                              (":&classes", lambda x, y: x & y)]:
            for new_classes in new.properties.get(prop, ()):
                if callable(new_classes):
                    new_classes = new_classes(classes, *info)
                if isinstance(new_classes, str):
                    new_classes = {new_classes}
                if new_classes:
                    new_classes = combine(classes, new_classes)
                    if new_classes != classes:
                        return self.explore(new_classes, *info)
        else:
            return new

    def premanipulate(self, parts):

        props = self.properties

        for rearrange in props.get(":rearrange", ()):
            if callable(rearrange):
                parts = rearrange(self.classes, parts)
            elif isinstance(rearrange, str):
                parts = (rearrange,)
            elif rearrange is not None:
                parts = rearrange

        before_acc = []
        for before in props.get(":before", ()):
            if callable(before):
                before_acc = list(before(self.classes, parts)) + before_acc
            if isinstance(before, str):
                before_acc = [before] + before_acc

        after_acc = []
        for after in props.get(":after", ()):
            if callable(after):
                after_acc += list(after(self.classes, parts))
            if isinstance(after, str):
                after_acc += [after]

        if before_acc or after_acc:
            parts = itertools.chain(before_acc, parts, after_acc)

        return parts

    def postmanipulate(self, parts):

        props = self.properties

        joiner = props.get(":join", None)
        joiner = joiner[0] if joiner else "".join
        if isinstance(joiner, str):
            joiner = joiner.join

        s = joiner(parts)

        for wrapper in props.get(":wrap", ()):
            s = wrapper(s)

        return s


