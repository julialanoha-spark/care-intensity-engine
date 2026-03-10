import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from care_engine.models import Medication

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[4] / 'data' / 'sample_medications.csv'


class Command(BaseCommand):
    help = 'Load medications from CSV (default: data/sample_medications.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=str(DEFAULT_CSV_PATH),
            help='Path to medications CSV (columns: name, dosage, category, is_specialty)',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['file'])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        created_count = 0
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name', '').strip()
                if not name:
                    continue

                is_specialty_raw = row.get('is_specialty', 'false').strip().lower()
                is_specialty = is_specialty_raw in ('true', '1', 'yes')

                _, created = Medication.objects.get_or_create(
                    name=name,
                    dosage=row.get('dosage', '').strip(),
                    defaults={
                        'category': row.get('category', '').strip(),
                        'is_specialty': is_specialty,
                    },
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Loaded medications: {created_count} created.')
        )
