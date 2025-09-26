from typing import Any

from django.core.management.base import BaseCommand

from datasets.models import Dataset, Tag
from users.models import User


class Command(BaseCommand):
    """Test command to create sample datasets for trending analysis."""

    help = "Create sample datasets for testing trending analysis"

    def handle(self, *args: Any, **options: Any) -> None:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email="test@example.com", defaults={"username": "testuser"}
        )

        # Create some sample tags
        tags_data = [
            "healthcare",
            "education",
            "agriculture",
            "finance",
            "technology",
            "transportation",
            "environment",
            "demographics",
            "economy",
            "governance",
        ]

        tags = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)

        # Create sample datasets with trending topics
        datasets_data: list[dict[str, Any]] = [
            {
                "title": "Nigeria Healthcare Facilities Database",
                "description": "Comprehensive database of healthcare facilities across Nigeria including hospitals, clinics, and primary health centers.",
                "tags": ["healthcare", "demographics"],
            },
            {
                "title": "Educational Institution Registry Nigeria",
                "description": "Registry of educational institutions in Nigeria from primary schools to universities.",
                "tags": ["education", "demographics"],
            },
            {
                "title": "Agricultural Production Data Nigeria",
                "description": "Agricultural production statistics for major crops across Nigerian states.",
                "tags": ["agriculture", "economy"],
            },
            {
                "title": "Lagos Traffic Flow Analysis",
                "description": "Real-time traffic flow data and analysis for major roads in Lagos State.",
                "tags": ["transportation", "technology"],
            },
            {
                "title": "Nigerian Banks Customer Data",
                "description": "Anonymized customer data from major Nigerian banks for financial analysis.",
                "tags": ["finance", "economy"],
            },
            {
                "title": "Environmental Monitoring Nigeria",
                "description": "Air quality and environmental monitoring data from sensors across Nigeria.",
                "tags": ["environment", "technology"],
            },
            {
                "title": "Population Census Data Nigeria",
                "description": "Population census data with demographic breakdowns by state and local government.",
                "tags": ["demographics", "governance"],
            },
            {
                "title": "Healthcare Technology Adoption",
                "description": "Study on healthcare technology adoption in Nigerian hospitals and clinics.",
                "tags": ["healthcare", "technology"],
            },
            {
                "title": "Education Technology Nigeria",
                "description": "Data on educational technology usage in Nigerian schools and universities.",
                "tags": ["education", "technology"],
            },
            {
                "title": "Financial Inclusion Nigeria",
                "description": "Data on financial services access and inclusion across Nigeria.",
                "tags": ["finance", "demographics"],
            },
        ]

        created_count = 0
        for data in datasets_data:
            # Check if dataset already exists
            if not Dataset.objects.filter(title=data["title"]).exists():
                dataset = Dataset.objects.create(
                    title=str(data["title"]),
                    description=str(data["description"]),
                    owner=user,
                    status="published",
                    is_public=True,
                    is_approved=True,
                )

                # Add tags
                tag_objects = []
                for tag_name in data["tags"]:
                    matching_tag = next((t for t in tags if t.name == tag_name), None)
                    if matching_tag is not None:
                        tag_objects.append(matching_tag)

                dataset.tags.set(tag_objects)
                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(f'Created dataset: "{dataset.title}"')
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} sample datasets")
        )
