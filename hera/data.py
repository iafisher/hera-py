from collections import namedtuple


Location = namedtuple("Location", ["line", "column", "path", "file_lines"])


class Op(namedtuple("Op", ["name", "args", "original"])):
    def __new__(cls, name, args, original=None):
        return tuple.__new__(cls, (name, args, original))

    def __eq__(self, other):
        return (
            isinstance(other, Op)
            and self.name == other.name
            and self.args == other.args
        )

    def __repr__(self):
        orepr = "None" if self.original is None else "Op(...)"
        return "Op(name={!r}, args={!r}, original={})".format(
            self.name, self.args, orepr
        )


class IntToken(int):
    def __new__(cls, value, loc=None, **kwargs):
        self = super(IntToken, cls).__new__(cls, value, **kwargs)
        self.location = loc
        return self


class Token(str):
    def __new__(cls, type_, value, loc=None):
        self = super(Token, cls).__new__(cls, value)
        self.type = type_
        self.location = loc
        return self
