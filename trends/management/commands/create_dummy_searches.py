import random
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

from trends.models import SearchQuery

User = get_user_model()


class Command(BaseCommand):
    help = "Create dummy search queries from multiple users for testing trending functionality"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing search queries before creating new ones",
        )
        parser.add_argument(
            "--queries",
            type=int,
            default=300,
            help="Number of search queries to generate (default: 300)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["clear"]:
            self.stdout.write("Clearing existing search queries...")
            SearchQuery.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing search queries"))

        self.create_dummy_users()
        self.create_dummy_searches(options["queries"])

    def create_dummy_users(self) -> None:
        """Create realistic dummy users."""
        self.stdout.write("Creating dummy users...")

        dummy_users = [
            {"username": "john_researcher", "email": "john.researcher@university.edu"},
            {"username": "mary_analyst", "email": "mary.analyst@government.ng"},
            {"username": "peter_journalist", "email": "peter.journalist@media.com"},
            {"username": "sarah_student", "email": "sarah.student@student.edu"},
            {"username": "david_economist", "email": "david.economist@bank.ng"},
            {"username": "lisa_health", "email": "lisa.health@ministry.ng"},
            {"username": "mike_startup", "email": "mike.startup@tech.ng"},
            {"username": "ada_consultant", "email": "ada.consultant@consulting.com"},
            {"username": "james_ngo", "email": "james.ngo@development.org"},
            {"username": "grace_researcher", "email": "grace.researcher@think-tank.ng"},
        ]

        created_count = 0
        for user_data in dummy_users:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={"username": user_data["username"], "password": "password123"},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} new users"))

    def create_dummy_searches(self, total_queries: int) -> None:
        """Create realistic search queries from multiple users."""
        self.stdout.write(f"Creating {total_queries} search queries...")

        # Get all users
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users found!"))
            return

        # Realistic search queries by category
        search_patterns: dict[str, dict[str, Any]] = {
            "healthcare": {
                "weight": 0.25,  # 25% of searches
                "queries": [
                    "covid data nigeria",
                    "coronavirus statistics",
                    "pandemic data",
                    "health statistics",
                    "medical records",
                    "hospital data",
                    "vaccination rates",
                    "health expenditure",
                    "mortality data",
                    "disease surveillance",
                    "health indicators",
                    "public health data",
                    "maternal health",
                    "child mortality",
                    "immunization data",
                    "malaria statistics",
                    "tuberculosis data",
                    "hiv data nigeria",
                ],
            },
            "economy": {
                "weight": 0.20,  # 20% of searches
                "queries": [
                    "gdp data nigeria",
                    "economic indicators",
                    "inflation rates",
                    "unemployment statistics",
                    "poverty data",
                    "income distribution",
                    "budget allocation",
                    "government spending",
                    "tax revenue",
                    "trade statistics",
                    "export data",
                    "import data",
                    "foreign investment",
                    "economic growth",
                    "fiscal data",
                ],
            },
            "education": {
                "weight": 0.15,  # 15% of searches
                "queries": [
                    "education statistics",
                    "school enrollment",
                    "literacy rates",
                    "university data",
                    "student performance",
                    "education budget",
                    "teacher statistics",
                    "dropout rates",
                    "examination results",
                    "higher education",
                    "primary education",
                    "secondary education",
                ],
            },
            "agriculture": {
                "weight": 0.12,  # 12% of searches
                "queries": [
                    "crop yields",
                    "agricultural production",
                    "farming data",
                    "food security",
                    "livestock statistics",
                    "agricultural exports",
                    "rice production",
                    "cassava data",
                    "maize statistics",
                    "agricultural gdp",
                    "farmer statistics",
                    "irrigation data",
                ],
            },
            "technology": {
                "weight": 0.10,  # 10% of searches
                "queries": [
                    "internet usage",
                    "mobile penetration",
                    "digital payments",
                    "tech adoption",
                    "smartphone data",
                    "connectivity statistics",
                    "broadband access",
                    "social media usage",
                    "e-commerce data",
                    "fintech statistics",
                    "digital banking",
                    "tech investment",
                ],
            },
            "demographics": {
                "weight": 0.10,  # 10% of searches
                "queries": [
                    "population census",
                    "demographic data",
                    "migration patterns",
                    "birth rates",
                    "death rates",
                    "age distribution",
                    "population growth",
                    "urban population",
                    "rural population",
                    "gender statistics",
                    "household data",
                    "family size",
                ],
            },
            "environment": {
                "weight": 0.08,  # 8% of searches
                "queries": [
                    "climate data",
                    "rainfall patterns",
                    "temperature data",
                    "environmental statistics",
                    "pollution data",
                    "deforestation",
                    "carbon emissions",
                    "renewable energy",
                    "water resources",
                    "biodiversity data",
                    "waste management",
                    "air quality",
                ],
            },
        }

        # User preferences (some users search more in certain categories)
        user_preferences = {
            "john.researcher@university.edu": ["healthcare", "education"],
            "mary.analyst@government.ng": ["economy", "demographics"],
            "peter.journalist@media.com": ["healthcare", "economy", "education"],
            "sarah.student@student.edu": ["education", "technology"],
            "david.economist@bank.ng": ["economy", "technology"],
            "lisa.health@ministry.ng": ["healthcare", "demographics"],
            "mike.startup@tech.ng": ["technology", "economy"],
            "ada.consultant@consulting.com": ["economy", "demographics"],
            "james.ngo@development.org": ["agriculture", "environment"],
            "grace.researcher@think-tank.ng": ["healthcare", "economy", "education"],
        }

        # Generate queries
        created_count = 0
        base_time = datetime.now() - timedelta(days=30)

        for _ in range(total_queries):
            # Select user
            user = random.choice(users)

            # Get user's preferred categories or use all categories
            preferred_categories = user_preferences.get(
                user.email, list(search_patterns.keys())
            )

            # Choose category (with some randomness)
            if random.random() < 0.7:  # 70% chance to use preferred category
                category = random.choice(preferred_categories)
            else:  # 30% chance to use any category
                category = random.choices(
                    list(search_patterns.keys()),
                    weights=[
                        float(pattern["weight"]) for pattern in search_patterns.values()
                    ],
                )[0]

            # Choose query from category
            query: str = random.choice(search_patterns[category]["queries"])

            # Add location variation (20% chance)
            if random.random() < 0.2:
                locations = [
                    "lagos",
                    "abuja",
                    "kano",
                    "rivers",
                    "ogun",
                    "kaduna",
                    "oyo",
                ]
                query += f" {random.choice(locations)}"

            # Generate realistic timestamp
            created_at = base_time + timedelta(
                days=random.randint(0, 29),
                hours=random.randint(8, 22),  # Business hours mostly
                minutes=random.randint(0, 59),
            )

            # Create search query
            SearchQuery.objects.create(user=user, query=query, created_at=created_at)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} search queries"))

        # Show summary
        self.show_summary()

    def show_summary(self) -> None:
        """Show summary of created data."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 50)

        total_queries = SearchQuery.objects.count()
        total_users = User.objects.count()

        self.stdout.write(f"Total users: {total_users}")
        self.stdout.write(f"Total search queries: {total_queries}")

        # Show queries per user
        self.stdout.write("\nQueries per user:")
        for user in User.objects.all():
            count = SearchQuery.objects.filter(user=user).count()
            if count > 0:
                self.stdout.write(f"  {user.email}: {count} queries")

        # Show top queries
        self.stdout.write("\nTop 10 most searched queries:")
        from collections import Counter

        queries = SearchQuery.objects.values_list("query", flat=True)
        query_counts = Counter(queries)

        for query, count in query_counts.most_common(10):
            self.stdout.write(f'  "{query}": {count} times')

        self.stdout.write("\n✅ Dummy data created successfully!")
        self.stdout.write(
            "🔥 Test trending endpoint: http://127.0.0.1:8000/api/v1/trends/"
        )
