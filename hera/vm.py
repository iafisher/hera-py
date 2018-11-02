

class VirtualMachine:
    """An abstract representation of a HERA processor."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the machine to its initial state."""
        # Sixteen 16-bit registers
        self.registers = [0] * 16
        # 16-bit program counter
        self.pc = 0
        # Status/control flags
        self.flag_sign = False
        self.flag_zero = False
        self.flag_overflow = False
        self.flag_carry = False
        self.flag_carry_block = False
        # A memory array of 16-bit words. The HERA specification requires 2**16
        # words to be addressable, but we start off with a considerably smaller
        # array and expand it as necessary, to keep the start-up time fast.
        self.memory = [0] * (2**4)

    def exec_one(self, inst):
        """Execute a single instruction."""
        try:
            handler = self.imap[inst.name]
        except KeyError:
            raise ValueError(f'unknown instruction "{inst.name}"') from None
        else:
            handler(self, *inst.args)

    def exec_many(self, program):
        """Execute a program (i.e., a list of instructions), resetting the
        machine's state beforehand.
        """
        self.reset()
        while self.pc < len(program):
            self.exec_one(program[self.pc])

    def setr(self, target, value):
        """Store the value in the target register, handling overflow and setting
        flags.
        """
        if value >= 2**15:
            value = (value % 2**15) - 2**15
            self.flag_carry = False
            self.flag_overflow = True
        elif value < -2**15:
            # TODO: This isn't the right way to do it.
            value += 2**16
            self.flag_carry = True
            self.flag_overflow = True
        else:
            self.flag_carry = False
            self.flag_overflow = False
        index = self.rindex(target)
        if index != 0:
            self.registers[self.rindex(target)] = value
        self.flag_zero = (value == 0)
        self.flag_sign = (value < 0)

    def getr(self, name):
        """Get the contents of the register with the given name."""
        return self.registers[self.rindex(name)]

    def rindex(self, name):
        """Return the index of the register with the given name in the register
        array.
        """
        if name.startswith('R'):
            return int(name[1:])
        else:
            raise KeyError(name)

    def exec_add(self, target, left, right):
        """Execute the ADD instruction."""
        carry = 1 if not self.flag_carry_block and self.flag_carry else 0
        self.setr(target, self.getr(left) + self.getr(right) + carry)
        self.pc += 1

    def exec_sub(self, target, left, right):
        """Execute the SUB instruction."""
        self.setr(target, self.getr(left) - self.getr(right))
        self.pc += 1

    # A mapping from instruction names to handler functions.
    imap = {
        'ADD': exec_add,
        'SUB': exec_sub,
    }
