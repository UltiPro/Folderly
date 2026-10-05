import click
from datetime import datetime, timezone

from flask.cli import AppGroup

from orm import db

from models.activationcode import ActivationCodeModel
from models.user import UserModel

from utils.activation import hash_code, new_code

codes_cli = AppGroup("codes", help="Manage activation codes.")


@codes_cli.command("new")
@click.option("--count", default=1, show_default=True, help="How many to generate.")
@click.option("--label", default=None, help="Note to yourself, e.g. who it is for.")
def create_codes(count, label):
    """Generate activation codes and print them.

    This is the only time the codes are readable: the database holds their
    hashes, so a code that is not written down now is gone.
    """
    if count < 1:
        raise click.BadParameter("--count must be at least 1.")

    created = datetime.now(timezone.utc).replace(tzinfo=None)
    generated = []
    for _ in range(count):
        code = new_code()
        db.session.add(ActivationCodeModel(code_hash=hash_code(code), label=label, created_at=created))
        generated.append(code)
    db.session.commit()

    click.echo("Write these down now - they are not stored in readable form:")
    for code in generated:
        click.echo(f"  {code}")


@codes_cli.command("list")
def list_codes():
    """Show which codes are still unused, and who redeemed the rest."""
    codes = ActivationCodeModel.query.order_by(ActivationCodeModel.id).all()
    if not codes:
        click.echo("No activation codes yet. Generate some with `codes new`.")
        return

    for code in codes:
        if code.used_at is None:
            state = "unused"
        else:
            user = db.session.get(UserModel, code.used_by_id) if code.used_by_id else None
            owner = user.email if user else "a since-deleted account"
            state = f"used {code.used_at:%Y-%m-%d} by {owner}"
        click.echo(f"#{code.id:<4} {state:<48} {code.label or ''}")
