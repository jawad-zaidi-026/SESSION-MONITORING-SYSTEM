from django.core.management.base import BaseCommand
from extract_logs import analyze_and_send_report

class Command(BaseCommand):
    help = 'Extracts Windows logs and sends email report'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔍 Extracting logs and sending report...")
        analyze_and_send_report()
        self.stdout.write("✅ Report sent successfully.")
