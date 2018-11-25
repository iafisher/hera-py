def preprocess(program):
    err = False
    for inst in program:
        if not inst.verify():
            err = True
    if err:
        return

    nprogram = []
    for inst in program:
        nprogram.extend(inst.convert_pseudo())

    labels = get_labels(nprogram)
    for inst in program:
        inst.resolve_labels(labels)

    return [inst for inst in nprogram if inst.name not in ("LABEL", "DLABEL", "CONSTANT")]


def get_labels(program):
    """Return a dictionary that maps from instruction label, data label and constant
    names to values.
    """
    labels = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        opname = op.name.lower()
        if opname == "label":
            labels[op.args[0]] = pc
        elif opname == "dlabel":
            labels[op.args[0]] = dc
        elif opname == "constant":
            labels[op.args[0]] = op.args[1]
        elif opname == "integer":
            dc += 1
        elif opname == "dskip":
            dc += op.args[0]
        elif opname == "lp_string":
            dc += len(op.args[0]) + 1
        else:
            pc += 1
    return labels
