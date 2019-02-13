from hera.main import main


def test_every_op_file(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/every_op.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""

    with open("test/assets/asm/every_op.hera.lcode") as f:
        assert captured.err == f.read()

    main(["assemble", "--data", "--stdout", "test/assets/asm/every_op.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""

    with open("test/assets/asm/every_op.hera.ldata") as f:
        assert captured.err == f.read()
