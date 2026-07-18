from django.core.management.base import BaseCommand

from billing.tasks import run_daily_billing_cycle


class Command(BaseCommand):
    help = (
        'Jalankan siklus billing (generate invoice periode berikutnya, tandai overdue, '
        'auto-suspend tenant/subscriber telat bayar) secara langsung di proses ini — '
        'tanpa lewat Celery/Redis. Buat testing manual atau kalau Celery beat belum jalan.'
    )

    def handle(self, *args, **options):
        results = run_daily_billing_cycle()
        for key, value in results.items():
            self.stdout.write(f'{key}: {value}')
