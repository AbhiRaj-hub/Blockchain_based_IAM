"""
Retry ledger writes that failed earlier (the outbox). Run on a schedule or via the
anchor_worker container:   python manage.py flush_anchors
"""

from django.core.management.base import BaseCommand

from core.models import LedgerAnchor, PendingAnchor
from core.services.ledger_client import LedgerError, anchor_event


class Command(BaseCommand):
    help = "Retry pending ledger anchors in order; stops at the first failure (ledger still down)."

    def handle(self, *args, **options):
        done = 0
        for pending in PendingAnchor.objects.select_related("identity").order_by("created_at")[:500]:
            try:
                block_hash = anchor_event(pending.event_type, pending.payload)
            except LedgerError as exc:
                pending.attempts += 1
                pending.last_error = str(exc)[:500]
                pending.save(update_fields=["attempts", "last_error"])
                self.stdout.write(self.style.WARNING(f"Ledger unavailable after {done} flushed: {exc}"))
                return
            LedgerAnchor.objects.create(identity=pending.identity, event_type=pending.event_type, block_hash=block_hash)
            pending.delete()
            done += 1
        if done:
            self.stdout.write(self.style.SUCCESS(f"Flushed {done} pending anchor(s)."))
