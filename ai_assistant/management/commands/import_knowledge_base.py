import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from ai_assistant.models import PolicyDocument
from ai_assistant.services import get_embedding
from ai_assistant.mongodb_service import upsert_policy, clear_language

class Command(BaseCommand):
    help = 'Import knowledge base documents from folder structure with language support'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--language', '-l',
            type=str,
            default='en',
            help='Language code to import (default: en)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing documents for this language before importing'
        )
    
    def handle(self, *args, **options):
        language = options['language']
        clear_existing = options['clear']
        
        # Knowledge base directory (relative to this file)
        kb_dir = Path(__file__).parent.parent.parent / 'knowledge_base' / language
        
        if not kb_dir.exists():
            self.stdout.write(self.style.ERROR(f'❌ Language directory not found: {kb_dir}'))
            return
        
        # Clear existing documents if requested
        if clear_existing:
            self.stdout.write(self.style.WARNING(f'🗑️  Clearing existing {language} documents from DB and MongoDB...'))
            # Clear Django DB
            deleted_count, _ = PolicyDocument.objects.filter(language=language).delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} documents from PostgreSQL'))
            # Clear MongoDB
            mongo_deleted = clear_language(language)
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {mongo_deleted} documents from MongoDB'))
        
        # Collect all .txt files recursively
        txt_files = list(kb_dir.rglob('*.txt'))
        
        if not txt_files:
            self.stdout.write(self.style.WARNING(f'⚠️  No .txt files found in {kb_dir}'))
            return
        
        self.stdout.write(f'\n📚 Importing {len(txt_files)} documents for language: {language}')
        self.stdout.write('=' * 70)
        
        success_count = 0
        skip_count = 0
        
        for txt_file in txt_files:
            # Determine category from folder structure or filename
            category = self._get_category_from_path(txt_file)
            
            # Read content
            try:
                content = txt_file.read_text(encoding='utf-8')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error reading {txt_file.name}: {e}'))
                skip_count += 1
                continue
            
            # Generate title from filename (e.g., "cancellation_policy.txt" -> "Cancellation Policy")
            title = txt_file.stem.replace('_', ' ').title()
            
            # Check if already exists in Django DB
            if PolicyDocument.objects.filter(title=title, language=language).exists():
                self.stdout.write(self.style.WARNING(f'⏭️  Skipping (already exists): {title}'))
                skip_count += 1
                continue
            
            # Generate embedding using local Ollama
            self.stdout.write(f'🔄 Processing: {title}...')
            embedding = get_embedding(content)
            
            if not embedding:
                self.stdout.write(self.style.WARNING(f'⚠️  Skipped (no embedding from Ollama): {title}'))
                skip_count += 1
                continue
            
            # 1. Save to Django PostgreSQL database
            try:
                policy = PolicyDocument.objects.create(
                    title=title,
                    content=content,
                    category=category,
                    language=language,
                    embedding=embedding
                )
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f'⚠️  Skipped (Integrity Error): {title}'))
                skip_count += 1
                continue
            
            # 2. Sync to MongoDB Atlas
            try:
                upsert_policy(
                    title=title,
                    content=content,
                    category=category,
                    embedding=embedding,
                    language=language
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Synced to MongoDB: {title}'))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ MongoDB sync failed for {title}: {e}'))
                skip_count += 1
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'✅ Import complete!'))
        self.stdout.write(f'   Success: {success_count}')
        self.stdout.write(f'   Skipped: {skip_count}')
        self.stdout.write(f'   Language: {language}')
    
    def _get_category_from_path(self, file_path: Path) -> str:
        """Map folder structure or filename to document category."""
        filename = file_path.stem.lower()
        
        # Specific mapping based on filename keywords
        if 'cancellation' in filename:
            return 'cancellation'
        elif 'payment' in filename:
            return 'payment'
        elif 'booking' in filename or 'guesthouse' in filename or 'accommodation' in filename:
            return 'booking'
        elif 'tour' in filename:
            return 'tour'
        elif 'motorbike' in filename or 'buggy' in filename or 'transport' in filename:
            return 'transport'
        elif 'safety' in filename or 'warning' in filename:
            return 'safety'
        elif 'pricing' in filename or 'price' in filename:
            return 'pricing'
        elif 'cultural' in filename or 'etiquette' in filename:
            return 'cultural'
        
        # Fallback to folder name
        folder_name = file_path.parent.name.lower()
        category_map = {
            'critical': 'general',
            'important': 'general',
            'helpful': 'general',
        }
        return category_map.get(folder_name, 'general')