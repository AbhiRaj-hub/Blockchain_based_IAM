"""
Create the first administrator (or an additional one).

Interactive:      python manage.py create_admin
Non-interactive:  ADMIN_PASSWORD=... python manage.py create_admin --noinput \
                      --username alice --email alice@example.com
First-boot (containers): set ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD and the entrypoint calls
                      `create_admin --noinput --if-none-exists`.  Remove ADMIN_PASSWORD afterwards.
"""

import os
from getpass import getpass

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Identity, LedgerAnchor
from core.services.ledger_client import LedgerError, anchor_event


class Command(BaseCommand):
    help = "Create an administrator identity and anchor its creation on the ledger."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--email")
        parser.add_argument("--noinput", action="store_true", help="Read ADMIN_PASSWORD from the environment.")
        parser.add_argument("--if-none-exists", action="store_true", help="Do nothing if an admin already exists.")

    def handle(self, *args, **opts):
        if opts["if_none_exists"] and Identity.objects.filter(role=Identity.Role.ADMIN).exists():
            self.stdout.write("An administrator already exists; nothing to do.")
            return

        noinput = opts["noinput"]
        username = opts["username"] or os.getenv("ADMIN_USERNAME") or ("" if noinput else input("Username: ").strip())
        email = opts["email"] or os.getenv("ADMIN_EMAIL") or ("" if noinput else input("Email: ").strip())
        if not username or not email:
            raise CommandError("A username and email are required (--username/--email or ADMIN_USERNAME/ADMIN_EMAIL).")
        if Identity.objects.filter(username=username).exists():
            raise CommandError(f"The username '{username}' is already taken.")

        if noinput:
            password = os.getenv("ADMIN_PASSWORD", "")
            if not password:
                raise CommandError("ADMIN_PASSWORD must be set with --noinput.")
        else:
            password = getpass("Password: ")
            if password != getpass("Password (again): "):
                raise CommandError("The passwords did not match.")

        admin = Identity(username=username, email=email, role=Identity.Role.ADMIN, clearance_level=5,
                         department="Security", status=Identity.Status.ACTIVE, is_active=True,
                         is_staff=True, is_superuser=True)
        try:
            password_validation.validate_password(password, user=admin)
        except ValidationError as exc:
            raise CommandError("Weak password: " + " ".join(exc.messages)) from exc
        admin.set_password(password)

        try:
            with transaction.atomic():
                admin.save()
                block_hash = anchor_event("identity_created", {"did": admin.did, "role": admin.role, "bootstrap": True})
                LedgerAnchor.objects.create(identity=admin, event_type="identity_created", block_hash=block_hash)
        except LedgerError as exc:
            raise CommandError(f"The ledger service is unreachable, so nothing was created: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Administrator '{username}' created ({admin.did})."))
