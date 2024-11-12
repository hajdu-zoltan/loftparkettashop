from django.core.management.base import BaseCommand
from shop.models import Product, Category, Brand

import mysql.connector
from mysql.connector import Error
import re

class Command(BaseCommand):
    help = 'Import products from MySQL to Django database'

    def handle(self, *args, **options):
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='loftpark_designn'
            )

            if connection.is_connected():
                self.stdout.write(self.style.SUCCESS('Sikeresen csatlakoztunk az adatbázishoz'))

                # Kategóriák beolvasása és létrehozása
                query_categories = '''
                SELECT id, name
                FROM product_category
                '''
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query_categories)
                categories = cursor.fetchall()
                category_map = {}
                for cat in categories:
                    category, created = Category.objects.get_or_create(id=cat['id'], defaults={'name': cat['name']})
                    category_map[cat['id']] = category

                # Termékek beolvasása
                query_products = '''
                SELECT id, title, price, short_desc, content, image_id, brand_id, deleted_at
                FROM products
                WHERE deleted_at IS NULL
                '''
                cursor.execute(query_products)
                products = cursor.fetchall()
                self.stdout.write(self.style.SUCCESS(f'Found {len(products)} products.'))

                # Termékek és kategóriák közötti kapcsolatok beolvasása
                query_relations = '''
                SELECT target_id, cat_id
                FROM product_category_relations
                '''
                cursor.execute(query_relations)
                relations = cursor.fetchall()
                product_category_map = {}
                for rel in relations:
                    product_id = rel['target_id']
                    category_id = rel['cat_id']
                    if product_id in product_category_map:
                        product_category_map[product_id].append(category_id)
                    else:
                        product_category_map[product_id] = [category_id]

                image_ids = [product['image_id'] for product in products if product['image_id'] is not None]
                if image_ids:
                    query_media_files = '''
                    SELECT id, file_name, file_path
                    FROM media_files
                    WHERE deleted_at IS NULL AND id IN (%s)
                    ''' % ','.join(map(str, image_ids))

                    cursor.execute(query_media_files)
                    media_files = cursor.fetchall()

                    media_files_map = {file['id']: file for file in media_files}

                    for product in products:
                        image_id = product['image_id']
                        image_path = media_files_map.get(image_id, {}).get('file_path', None) if image_id else None

                        if image_path:
                            image_path = image_path.split('/')[-1]

                        product_id = product['id']
                        category_ids = product_category_map.get(product_id, [])
                        category = None
                        if category_ids:
                            category_id = category_ids[0]  # Assuming single category association for simplicity
                            category = category_map.get(category_id, None)

                        brand_id = product['brand_id']
                        brand = None
                        if brand_id:
                            brand, created = Brand.objects.get_or_create(id=brand_id)

                        # Clean HTML tags from description
                        description = product.get('short_desc', '')
                        sort_description = product.get('content', '')

                        # Remove HTML tags using regex
                        description = re.sub(r'<[^>]+>', '', description) if description else ''
                        sort_description = re.sub(r'<[^>]+>', '', sort_description) if sort_description else ''

                        # Handle null or empty price
                        price = product.get('price')
                        if price is None:
                            price = 0.00  # Set a default price if necessary

                        Product.objects.update_or_create(
                            id=product_id,
                            defaults={
                                'name': product['title'],
                                'price': price,
                                'description': description,
                                'sort_description': sort_description,
                                'category': category,
                                'brand': brand,
                                'image': image_path,
                                'popularity': 0,
                                'rating': 0.00,
                                'is_discounted': False,
                                'discount_rate': 0.00,
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f'Product {product_id} updated/created.'))

                    self.stdout.write(self.style.SUCCESS('Adatok sikeresen feltöltve a Django adatbázisba.'))
                else:
                    self.stdout.write(self.style.WARNING("Nincsenek érvényes image_id-k a lekérdezéshez."))

        except Error as e:
            self.stderr.write(self.style.ERROR(f'Hiba történt: {e}'))

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                self.stdout.write(self.style.SUCCESS('Kapcsolat bezárva'))
