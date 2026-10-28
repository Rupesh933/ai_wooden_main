from django.core.management.base import BaseCommand
from supports.rag import load_documents


class Command(BaseCommand):
    help = "Loads PDF document chunks from supports/documents into ChromaDB"

    def handle(self, *args, **options):
        self.stdout.write("Loading documents into ChromaDB...")
        load_documents()
        self.stdout.write(self.style.SUCCESS("Documents loaded successfully."))
