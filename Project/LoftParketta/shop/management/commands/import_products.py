from django.core.management.base import BaseCommand
from shop.models import Product, Category, Brand

import pymysql
import re

class Command(BaseCommand):
    help = 'Import products from MySQL to Django database'

    def handle(self, *args, **options):
        try:
            # Kapcsolódás a MySQL adatbázishoz
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='',
                database='loftpark_designn',
                port=3306,
                cursorclass=pymysql.cursors.DictCursor
            )

            self.stdout.write(self.style.SUCCESS('Sikeresen csatlakoztunk az adatbázishoz'))

            # Kategóriák beolvasása és létrehozása
            self.import_categories(connection)

            # Termékek beolvasása
            self.import_products(connection)

        except pymysql.MySQLError as e:
            self.stderr.write(self.style.ERROR(f'Hiba történt a MySQL kapcsolódás során: {e}'))

        finally:
            if connection:
                connection.close()
                self.stdout.write(self.style.SUCCESS('Kapcsolat bezárva'))

    def import_categories(self, connection):
        """Kategóriák beolvasása és létrehozása."""
        query = '''
        SELECT id, name
        FROM product_category
        '''

        with connection.cursor() as cursor:
            cursor.execute(query)
            categories = cursor.fetchall()

        category_map = {}
        for cat in categories:
            category, created = Category.objects.get_or_create(
                id=cat['id'], defaults={'name': cat['name']}
            )
            category_map[cat['id']] = category

        self.stdout.write(self.style.SUCCESS(f'{len(categories)} kategória feldolgozva.'))
        return category_map

    def import_products(self, connection):
        """Termékek beolvasása és létrehozása."""
        query_products = '''
        SELECT id, title, price, short_desc, content, image_id, brand_id, deleted_at
        FROM products
        WHERE deleted_at IS NULL
        '''

        with connection.cursor() as cursor:
            cursor.execute(query_products)
            products = cursor.fetchall()

        self.stdout.write(self.style.SUCCESS(f'{len(products)} termék található.'))

        # Kategória és termék kapcsolat beolvasása
        product_category_map = self.get_product_category_relations(connection)

        # Kép adatok beolvasása
        media_files_map = self.get_media_files(connection, products)

        # Termékek feldolgozása
        for product in products:
            self.process_product(product, product_category_map, media_files_map)

        self.stdout.write(self.style.SUCCESS('Termékek sikeresen feldolgozva.'))

    def get_product_category_relations(self, connection):
        """Termékek és kategóriák közötti kapcsolatok beolvasása."""
        query_relations = '''
        SELECT target_id, cat_id
        FROM product_category_relations
        '''

        with connection.cursor() as cursor:
            cursor.execute(query_relations)
            relations = cursor.fetchall()

        product_category_map = {}
        for rel in relations:
            product_id = rel['target_id']
            category_id = rel['cat_id']
            product_category_map.setdefault(product_id, []).append(category_id)

        return product_category_map

    def get_media_files(self, connection, products):
        """Kép adatok beolvasása a termékekhez."""
        image_ids = [product['image_id'] for product in products if product['image_id'] is not None]

        if not image_ids:
            self.stdout.write(self.style.WARNING('Nincsenek kép azonosítók a lekérdezéshez.'))
            return {}

        query_media_files = '''
        SELECT id, file_name, file_path
        FROM media_files
        WHERE deleted_at IS NULL AND id IN (%s)
        ''' % ','.join(map(str, image_ids))

        with connection.cursor() as cursor:
            cursor.execute(query_media_files)
            media_files = cursor.fetchall()

        return {file['id']: file for file in media_files}

    def process_product(self, product, product_category_map, media_files_map):
        """Egy termék feldolgozása és mentése a Django adatbázisba."""
        # Kép elérési út feldolgozása
        image_id = product['image_id']
        image_path = media_files_map.get(image_id, {}).get('file_path', None) if image_id else None

        if image_path:
            image_path = image_path.split('/')[-1]

        # Kategória hozzárendelése
        product_id = product['id']
        category_ids = product_category_map.get(product_id, [])
        category = None
        if category_ids:
            category = Category.objects.filter(id=category_ids[0]).first()

        # Márka hozzárendelése
        brand = None
        if product['brand_id']:
            brand, _ = Brand.objects.get_or_create(id=product['brand_id'])

        # HTML tag-ek eltávolítása a leírásból
        description = product.get('short_desc', '')
        short_description = product.get('content', '')

        # description = re.sub(r'<[^>]+>', '', description) if description else ''
        # short_description = re.sub(r'<[^>]+>', '', short_description) if short_description else ''

        # Ár kezelése
        price = product.get('price', 0.00)
        if price is None:
            price = 0.00  # Alapértelmezett érték, ha a price hiányzik vagy null

        if description is None:
            description = ""

        if short_description is None:
            short_description = ""
        # Termék mentése
        Product.objects.update_or_create(
            id=product_id,
            defaults={
                'name': product['title'],
                'price': price,
                'description': description,
                'sort_description': short_description,
                'category': category,
                'brand': brand,
                'image': image_path,
                'popularity': 0,
                'rating': 0.00,
                'is_discounted': False,
                'discount_rate': 0.00,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Termék {product_id} feldolgozva.'))
