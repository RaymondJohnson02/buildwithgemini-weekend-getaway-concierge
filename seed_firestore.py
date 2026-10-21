#!/usr/bin/env python3
"""Seed Firestore with curated weekend getaway packages and food tour items."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-9c93db10a08a"

SEED_PACKAGES = [
    {
        "id": "sf-fog-foodie",
        "title": "48 Hours in San Francisco: Mission Burritos & Waterfront Seafood",
        "city": "San Francisco",
        "state": "CA",
        "duration_hours": 48,
        "theme": "Food & Scenic Views",
        "estimated_budget_usd": 450,
        "cuisines": ["Mexican", "Seafood", "Artisan Bakery", "Dim Sum"],
        "highlights": [
            "Mission District Taqueria crawl (carne asada & al pastor)",
            "Ferry Building Farmer's Market artisan tasting",
            "Chinatown historic dim sum tea house experience",
            "North Beach Italian espresso & cannoli walk"
        ],
        "itinerary_preview": [
            {"day": "Saturday Morning", "activity": "Tartine Bakery & Mission Dolores Park picnic"},
            {"day": "Saturday Evening", "activity": "La Taqueria & rooftop cocktail in Mission"},
            {"day": "Sunday Morning", "activity": "Ferry Building oysters & Blue Bottle coffee"},
            {"day": "Sunday Afternoon", "activity": "Dim sum in Chinatown & walk across Golden Gate Vista"}
        ]
    },
    {
        "id": "nyc-greenwich-gastronomy",
        "title": "NYC Weekend: Village Trattorias & Speakeasy Bites",
        "city": "New York",
        "state": "NY",
        "duration_hours": 48,
        "theme": "Urban Food Tour",
        "estimated_budget_usd": 600,
        "cuisines": ["Italian", "Jewish Deli", "Speakeasy Cocktails", "NY Pizza"],
        "highlights": [
            "West Village wood-fired pizza & fresh pasta tasting",
            "Lower East Side pastrami on rye & pickle bar tradition",
            "Hidden speakeasy craft cocktails and small plates in East Village",
            "Chelsea Market artisan food crawl & High Line walk"
        ],
        "itinerary_preview": [
            {"day": "Saturday Morning", "activity": "Katz's Delicatessen & Russ & Daughters appetizing"},
            {"day": "Saturday Evening", "activity": "West Village fresh pasta supper & jazz bar"},
            {"day": "Sunday Morning", "activity": "Bagel brunch with smoked lox & High Line stroll"},
            {"day": "Sunday Afternoon", "activity": "Joe's Pizza slice tour & artisanal gelato"}
        ]
    },
    {
        "id": "austin-tacos-smoke",
        "title": "Austin Weekend: Central Texas BBQ & Craft Taco Crawl",
        "city": "Austin",
        "state": "TX",
        "duration_hours": 48,
        "theme": "BBQ & Craft Beers",
        "estimated_budget_usd": 380,
        "cuisines": ["Texas BBQ", "Tex-Mex", "Craft Beer", "Breakfast Tacos"],
        "highlights": [
            "Franklin BBQ / Terry Black's smoked brisket & ribs masterclass",
            "South Congress street taco trail & queso tastings",
            "Rainey Street craft beer garden hopping & live music",
            "Barton Springs morning dip followed by migas breakfast tacos"
        ],
        "itinerary_preview": [
            {"day": "Saturday Morning", "activity": "Veracruz All Natural breakfast taco trailer"},
            {"day": "Saturday Afternoon", "activity": "Post oak smoked brisket feast & local cider"},
            {"day": "Sunday Morning", "activity": "Barton Springs swim & cold brew coffee"},
            {"day": "Sunday Evening", "activity": "Rainey street food truck park & live honky tonk"}
        ]
    },
    {
        "id": "portland-craft-carts",
        "title": "Portland Weekend: Food Pods, Micro-Roasters & Farm-to-Table",
        "city": "Portland",
        "state": "OR",
        "duration_hours": 48,
        "theme": "Artisanal & Coffee Culture",
        "estimated_budget_usd": 350,
        "cuisines": ["Pacific Northwest", "Thai", "Specialty Coffee", "Donuts & Pastries"],
        "highlights": [
            "Hawthorne & Central Eastside food cart pod crawl",
            "Third-wave micro-roastery single-origin coffee flight",
            "Farm-to-table Pacific Northwest seasonal dinner",
            "Artisanal ice cream and gourmet brioche donuts"
        ],
        "itinerary_preview": [
            {"day": "Saturday Morning", "activity": "Coava Coffee flight & Pip's original warm donuts"},
            {"day": "Saturday Afternoon", "activity": "Cartopia food cart sampling (gourmet poutine & Thai chicken)"},
            {"day": "Sunday Morning", "activity": "Forest Park trail hike & local brunch"},
            {"day": "Sunday Evening", "activity": "Willamette Valley Pinot Noir tasting & wood-fired dining"}
        ]
    }
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("getaway_packages")
    print(f"Connecting to Firestore for project: {PROJECT_ID}")

    for package in SEED_PACKAGES:
        doc_id = package["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(package)
        print(f"  ✓ Seeded package: {doc_id} -> {package['title']}")

    print("\nFirestore successfully seeded with weekend getaway packages!")


if __name__ == "__main__":
    seed_database()
