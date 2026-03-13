import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from care_engine.models import Provider

# Maps specialty name (lower-cased) to (tier, score).
# High (7 pts): Oncology, Nephrology, Cardiology, Neurology, Hematology, Infectious Disease
# Medium (5 pts): Endocrinology, Pulmonology, Psychiatry, Rheumatology, Transplant
# Base (0 pts): Primary Care / NP / PA
# Low (2 pts): everything else (the default fallback)
SPECIALTY_MAP = {
    # ── HIGH ──────────────────────────────────────────────────────────────────
    'oncology':                                ('high', 7),
    'medical oncology':                        ('high', 7),
    'radiation oncology':                      ('high', 7),
    'gynecologic oncology':                    ('high', 7),
    'surgical oncology':                       ('high', 7),
    'hematology/oncology':                     ('high', 7),
    'hematology oncology':                     ('high', 7),
    'hematology  oncology':                    ('high', 7),
    'hematology oncology physician':           ('high', 7),
    'hematology  oncology physician':          ('high', 7),
    'hematology internal medicine':            ('high', 7),
    'hematology':                              ('high', 7),
    'nephrology':                              ('high', 7),
    'nephrology physician':                    ('high', 7),
    'pediatric nephrology':                    ('high', 7),
    'cardiology':                              ('high', 7),
    'interventional cardiology':               ('high', 7),
    'interventional cardiology physician':     ('high', 7),
    'advanced heart failure and transplant cardiology': ('high', 7),
    'advanced heart failure/transplant cardiology':     ('high', 7),
    'nuclear cardiology':                      ('high', 7),
    'pediatric cardiology':                    ('high', 7),
    'clinical cardiac electrophysiology':      ('high', 7),
    'neurology':                               ('high', 7),
    'neurology physician':                     ('high', 7),
    'neurological surgery':                    ('high', 7),
    'neurological surgery physician':          ('high', 7),
    'vascular neurology':                      ('high', 7),
    'pediatric neurology':                     ('high', 7),
    'child neurology':                         ('high', 7),
    'clinical neurophysiology':                ('high', 7),
    'infectious disease':                      ('high', 7),
    'infectious disease physician':            ('high', 7),
    'pediatric infectious diseases':           ('high', 7),

    # ── MEDIUM ────────────────────────────────────────────────────────────────
    'endocrinology':                                       ('medium', 5),
    'endocrinology, diabetes  metabolism':                 ('medium', 5),
    'endocrinology, diabetes & metabolism':                ('medium', 5),
    'endocrinology, diabetes  metabolism physician':       ('medium', 5),
    'endocrinology, diabetes & metabolism physician':      ('medium', 5),
    'reproductive endocrinology':                          ('medium', 5),
    'pediatric endocrinology':                             ('medium', 5),
    'pulmonary disease':                                   ('medium', 5),
    'pulmonary disease physician':                         ('medium', 5),
    'pulmonology':                                         ('medium', 5),
    'pediatric pulmonology':                               ('medium', 5),
    'psychiatry':                                          ('medium', 5),
    'psychiatry & neurology':                              ('medium', 5),
    'psychiatry physician':                                ('medium', 5),
    'geriatric psychiatry':                                ('medium', 5),
    'geriatric psychiatry physician':                      ('medium', 5),
    'addiction psychiatry':                                ('medium', 5),
    'forensic psychiatry':                                 ('medium', 5),
    'psychiatric/mental health np':                        ('medium', 5),
    'psychiatric/mental health cns':                       ('medium', 5),
    'psychiatricmental health nurse practitioner':         ('medium', 5),
    'psychiatricmental health clinical nurse specialist':  ('medium', 5),
    'rheumatology':                                        ('medium', 5),
    'rheumatology physician':                              ('medium', 5),
    'transplant':                                          ('medium', 5),
    'transplant surgery':                                  ('medium', 5),
    'transplant surgery physician':                        ('medium', 5),
    'transplant hepatology':                               ('medium', 5),
    'transplant hepatology physician':                     ('medium', 5),

    # ── BASE (primary care) ───────────────────────────────────────────────────
    'internal medicine':                       ('base', 0),
    'internal medicine physician':             ('base', 0),
    'family medicine':                         ('base', 0),
    'family medicine physician':               ('base', 0),
    'family practice':                         ('base', 0),
    'general practice':                        ('base', 0),
    'primary care':                            ('base', 0),
    'primary care physician':                  ('base', 0),
    'nurse practitioner':                      ('base', 0),
    'family nurse practitioner':               ('base', 0),
    'physician assistant':                     ('base', 0),
    'geriatric medicine':                      ('base', 0),
    'geriatrician':                            ('base', 0),
    'pediatrics':                              ('base', 0),
    'obstetrics & gynecology':                 ('base', 0),
    # Everything else → low (2 pts) via the default fallback in handle()
}

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[4] / 'data' / 'providers_clean.csv'
BATCH_SIZE = 2000


class Command(BaseCommand):
    help = 'Load providers from CSV. Default: data/providers_clean.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, default=str(DEFAULT_CSV_PATH),
            help='Path to providers CSV (columns: name, specialty)',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all existing providers before loading',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['file'])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        if options['clear']:
            deleted, _ = Provider.objects.all().delete()
            self.stdout.write(f'Cleared {deleted} existing providers.')

        skipped = 0
        batch: list[Provider] = []
        created_total = 0

        with open(csv_path, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get('name') or row.get('Name') or '').strip()
                specialty = (row.get('specialty') or row.get('Specialty') or '').strip()

                if not name:
                    skipped += 1
                    continue

                tier, score = SPECIALTY_MAP.get(specialty.lower(), ('low', 2))

                batch.append(Provider(
                    name=name,
                    specialty=specialty,
                    specialty_tier=tier,
                    specialty_score=score,
                    npi='',
                ))

                if len(batch) >= BATCH_SIZE:
                    Provider.objects.bulk_create(batch, ignore_conflicts=True)
                    created_total += len(batch)
                    batch = []
                    if created_total % 20000 == 0:
                        self.stdout.write(f'  … {created_total:,} processed')

        if batch:
            Provider.objects.bulk_create(batch, ignore_conflicts=True)
            created_total += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Done. Processed {created_total:,} providers ({skipped} skipped).'
        ))
