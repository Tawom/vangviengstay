from django.core.management.base import BaseCommand
from ai_assistant.models import PolicyDocument
from ai_assistant.services import get_embedding

class Command(BaseCommand):
    help = 'Import policy documents and generate embeddings'

    def handle(self, *args, **options):
        policies = [
            {
                'title': 'Cancellation Policy',
                'content': 'You can cancel your booking up to 24 hours before check-in for a full refund. Cancellations within 24 hours will be charged 50%. No-shows will be charged the full amount. To cancel, please contact us via WhatsApp or email with your booking reference number.',
                'category': 'cancellation'
            },
            {
                'title': 'Payment Methods',
                'content': 'We accept cash (Lao Kip, USD, THB), bank transfer, and major credit cards. Payment is due at check-in unless otherwise arranged. For tours, a 50% deposit may be required at booking.',
                'category': 'payment'
            },
            {
                'title': 'Check-in and Check-out Times',
                'content': 'Standard check-in time is 2:00 PM. Check-out time is 11:00 AM. Early check-in or late check-out may be available upon request and subject to availability. Please contact us in advance if you need special arrangements.',
                'category': 'booking'
            },
            {
                'title': 'Late Arrival Policy',
                'content': 'If you are running late, you MUST call or message the property immediately. Bookings will be automatically revoked and marked as a "No-Show" if you arrive late without prior notice, and no refund will be issued.',
                'category': 'booking'
            },
            {
                'title': 'Tour Cancellation',
                'content': 'Tours can be cancelled up to 48 hours before the scheduled start time for a full refund. Cancellations within 48 hours will be charged 50%. Weather-related cancellations by the operator will result in a full refund or rescheduling.',
                'category': 'tour'
            },
            {
                'title': 'What to Bring for Tours',
                'content': 'For outdoor tours, please bring: comfortable walking shoes, sunscreen, hat, water bottle, camera, and any personal medications. For water activities, bring swimwear and a towel. We provide all necessary equipment.',
                'category': 'tour'
            },
            {
                'title': 'Motorbike Rental Requirements',
                'content': 'To rent a motorbike, you must have a valid driver\'s license and international driving permit. A security deposit of $100-200 is required. Helmets are provided and mandatory. Fuel is not included.',
                'category': 'transport'
            },
            {
                'title': 'Contact Information',
                'content': 'For urgent matters, contact us via WhatsApp at +856 XX XXX XXXX. For general inquiries, email us at info@vangviengstay.online. We respond within 2 hours during business hours (8 AM - 8 PM Laos time).',
                'category': 'general'
            },
        ]
        
        self.stdout.write('Importing policy documents...')
        
        for policy_data in policies:
            doc, created = PolicyDocument.objects.update_or_create(
                title=policy_data['title'],
                defaults={
                    'content': policy_data['content'],
                    'category': policy_data['category']
                }
            )
            
            # Try to generate embedding (works on production with pgvector + Ollama)
            # On local SQLite without Ollama, this will gracefully skip
            if created or not doc.embedding:
                self.stdout.write(f'Generating embedding for: {doc.title}')
                embedding = get_embedding(doc.content)
                
                if embedding:
                    doc.embedding = embedding
                    self.stdout.write(self.style.SUCCESS(f'✓ Created/Updated with embedding: {doc.title}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Saved without embedding (keyword search will be used): {doc.title}'))
            
            # Always save the document, even if embedding generation failed
            doc.save()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Policy import complete!'))