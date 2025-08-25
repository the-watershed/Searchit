#!/usr/bin/env python3
"""
Test script to populate the enhanced catalog with sample data.
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from db import DB

def create_sample_data():
    """Create some sample catalog items to demonstrate enhanced features."""
    db = DB()
    
    # Sample items with enhanced catalog data
    sample_items = [
        {
            'title': 'Victorian Mahogany Writing Desk',
            'brand': 'Gillows of Lancaster',
            'maker': 'Robert Gillow',
            'category': 'Furniture',
            'subcategory': 'Desk',
            'description': 'Beautifully crafted mahogany writing desk with brass fittings and leather inlay',
            'condition': 'Very Good',
            'era_period': 'Victorian',
            'material': 'Mahogany, Brass, Leather',
            'dimensions': 'H: 30" W: 48" D: 24"',
            'weight': '85 lbs',
            'color_scheme': 'Rich Brown/Gold',
            'rarity': 'Rare',
            'authentication': 'Authenticated',
            'acquisition_date': '2024-03-15',
            'acquisition_source': 'London Antiques Fair',
            'acquisition_cost': 1200.00,
            'insurance_value': 2500.00,
            'location_stored': 'Warehouse A-12',
            'tags': 'writing desk, Victorian, mahogany, Gillows, brass fittings',
            'status': 'Available',
            'public_display': 1,
            'featured_item': 1,
            'provenance_notes': 'Originally from the estate of Lord Hamilton, documented in family records from 1895.',
            'notes': 'Excellent craftsmanship, all original hardware intact.',
            'prc_low': 2000.00,
            'prc_med': 2500.00,
            'prc_hi': 3200.00,
        },
        {
            'title': 'Art Deco Sterling Silver Tea Set',
            'brand': 'Tiffany & Co.',
            'maker': 'Tiffany Studios',
            'category': 'Silver',
            'subcategory': 'Tea Service',
            'description': 'Complete 5-piece Art Deco tea service in sterling silver',
            'condition': 'Excellent',
            'era_period': 'Art Deco',
            'material': 'Sterling Silver',
            'dimensions': 'Teapot: H: 8" W: 12" D: 6"',
            'weight': '4.2 lbs total',
            'color_scheme': 'Silver',
            'rarity': 'Very Rare',
            'authentication': 'Certificate of Authenticity',
            'acquisition_date': '2024-01-20',
            'acquisition_source': 'Private Collection',
            'acquisition_cost': 2800.00,
            'insurance_value': 4500.00,
            'location_stored': 'Safe B-03',
            'tags': 'Tiffany, Art Deco, sterling silver, tea set, 1920s',
            'status': 'Available',
            'public_display': 1,
            'featured_item': 1,
            'provenance_notes': 'Wedding gift to the Astors in 1925, family documentation included.',
            'notes': 'Complete with original presentation case, minor tarnishing on base.',
            'prc_low': 4000.00,
            'prc_med': 4500.00,
            'prc_hi': 5500.00,
        },
        {
            'title': 'Chinese Ming Vase',
            'brand': '',
            'maker': 'Unknown Imperial Artisan',
            'category': 'Ceramics',
            'subcategory': 'Vase',
            'description': 'Blue and white porcelain vase with dragon motif',
            'condition': 'Good',
            'era_period': 'Ming Dynasty',
            'material': 'Porcelain',
            'dimensions': 'H: 14" D: 8"',
            'weight': '3.5 lbs',
            'color_scheme': 'Blue/White',
            'rarity': 'Unique',
            'authentication': 'Questionable',
            'acquisition_date': '2024-02-10',
            'acquisition_source': 'Estate Sale',
            'acquisition_cost': 350.00,
            'insurance_value': 1200.00,
            'location_stored': 'Display Case 5',
            'tags': 'Ming, Chinese, porcelain, dragon, blue and white',
            'status': 'Under Restoration',
            'public_display': 0,
            'featured_item': 0,
            'provenance_notes': 'Needs authentication, possible 19th century reproduction.',
            'notes': 'Small chip on base, restoration in progress.',
            'prc_low': 800.00,
            'prc_med': 1200.00,
            'prc_hi': 2000.00,
        },
        {
            'title': 'Mid-Century Modern Chair',
            'brand': 'Herman Miller',
            'maker': 'Charles Eames',
            'category': 'Furniture',
            'subcategory': 'Chair',
            'description': 'Iconic Eames lounge chair in black leather',
            'condition': 'Near Mint',
            'era_period': 'Mid-Century Modern',
            'material': 'Molded Plywood, Leather, Steel',
            'dimensions': 'H: 32" W: 32" D: 32"',
            'weight': '45 lbs',
            'color_scheme': 'Black/Walnut',
            'rarity': 'Uncommon',
            'authentication': 'Authenticated',
            'acquisition_date': '2024-04-05',
            'acquisition_source': 'Design Auction House',
            'acquisition_cost': 3200.00,
            'insurance_value': 4000.00,
            'location_stored': 'Showroom Floor',
            'tags': 'Eames, Herman Miller, mid-century, modern, chair, leather',
            'status': 'Available',
            'public_display': 1,
            'featured_item': 1,
            'provenance_notes': 'Original 1960s production, Herman Miller label intact.',
            'notes': 'Excellent condition, all original components.',
            'prc_low': 3800.00,
            'prc_med': 4200.00,
            'prc_hi': 5000.00,
        },
        {
            'title': 'Vintage Rolex Submariner',
            'brand': 'Rolex',
            'maker': 'Rolex SA',
            'category': 'Watches',
            'subcategory': 'Diving Watch',
            'description': 'Vintage 1970s Submariner reference 5513',
            'condition': 'Very Good',
            'era_period': '1970s',
            'material': 'Stainless Steel',
            'dimensions': 'Case: 40mm',
            'weight': '140g',
            'color_scheme': 'Black/Steel',
            'rarity': 'Rare',
            'authentication': 'Certificate of Authenticity',
            'acquisition_date': '2024-05-12',
            'acquisition_source': 'Watch Specialist',
            'acquisition_cost': 8500.00,
            'insurance_value': 12000.00,
            'location_stored': 'Security Vault',
            'tags': 'Rolex, Submariner, vintage, diving watch, 1970s',
            'status': 'Sold',
            'public_display': 0,
            'featured_item': 0,
            'provenance_notes': 'Service records from authorized dealer, matching serial numbers.',
            'notes': 'Recently serviced, keeps excellent time.',
            'prc_low': 10000.00,
            'prc_med': 11500.00,
            'prc_hi': 13500.00,
        }
    ]
    
    print("Adding sample catalog items...")
    
    for i, item_data in enumerate(sample_items, 1):
        try:
            # Create a minimal OpenAI result JSON for the basic fields
            basic_fields = {
                'title': item_data.get('title', ''),
                'brand': item_data.get('brand', ''),
                'maker': item_data.get('maker', ''),
                'description': item_data.get('description', ''),
                'condition': item_data.get('condition', ''),
                'provenance_notes': item_data.get('provenance_notes', ''),
            }
            
            import json
            openai_result = json.dumps(basic_fields)
            
            # Use the existing add_item method
            item_id = db.add_item(
                image_path="",  # No images for this demo
                notes=item_data.get('notes', ''),
                openai_result=openai_result
            )
            
            # Now update with all the enhanced fields
            enhanced_fields = {k: v for k, v in item_data.items() 
                             if k not in ['notes']}  # Include all fields
            
            success = db.update_item_fields(item_id, enhanced_fields)
            
            if success:
                print(f"✅ Added item {i}: {item_data['title']}")
            else:
                print(f"⚠️ Added item {i} but failed to update enhanced fields: {item_data['title']}")
                
        except Exception as e:
            print(f"❌ Failed to add item {i}: {e}")
    
    print(f"\n🎉 Sample data creation complete! Added {len(sample_items)} items.")
    print("You can now test the enhanced catalog features:")
    print("- Search across all fields")
    print("- Filter by category, status, condition, rarity")
    print("- Sort by multiple columns")
    print("- Export to CSV")
    print("- Edit items with full enhanced fields")

if __name__ == "__main__":
    create_sample_data()
