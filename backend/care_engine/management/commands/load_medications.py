import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from care_engine.models import Medication

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[4] / 'data' / 'meds_clean.csv'
BATCH_SIZE = 1000


class Command(BaseCommand):
    help = 'Load medications from CSV. Default: data/meds_clean.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, default=str(DEFAULT_CSV_PATH),
            help='Path to medications CSV (columns: drug_name, dosage_name, is_specialty)',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all existing medications before loading',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['file'])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        if options['clear']:
            deleted, _ = Medication.objects.all().delete()
            self.stdout.write(f'Cleared {deleted} existing medications.')

        batch = []
        total = 0
        skipped = 0

        with open(csv_path, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                drug_name   = (row.get('drug_name') or '').strip()
                dosage_name = (row.get('dosage_name') or '').strip()
                is_spec_raw = (row.get('is_specialty') or 'false').strip().lower()

                if not drug_name or not dosage_name:
                    skipped += 1
                    continue

                is_specialty = is_spec_raw in ('true', '1', 'yes')

                batch.append(Medication(
                    name=drug_name,
                    dosage=dosage_name,
                    category='',
                    is_specialty=is_specialty,
                ))

                if len(batch) >= BATCH_SIZE:
                    Medication.objects.bulk_create(batch, ignore_conflicts=True)
                    total += len(batch)
                    batch = []

        if batch:
            Medication.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Done. Loaded {total:,} medications ({skipped} skipped).'
        ))
