import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from care_engine.models import Provider

# Maps specialty name (case-insensitive) to (tier, score)
# Update this dict when loading CSVs with different specialty naming conventions
SPECIALTY_MAP = {
    # High complexity — 7 pts
    'oncology': ('high', 7),
    'nephrology': ('high', 7),
    'cardiology': ('high', 7),
    'neurology': ('high', 7),
    'hematology': ('high', 7),
    'infectious disease': ('high', 7),
    'hematology/oncology': ('high', 7),
    # Medium complexity — 5 pts
    'endocrinology': ('medium', 5),
    'pulmonology': ('medium', 5),
    'psychiatry': ('medium', 5),
    'rheumatology': ('medium', 5),
    'transplant': ('medium', 5),
    'transplant surgery': ('medium', 5),
    # Base — 0 pts
    'primary care physician': ('base', 0),
    'primary care': ('base', 0),
    'family medicine': ('base', 0),
    'general practice': ('base', 0),
    # Everything else falls through to low (2 pts)
}

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[4] / 'data' / 'sample_providers.csv'


class Command(BaseCommand):
    help = 'Load providers from CSV (default: data/sample_providers.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=str(DEFAULT_CSV_PATH),
            help='Path to providers CSV (columns: name, specialty, npi)',
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
                specialty = row.get('specialty', '').strip()
                npi = row.get('npi', '').strip()

                if not name or not specialty:
                    continue

                tier, score = SPECIALTY_MAP.get(specialty.lower(), ('low', 2))

                _, created = Provider.objects.get_or_create(
                    name=name,
                    specialty=specialty,
                    defaults={
                        'specialty_tier': tier,
                        'specialty_score': score,
                        'npi': npi,
                    },
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Loaded providers: {created_count} created.')
        )
