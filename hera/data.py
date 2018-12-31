from collections import namedtuple


Location = namedtuple("Location", ["path", "lines"])


class Op(namedtuple("Op", ["name", "args", "location", "original"])):
    def __new__(cls, name, args, location=None, original=None):
        return tuple.__new__(cls, (name, args, location, original))

    def __eq__(self, other):
        return (
            isinstance(other, Op)
            and self.name == other.name
            and self.args == other.args
        )

    def __repr__(self):
        lrepr = "None" if self.location is None else "Location(...)"
        orepr = "None" if self.original is None else "Op(...)"
        return "Op(name={!r}, args={!r}, location={}, original={})".format(
            self.name, self.args, lrepr, orepr
        )


Program = namedtuple("Program", ["ops", "data_statements", "labels"])
