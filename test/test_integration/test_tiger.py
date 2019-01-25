from hera.main import main


def test_lexical_scope_deep(capsys):
    main(["test/assets/tiger/lexical_scope_deep.hera"])

    captured = capsys.readouterr()
    assert captured.out == "42"
