"""
DB: Handles all SQLite operations for items, revision history, and price tracking.
"""
import sqlite3
import os
import datetime
import json

DB_PATH = "provenance.db"


class DB:
    # --- Internal helpers ---
    def _coerce_json_obj(self, openai_result):
        """Best-effort conversion of a string response into a JSON object (dict).
        - Accepts raw JSON string.
        - If embedded in prose or code fences, extracts the first {...} block.
        - Returns dict on success, else None.
        """
        if not openai_result:
            return None
        try:
            if isinstance(openai_result, dict):
                return openai_result
            if isinstance(openai_result, str):
                # Try direct parse
                return json.loads(openai_result)
        except Exception:
            pass
        # Try to extract JSON object from within text
        if isinstance(openai_result, str):
            s = openai_result.strip()
            # Strip Markdown code fences if present
            if s.startswith("```"):
                try:
                    s = s.strip('`')
                except Exception:
                    pass
            try:
                start = s.find('{')
                end = s.rfind('}')
                if start != -1 and end != -1 and end > start:
                    maybe = s[start:end+1]
                    return json.loads(maybe)
            except Exception:
                return None
        return None
    # --- Images helpers ---
    def add_image(self, item_id, image_path, annotation=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO images (item_id, image_path, annotation) VALUES (?, ?, ?)", (item_id, image_path, annotation))
        self.conn.commit()

    def get_images(self, item_id):
        c = self.conn.cursor()
        c.execute("SELECT image_path FROM images WHERE item_id=?", (item_id,))
        return [row[0] for row in c.fetchall()]

    def get_image_annotations(self, item_id):
        """Return list of annotation texts for the item's images (empty strings filtered out)."""
        try:
            c = self.conn.cursor()
            c.execute("SELECT annotation FROM images WHERE item_id=?", (item_id,))
            return [row[0] for row in c.fetchall() if row and row[0]]
        except Exception:
            return []

    def get_image_annotation(self, item_id: int, image_path: str) -> str:
        """Return annotation text for a specific image path, if present in images table; else ''."""
        try:
            c = self.conn.cursor()
            c.execute("SELECT annotation FROM images WHERE item_id=? AND image_path=? LIMIT 1", (item_id, image_path))
            row = c.fetchone()
            if row and row[0]:
                return row[0]
        except Exception:
            pass
        return ""

    def update_image_annotation(self, item_id: int, image_path: str, annotation: str):
        """Update or create an annotation for a specific image path.
        If an images row exists, update it; otherwise, insert a new one to persist the note.
        Also records an image_history entry.
        """
        try:
            c = self.conn.cursor()
            c.execute(
                "UPDATE images SET annotation=? WHERE item_id=? AND image_path=?",
                (annotation, item_id, image_path),
            )
            if c.rowcount == 0:
                c.execute(
                    "INSERT INTO images (item_id, image_path, annotation) VALUES (?, ?, ?)",
                    (item_id, image_path, annotation),
                )
            self.conn.commit()
            try:
                self.record_image_action(item_id, image_path, "annotate", annotation)
            except Exception:
                pass
        except Exception:
            pass

    def replace_image_path(self, item_id: int, old_path: str, new_path: str):
        """Replace an image path for an item. Updates images table if present; otherwise updates legacy items.image_path.
        Records image_history.
        """
        try:
            c = self.conn.cursor()
            # Try images table first
            c.execute(
                "UPDATE images SET image_path=? WHERE item_id=? AND image_path=?",
                (new_path, item_id, old_path),
            )
            affected = c.rowcount
            if affected == 0:
                # Maybe it's the legacy primary path on items
                c.execute(
                    "UPDATE items SET image_path=? WHERE id=? AND image_path=?",
                    (new_path, item_id, old_path),
                )
            self.conn.commit()
            try:
                self.record_image_action(item_id, new_path, "replace", f"from:{old_path}")
            except Exception:
                pass
        except Exception:
            pass

    def delete_image_path(self, item_id: int, image_path: str):
        """Delete an image path from an item. Removes from images table; if not present, clears legacy items.image_path when matching.
        Records image_history.
        """
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM images WHERE item_id=? AND image_path=?", (item_id, image_path))
            affected = c.rowcount
            if affected == 0:
                # If legacy path matches, clear it
                c.execute("UPDATE items SET image_path=NULL WHERE id=? AND image_path=?", (item_id, image_path))
            self.conn.commit()
            try:
                self.record_image_action(item_id, image_path, "delete", "")
            except Exception:
                pass
        except Exception:
            pass

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()
        self._migrate_prices_to_columns()
        self._migrate_drop_value_columns()

    def create_tables(self):
        c = self.conn.cursor()
        # Items (no legacy 'value')
        c.execute(
            '''CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                notes TEXT,
                openai_result TEXT,
                created_at TEXT,
                title TEXT,
                brand TEXT,
                maker TEXT,
                description TEXT,
                condition TEXT,
                provenance_notes TEXT,
                prc_low REAL,
                prc_med REAL,
                prc_hi REAL
            )'''
        )
        # Add columns if missing (idempotent guards)
        additional_columns = [
            ("title", "TEXT"),
            ("brand", "TEXT"),
            ("maker", "TEXT"),
            ("description", "TEXT"),
            ("condition", "TEXT"),
            ("provenance_notes", "TEXT"),
            ("prc_low", "REAL"),
            ("prc_med", "REAL"),
            ("prc_hi", "REAL"),
            # Enhanced cataloging fields
            ("category", "TEXT"),           # e.g., "Furniture", "Jewelry", "Art", "Books"
            ("subcategory", "TEXT"),        # e.g., "Chair", "Ring", "Painting", "Novel"
            ("era_period", "TEXT"),         # e.g., "Victorian", "Art Deco", "Mid-Century Modern"
            ("material", "TEXT"),           # e.g., "Wood", "Silver", "Oil on Canvas", "Paper"
            ("dimensions", "TEXT"),         # e.g., "12\"x8\"x3\"", "H: 36\" W: 24\" D: 18\""
            ("weight", "TEXT"),             # e.g., "2.5 lbs", "850g"
            ("color_scheme", "TEXT"),       # e.g., "Brown/Gold", "Blue/White", "Multicolor"
            ("rarity", "TEXT"),             # e.g., "Common", "Uncommon", "Rare", "Very Rare", "Unique"
            ("authentication", "TEXT"),     # e.g., "Authenticated", "Certificate of Authenticity", "Unsigned", "Questionable"
            ("acquisition_date", "TEXT"),   # When was it acquired
            ("acquisition_source", "TEXT"), # Where was it acquired from
            ("acquisition_cost", "REAL"),   # What was paid for it
            ("insurance_value", "REAL"),    # Current insurance value
            ("location_stored", "TEXT"),    # Where is it physically stored
            ("tags", "TEXT"),               # Comma-separated tags for flexible categorization
            ("status", "TEXT"),             # e.g., "Available", "Sold", "On Hold", "Damaged", "Under Restoration"
            ("public_display", "INTEGER"),  # 0/1 boolean - should this be visible in public catalogs
            ("featured_item", "INTEGER"),   # 0/1 boolean - is this a featured/highlighted item
            ("last_updated", "TEXT"),       # Track when item was last modified
        ]
        for col, col_type in additional_columns:
            try:
                c.execute(f'ALTER TABLE items ADD COLUMN {col} {col_type}')
            except Exception:
                pass

        # Other tables
        # Add annotation column to images table if missing
        c.execute(
            '''CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                image_path TEXT,
                annotation TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )'''
        )
        # Try to add annotation column if it doesn't exist (idempotent)
        try:
            c.execute('ALTER TABLE images ADD COLUMN annotation TEXT')
        except Exception:
            pass
        c.execute(
            '''CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                notes TEXT,
                timestamp TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )'''
        )
        c.execute(
            '''CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                price TEXT,
                timestamp TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )'''
        )
        c.execute(
            '''CREATE TABLE IF NOT EXISTS item_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )'''
        )
        c.execute(
            '''CREATE TABLE IF NOT EXISTS image_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                image_path TEXT,
                action TEXT,
                meta TEXT,
                timestamp TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )'''
        )
        self.conn.commit()

    def add_item(self, image_path, notes, openai_result):
        # Extract provenance and prices
        fields = self.extract_provenance_fields(openai_result)
        prices = self.extract_prices(openai_result)

        # Compute low/med/high now
        prc_low = prc_med = prc_hi = None
        if prices:
            prices.sort()
            prc_low = prices[0]
            prc_hi = prices[-1]
            n = len(prices)
            prc_med = prices[n // 2] if n % 2 == 1 else (prices[n // 2 - 1] + prices[n // 2]) / 2

        c = self.conn.cursor()
        c.execute(
            '''
            INSERT INTO items (
                image_path, notes, openai_result, created_at,
                title, brand, maker, description, condition, provenance_notes,
                prc_low, prc_med, prc_hi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                image_path, notes, openai_result, datetime.datetime.now().isoformat(),
                fields.get('title', ''), fields.get('brand', ''), fields.get('maker', ''), fields.get('description', ''),
                fields.get('condition', ''), fields.get('provenance_notes', ''),
                prc_low, prc_med, prc_hi,
            ),
        )
        item_id = c.lastrowid
        self.conn.commit()
        self.add_revision(item_id, notes)
        for price in prices:
            self.add_price(item_id, price)
        return item_id

    # --- Fetch helpers ---
    def get_item(self, item_id):
        c = self.conn.cursor()
        c.execute(
            '''
            SELECT id, image_path, notes, openai_result, created_at,
                   title, brand, maker, description, condition, provenance_notes,
                   prc_low, prc_med, prc_hi,
                   category, subcategory, era_period, material, dimensions, weight,
                   color_scheme, rarity, authentication, acquisition_date, acquisition_source,
                   acquisition_cost, insurance_value, location_stored, tags, status,
                   public_display, featured_item, last_updated
            FROM items WHERE id=?
            ''',
            (item_id,),
        )
        row = c.fetchone()
        if not row:
            return None
        keys = [
            'id', 'image_path', 'notes', 'openai_result', 'created_at',
            'title', 'brand', 'maker', 'description', 'condition', 'provenance_notes',
            'prc_low', 'prc_med', 'prc_hi',
            'category', 'subcategory', 'era_period', 'material', 'dimensions', 'weight',
            'color_scheme', 'rarity', 'authentication', 'acquisition_date', 'acquisition_source',
            'acquisition_cost', 'insurance_value', 'location_stored', 'tags', 'status',
            'public_display', 'featured_item', 'last_updated'
        ]
        item = dict(zip(keys, row))
        item['images'] = self.get_images(item_id)
        item['history'] = self.get_revision_history(item_id)
        return item

    def extract_provenance_fields(self, openai_result):
        fields = {k: '' for k in ['title', 'brand', 'maker', 'description', 'condition', 'provenance_notes']}
        if not openai_result:
            return fields
        # Try JSON first (with synonyms)
        data = self._coerce_json_obj(openai_result)
        if isinstance(data, dict):
            # Map common synonyms to our schema
            synonyms = {
                'title': ['title', 'name', 'object_title', 'item_title'],
                'brand': ['brand', 'brand_name'],
                'maker': ['maker', 'manufacturer', 'artist', 'creator', 'author'],
                'description': ['description', 'summary', 'details'],
                'condition': ['condition', 'condition_notes', 'state'],
                'provenance_notes': ['provenance_notes', 'provenance', 'history', 'notes_provenance'],
            }
            for key, keys in synonyms.items():
                for k in keys:
                    v = data.get(k)
                    if isinstance(v, str) and v:
                        fields[key] = v
                        break
            if any(fields.values()):
                return fields
        # Fallback to regex parsing of labeled text
        import re
        for line in openai_result.splitlines():
            for k in fields:
                pattern = re.compile(rf'^{k}[\s_]*:', re.IGNORECASE)
                if pattern.match(line.strip()):
                    fields[k] = line.split(':', 1)[-1].strip()
        if all(not v for v in fields.values()):
            fields['provenance_notes'] = openai_result.strip()
        return fields

    def extract_title(self, openai_result):
        if not openai_result:
            return ''
        for line in openai_result.splitlines():
            if 'title:' in line.lower():
                return line.split(':', 1)[-1].strip()
        for line in openai_result.splitlines():
            if line.strip():
                return line.strip()
        return ''

    def extract_prices(self, openai_result):
        import re
        prices = []
        if not openai_result:
            return prices
        # Try JSON first (with coercion from strings like "$1,234")
        data = self._coerce_json_obj(openai_result)
        if isinstance(data, dict):
            p = data.get('prices') or {}
            def _to_float(x):
                if x is None:
                    return None
                if isinstance(x, (int, float)):
                    return float(x)
                if isinstance(x, str):
                    try:
                        m = re.search(r"([0-9][0-9,]*\.?[0-9]*)", x)
                        if m:
                            return float(m.group(1).replace(',', ''))
                    except Exception:
                        return None
                return None
            for key in ('low', 'median', 'high'):
                val = _to_float(p.get(key))
                if val is not None:
                    prices.append(val)
            if prices:
                return prices
        # Fallback to $-amount regex
        for line in openai_result.splitlines():
            matches = re.findall(r'\$([0-9,.]+)', line)
            for m in matches:
                try:
                    prices.append(float(m.replace(',', '')))
                except Exception:
                    pass
        return prices

    def get_price_range(self, item_id):
        c = self.conn.cursor()
        # Prefer stored columns if present
        try:
            c.execute("SELECT prc_low, prc_med, prc_hi FROM items WHERE id=?", (item_id,))
            pr = c.fetchone()
            if pr and any(pr):
                return tuple(pr)
        except Exception:
            pass
        # Fallback to compute from price entries
        c.execute("SELECT price FROM prices WHERE item_id=?", (item_id,))
        prices = [float(row[0]) for row in c.fetchall() if row[0] is not None]
        if not prices:
            return ('', '', '')
        prices.sort()
        n = len(prices)
        low = prices[0]
        high = prices[-1]
        med = prices[n // 2] if n % 2 == 1 else (prices[n // 2 - 1] + prices[n // 2]) / 2
        try:
            c.execute("UPDATE items SET prc_low=?, prc_med=?, prc_hi=? WHERE id=?", (low, med, high, item_id))
            self.conn.commit()
        except Exception:
            pass
        return (low, med, high)

    def add_revision(self, item_id, notes):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO revisions (item_id, notes, timestamp) VALUES (?, ?, ?)",
            (item_id, notes, datetime.datetime.now().isoformat()),
        )
        self.conn.commit()

    def add_price(self, item_id, price):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO prices (item_id, price, timestamp) VALUES (?, ?, ?)",
            (item_id, price, datetime.datetime.now().isoformat()),
        )
        self.conn.commit()

    def update_item_analysis(self, item_id, new_openai_result):
        """Update an existing item with a new OpenAI result, refreshing fields and prices.
        Records changes and adds a revision. Safe to call repeatedly.
        """
        try:
            # Get current item for change tracking
            current = self.get_item(item_id) or {}
            old_fields = {
                'title': current.get('title', ''),
                'brand': current.get('brand', ''),
                'maker': current.get('maker', ''),
                'description': current.get('description', ''),
                'condition': current.get('condition', ''),
                'provenance_notes': current.get('provenance_notes', ''),
            }
            # Extract values from new result
            fields = self.extract_provenance_fields(new_openai_result)
            prices = self.extract_prices(new_openai_result)
            prc_low = prc_med = prc_hi = None
            if prices:
                prices.sort()
                prc_low = prices[0]
                prc_hi = prices[-1]
                n = len(prices)
                prc_med = prices[n // 2] if n % 2 == 1 else (prices[n // 2 - 1] + prices[n // 2]) / 2

            # Update items row
            c = self.conn.cursor()
            c.execute(
                '''UPDATE items SET
                       openai_result=?,
                       title=?, brand=?, maker=?, description=?, condition=?, provenance_notes=?,
                       prc_low=?, prc_med=?, prc_hi=?
                   WHERE id=?''',
                (
                    new_openai_result,
                    fields.get('title', ''), fields.get('brand', ''), fields.get('maker', ''), fields.get('description', ''),
                    fields.get('condition', ''), fields.get('provenance_notes', ''),
                    prc_low, prc_med, prc_hi,
                    item_id,
                ),
            )
            self.conn.commit()

            # Record field changes
            for k, old_val in old_fields.items():
                self.record_change(item_id, k, old_val, fields.get(k, ''))

            # Add revision note
            self.add_revision(item_id, "AI re-evaluation updated metadata.")

            # Store individual prices
            for p in prices:
                try:
                    self.add_price(item_id, p)
                except Exception:
                    pass
        except Exception:
            # Best-effort update; ignore failures to keep UI responsive
            pass

    def update_item_fields(self, item_id, fields):
        """Update item with enhanced field support.
        
        Args:
            item_id (int): ID of item to update
            fields (dict): Dictionary of field names and values to update
        """
        try:
            # Get current item data for change tracking
            current_item = self.get_item(item_id)
            if not current_item:
                return False
            
            # Build dynamic UPDATE query
            update_fields = []
            params = []
            
            # Define all updatable fields
            updatable_fields = [
                'title', 'brand', 'maker', 'description', 'condition', 'provenance_notes',
                'notes', 'prc_low', 'prc_med', 'prc_hi', 'category', 'subcategory',
                'era_period', 'material', 'dimensions', 'weight', 'color_scheme',
                'rarity', 'authentication', 'acquisition_date', 'acquisition_source',
                'acquisition_cost', 'insurance_value', 'location_stored', 'tags',
                'status', 'public_display', 'featured_item'
            ]
            
            # Always update last_updated timestamp
            import datetime
            fields['last_updated'] = datetime.datetime.now().isoformat()
            
            # Build SET clause
            for field, value in fields.items():
                if field in updatable_fields or field == 'last_updated':
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return False
            
            params.append(item_id)  # For WHERE clause
            
            # Execute update
            c = self.conn.cursor()
            query = f"UPDATE items SET {', '.join(update_fields)} WHERE id = ?"
            c.execute(query, params)
            self.conn.commit()
            
            # Record field changes
            for field, new_value in fields.items():
                if field in updatable_fields:  # Don't log last_updated changes
                    old_value = current_item.get(field, '')
                    if str(old_value) != str(new_value):
                        self.record_change(item_id, field, str(old_value), str(new_value))
            
            return True
            
        except Exception as e:
            print(f"Error updating item {item_id}: {e}")
            return False

    def record_change(self, item_id, field, old_value, new_value):
        """Record a field change in the item_changes table."""
        try:
            import datetime
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO item_changes (item_id, field, old_value, new_value, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, field, old_value, new_value, datetime.datetime.now().isoformat())
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error recording change for item {item_id}: {e}")

    def get_all_items(self):
        c = self.conn.cursor()
        c.execute(
            '''
            SELECT id, image_path, notes, created_at,
                   title, brand, maker, description, condition, provenance_notes,
                   prc_low, prc_med, prc_hi
            FROM items
            ORDER BY id DESC
            '''
        )
        items = []
        for row in c.fetchall():
            item_id = row[0]
            # Use already fetched price data instead of calling get_price_range
            prc_low, prc_med, prc_hi = row[10], row[11], row[12]
            
            # Only fetch revision history when specifically needed, not in bulk operations
            items.append(
                {
                    'id': item_id,
                    'image_path': row[1],
                    'notes': row[2],
                    'created_at': row[3],
                    'title': row[4] or '',
                    'brand': row[5] or '',
                    'maker': row[6] or '',
                    'description': row[7] or '',
                    'condition': row[8] or '',
                    'provenance_notes': row[9] or '',
                    'prc_low': prc_low or 0.0,
                    'prc_med': prc_med or 0.0,
                    'prc_hi': prc_hi or 0.0,
                }
            )
        return items

    def get_all_items_enhanced(self, search_text=None, filters=None, limit=None, offset=None):
        """Enhanced item retrieval with search and filtering capabilities.
        
        Args:
            search_text (str): Text to search across all text fields
            filters (dict): Field-specific filters {field_name: value_or_list}
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip (for pagination)
        
        Returns:
            dict: {items: [...], total_count: int, filtered_count: int}
        """
        c = self.conn.cursor()
        
        # Build the base query with all available columns
        base_query = '''
            SELECT id, image_path, notes, created_at,
                   title, brand, maker, description, condition, provenance_notes,
                   prc_low, prc_med, prc_hi,
                   category, subcategory, era_period, material, dimensions, weight,
                   color_scheme, rarity, authentication, acquisition_date, acquisition_source,
                   acquisition_cost, insurance_value, location_stored, tags, status,
                   public_display, featured_item, last_updated
            FROM items
        '''
        
        # Build WHERE conditions
        where_conditions = []
        params = []
        
        # Text search across multiple fields
        if search_text and search_text.strip():
            search_text = search_text.strip()
            search_conditions = [
                "title LIKE ?",
                "brand LIKE ?", 
                "maker LIKE ?",
                "description LIKE ?",
                "condition LIKE ?",
                "provenance_notes LIKE ?",
                "notes LIKE ?",
                "category LIKE ?",
                "subcategory LIKE ?",
                "era_period LIKE ?",
                "material LIKE ?",
                "tags LIKE ?",
                "location_stored LIKE ?"
            ]
            where_conditions.append(f"({' OR '.join(search_conditions)})")
            search_param = f"%{search_text}%"
            params.extend([search_param] * len(search_conditions))
        
        # Field-specific filters
        if filters:
            for field, value in filters.items():
                if value is None or value == '':
                    continue
                    
                if isinstance(value, list):
                    # Multiple values (OR condition)
                    if value:
                        placeholders = ','.join(['?'] * len(value))
                        where_conditions.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                elif isinstance(value, dict):
                    # Range filters (for numeric fields)
                    if 'min' in value and value['min'] is not None:
                        where_conditions.append(f"{field} >= ?")
                        params.append(value['min'])
                    if 'max' in value and value['max'] is not None:
                        where_conditions.append(f"{field} <= ?")
                        params.append(value['max'])
                else:
                    # Single value
                    where_conditions.append(f"{field} = ?")
                    params.append(value)
        
        # Combine WHERE conditions
        query = base_query
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Get total count before applying limit/offset
        count_query = f"SELECT COUNT(*) FROM items"
        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions)
        
        c.execute(count_query, params)
        filtered_count = c.fetchone()[0]
        
        # Get total count (unfiltered)
        c.execute("SELECT COUNT(*) FROM items")
        total_count = c.fetchone()[0]
        
        # Add ordering and pagination
        query += " ORDER BY id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            if offset:
                query += " OFFSET ?"
                params.append(offset)
        
        # Execute main query
        c.execute(query, params)
        items = []
        for row in c.fetchall():
            item = {
                'id': row[0],
                'image_path': row[1],
                'notes': row[2],
                'created_at': row[3],
                'title': row[4] or '',
                'brand': row[5] or '',
                'maker': row[6] or '',
                'description': row[7] or '',
                'condition': row[8] or '',
                'provenance_notes': row[9] or '',
                'prc_low': row[10] or 0.0,
                'prc_med': row[11] or 0.0,
                'prc_hi': row[12] or 0.0,
                'category': row[13] or '',
                'subcategory': row[14] or '',
                'era_period': row[15] or '',
                'material': row[16] or '',
                'dimensions': row[17] or '',
                'weight': row[18] or '',
                'color_scheme': row[19] or '',
                'rarity': row[20] or '',
                'authentication': row[21] or '',
                'acquisition_date': row[22] or '',
                'acquisition_source': row[23] or '',
                'acquisition_cost': row[24] or 0.0,
                'insurance_value': row[25] or 0.0,
                'location_stored': row[26] or '',
                'tags': row[27] or '',
                'status': row[28] or 'Available',
                'public_display': bool(row[29]) if row[29] is not None else True,
                'featured_item': bool(row[30]) if row[30] is not None else False,
                'last_updated': row[31] or '',
            }
            items.append(item)
        
        return {
            'items': items,
            'total_count': total_count,
            'filtered_count': filtered_count
        }

    def get_filter_options(self):
        """Get all unique values for filterable fields to populate filter dropdowns."""
        c = self.conn.cursor()
        
        filter_fields = [
            'category', 'subcategory', 'era_period', 'material', 'condition',
            'rarity', 'authentication', 'status', 'location_stored', 'brand', 'maker'
        ]
        
        options = {}
        for field in filter_fields:
            try:
                c.execute(f"SELECT DISTINCT {field} FROM items WHERE {field} IS NOT NULL AND {field} != '' ORDER BY {field}")
                options[field] = [row[0] for row in c.fetchall()]
            except Exception:
                options[field] = []
        
        # Get price ranges for slider filters
        try:
            c.execute("SELECT MIN(prc_low), MAX(prc_hi), MIN(acquisition_cost), MAX(insurance_value) FROM items")
            row = c.fetchone()
            if row:
                options['price_range'] = {
                    'min_price': row[0] or 0,
                    'max_price': row[1] or 0,
                    'min_acquisition': row[2] or 0,
                    'max_insurance': row[3] or 0
                }
        except Exception:
            options['price_range'] = {'min_price': 0, 'max_price': 0, 'min_acquisition': 0, 'max_insurance': 0}
        
        return options

    # --- Migration helpers ---
    def _migrate_prices_to_columns(self):
        """Backfill prc_low/med/hi columns for existing rows if empty."""
        try:
            c = self.conn.cursor()
            c.execute("SELECT id, prc_low, prc_med, prc_hi FROM items")
            rows = c.fetchall()
            for item_id, lo, me, hi in rows:
                if lo is None and me is None and hi is None:
                    low, med, high = self.get_price_range(item_id)
                    if any((low, med, high)):
                        try:
                            c.execute("UPDATE items SET prc_low=?, prc_med=?, prc_hi=? WHERE id=?", (low, med, high, item_id))
                        except Exception:
                            pass
            self.conn.commit()
        except Exception:
            pass

    def get_revision_history(self, item_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT notes, timestamp FROM revisions WHERE item_id=? ORDER BY timestamp DESC",
            (item_id,),
        )
        return c.fetchall()

    # --- Schema migration: drop deprecated 'value' columns ---
    def _migrate_drop_value_columns(self):
        """If legacy 'value' columns exist in items or revisions, rebuild tables without them."""
        try:
            c = self.conn.cursor()

            def has_col(table, col):
                c.execute(f"PRAGMA table_info({table})")
                return any(r[1] == col for r in c.fetchall())

            c.execute("PRAGMA foreign_keys=OFF")

            if has_col('items', 'value'):
                c.execute(
                    '''CREATE TABLE IF NOT EXISTS items_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_path TEXT,
                        notes TEXT,
                        openai_result TEXT,
                        created_at TEXT,
                        title TEXT,
                        brand TEXT,
                        maker TEXT,
                        description TEXT,
                        condition TEXT,
                        provenance_notes TEXT,
                        prc_low REAL,
                        prc_med REAL,
                        prc_hi REAL
                    )'''
                )
                c.execute(
                    '''INSERT INTO items_new (
                           id, image_path, notes, openai_result, created_at,
                           title, brand, maker, description, condition, provenance_notes,
                           prc_low, prc_med, prc_hi
                       )
                       SELECT id, image_path, notes, openai_result, created_at,
                              title, brand, maker, description, condition, provenance_notes,
                              prc_low, prc_med, prc_hi
                       FROM items'''
                )
                c.execute('DROP TABLE items')
                c.execute('ALTER TABLE items_new RENAME TO items')

            if has_col('revisions', 'value'):
                c.execute(
                    '''CREATE TABLE IF NOT EXISTS revisions_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        notes TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(item_id) REFERENCES items(id)
                    )'''
                )
                c.execute(
                    '''INSERT INTO revisions_new (id, item_id, notes, timestamp)
                       SELECT id, item_id, notes, timestamp FROM revisions'''
                )
                c.execute('DROP TABLE revisions')
                c.execute('ALTER TABLE revisions_new RENAME TO revisions')

            self.conn.commit()
        except Exception:
            pass
        finally:
            try:
                c.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass

    # --- Change tracking helpers ---
    def record_change(self, item_id, field, old_value, new_value):
        if (old_value or '') == (new_value or ''):
            return
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO item_changes (item_id, field, old_value, new_value, timestamp) VALUES (?, ?, ?, ?, ?)",
            (
                item_id,
                field,
                str(old_value) if old_value is not None else '',
                str(new_value) if new_value is not None else '',
                datetime.datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def record_image_action(self, item_id, image_path, action, meta=""):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO image_history (item_id, image_path, action, meta, timestamp) VALUES (?, ?, ?, ?, ?)",
            (item_id, image_path, action, meta or '', datetime.datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_item_changes(self, item_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT field, old_value, new_value, timestamp FROM item_changes WHERE item_id=? ORDER BY timestamp DESC",
            (item_id,),
        )
        return c.fetchall()

    def get_analytics(self):
        """Legacy method - kept for backwards compatibility."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*), AVG(LENGTH(notes)) FROM items")
        count, avg_notes = c.fetchone()
        c.execute("SELECT AVG(CAST(price AS FLOAT)) FROM prices")
        avg_price = c.fetchone()[0]
        return f"Total items: {count}\nAvg notes length: {avg_notes}\nAvg price: {avg_price}"

    def get_comprehensive_analytics(self):
        """Get comprehensive analytics data for the enhanced analytics page."""
        c = self.conn.cursor()
        analytics = {}
        
        try:
            # Collection Overview
            c.execute("SELECT COUNT(*) FROM items")
            analytics['total_items'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM images")
            analytics['total_images'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prices")
            analytics['total_price_entries'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM revisions")
            analytics['total_revisions'] = c.fetchone()[0]
            
            # Items by Status/Condition
            c.execute("SELECT condition, COUNT(*) FROM items WHERE condition IS NOT NULL AND condition != '' GROUP BY condition ORDER BY COUNT(*) DESC")
            analytics['items_by_condition'] = c.fetchall()
            
            # Items by Brand
            c.execute("SELECT brand, COUNT(*) FROM items WHERE brand IS NOT NULL AND brand != '' GROUP BY brand ORDER BY COUNT(*) DESC LIMIT 10")
            analytics['top_brands'] = c.fetchall()
            
            # Items by Maker
            c.execute("SELECT maker, COUNT(*) FROM items WHERE maker IS NOT NULL AND maker != '' GROUP BY maker ORDER BY COUNT(*) DESC LIMIT 10")
            analytics['top_makers'] = c.fetchall()
            
            # Price Analytics
            try:
                c.execute("SELECT MIN(CAST(price AS FLOAT)), MAX(CAST(price AS FLOAT)), AVG(CAST(price AS FLOAT)) FROM prices WHERE price IS NOT NULL AND price != '' AND price NOT LIKE '%[^0-9.]%'")
                price_stats = c.fetchone()
                analytics['price_min'] = price_stats[0] if price_stats[0] else 0
                analytics['price_max'] = price_stats[1] if price_stats[1] else 0
                analytics['price_avg'] = price_stats[2] if price_stats[2] else 0
            except:
                analytics['price_min'] = 0
                analytics['price_max'] = 0
                analytics['price_avg'] = 0
            
            # Price ranges distribution
            try:
                c.execute("""
                    SELECT 
                        CASE 
                            WHEN CAST(price AS FLOAT) < 50 THEN 'Under $50'
                            WHEN CAST(price AS FLOAT) < 100 THEN '$50-$100'
                            WHEN CAST(price AS FLOAT) < 250 THEN '$100-$250'
                            WHEN CAST(price AS FLOAT) < 500 THEN '$250-$500'
                            WHEN CAST(price AS FLOAT) < 1000 THEN '$500-$1000'
                            ELSE 'Over $1000'
                        END as price_range,
                        COUNT(*) as count
                    FROM prices 
                    WHERE price IS NOT NULL AND price != '' AND price NOT LIKE '%[^0-9.]%'
                    GROUP BY price_range
                    ORDER BY MIN(CAST(price AS FLOAT))
                """)
                analytics['price_distribution'] = c.fetchall()
            except:
                analytics['price_distribution'] = []
            
            # Activity by Month (last 12 months)
            try:
                c.execute("""
                    SELECT 
                        strftime('%Y-%m', created_at) as month,
                        COUNT(*) as items_added
                    FROM items 
                    WHERE created_at IS NOT NULL 
                    AND date(created_at) >= date('now', '-12 months')
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                """)
                analytics['monthly_activity'] = c.fetchall()
            except:
                analytics['monthly_activity'] = []
            
            # Top items by image count
            try:
                c.execute("""
                    SELECT i.title, i.brand, COUNT(img.id) as image_count
                    FROM items i
                    LEFT JOIN images img ON i.id = img.item_id
                    GROUP BY i.id, i.title, i.brand
                    HAVING image_count > 0
                    ORDER BY image_count DESC
                    LIMIT 10
                """)
                analytics['most_documented_items'] = c.fetchall()
            except:
                analytics['most_documented_items'] = []
            
            # Items with most revisions
            try:
                c.execute("""
                    SELECT i.title, i.brand, COUNT(r.id) as revision_count
                    FROM items i
                    LEFT JOIN revisions r ON i.id = r.item_id
                    GROUP BY i.id, i.title, i.brand
                    HAVING revision_count > 0
                    ORDER BY revision_count DESC
                    LIMIT 10
                """)
                analytics['most_revised_items'] = c.fetchall()
            except:
                analytics['most_revised_items'] = []
            
            # Data quality metrics
            c.execute("SELECT COUNT(*) FROM items WHERE title IS NOT NULL AND title != ''")
            analytics['items_with_title'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM items WHERE description IS NOT NULL AND description != ''")
            analytics['items_with_description'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM items WHERE provenance_notes IS NOT NULL AND provenance_notes != ''")
            analytics['items_with_provenance'] = c.fetchone()[0]
            
            # Storage metrics
            c.execute("SELECT AVG(LENGTH(title)), AVG(LENGTH(description)), AVG(LENGTH(notes)) FROM items")
            text_lengths = c.fetchone()
            analytics['avg_title_length'] = text_lengths[0] if text_lengths[0] else 0
            analytics['avg_description_length'] = text_lengths[1] if text_lengths[1] else 0
            analytics['avg_notes_length'] = text_lengths[2] if text_lengths[2] else 0
            
            # Recent activity (last 30 days)
            try:
                c.execute("SELECT COUNT(*) FROM items WHERE date(created_at) >= date('now', '-30 days')")
                analytics['items_added_30_days'] = c.fetchone()[0]
            except:
                analytics['items_added_30_days'] = 0
            
            try:
                c.execute("SELECT COUNT(*) FROM revisions WHERE date(timestamp) >= date('now', '-30 days')")
                analytics['revisions_30_days'] = c.fetchone()[0]
            except:
                analytics['revisions_30_days'] = 0
            
        except Exception as e:
            print(f"[Analytics] Error getting analytics data: {e}")
            # Return default values if there's an error
            return {
                'total_items': 0,
                'total_images': 0,
                'total_price_entries': 0,
                'total_revisions': 0,
                'items_by_condition': [],
                'top_brands': [],
                'top_makers': [],
                'price_min': 0,
                'price_max': 0,
                'price_avg': 0,
                'price_distribution': [],
                'monthly_activity': [],
                'most_documented_items': [],
                'most_revised_items': [],
                'items_with_title': 0,
                'items_with_description': 0,
                'items_with_provenance': 0,
                'avg_title_length': 0,
                'avg_description_length': 0,
                'avg_notes_length': 0,
                'items_added_30_days': 0,
                'revisions_30_days': 0,
            }
        
        return analytics
