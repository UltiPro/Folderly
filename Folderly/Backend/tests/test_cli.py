"""The `codes` CLI, the only way an instance gets its first usable account."""

import re
from cli import codes_cli

CODE = re.compile(r"[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}")


def run(app, *args):
    return app.test_cli_runner().invoke(codes_cli, list(args))


def test_generated_codes_are_printed_once_and_work(app, client, make_account):
    result = run(app, "new", "--count", "2", "--label", "family")
    assert result.exit_code == 0
    codes = CODE.findall(result.output)
    assert len(codes) == 2

    for code in codes:
        account = make_account(activate=False)
        assert (
            client.post("/user/activate", json={"code": code}, headers=account.headers).status_code == 204
        )


def test_the_database_keeps_only_hashes(app):
    from models.activationcode import ActivationCodeModel
    from orm import db

    code = CODE.findall(run(app, "new").output)[0]
    with app.app_context():
        stored = db.session.query(ActivationCodeModel).one()
        assert code not in stored.code_hash
        assert len(stored.code_hash) == 64  # sha256, hex


def test_list_shows_what_is_spent_and_by_whom(app, client, make_account):
    code = CODE.findall(run(app, "new", "--label", "for-me").output)[0]

    assert "unused" in run(app, "list").output

    account = make_account(activate=False)
    client.post("/user/activate", json={"code": code}, headers=account.headers)

    listed = run(app, "list").output
    assert "unused" not in listed
    assert account.email in listed
    assert "for-me" in listed


def test_list_on_an_empty_database_says_so(app):
    assert "No activation codes yet" in run(app, "list").output


def test_count_must_be_at_least_one(app):
    assert run(app, "new", "--count", "0").exit_code != 0
