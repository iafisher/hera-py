from hera.main import main


def test_assemble_set_inc(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/set_inc.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/set_inc.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_binary_op(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/binary_op.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/binary_op.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_branch(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/branch.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/branch.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_flag(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/flag.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/flag.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_shift(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/shift.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/shift.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_misc(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/misc.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/misc.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_data(capsys):
    main(["assemble", "--data", "--stdout", "test/assets/asm/data.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/data.hera.ldata") as f:
        assert captured.out == f.read()
