# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a product from the database"""
        # Create a product using the ProductFactory
        product = ProductFactory()
        logging.debug("Product created: %s", product)
        
        # Set the ID to None and create the product in the database
        product.id = None
        product.create()
        
        # Assert that the product ID is not None after creation
        self.assertIsNotNone(product.id)
        
        # Fetch the product back from the database
        found_product = Product.find(product.id)
        
        # Assert that the found product is not None
        self.assertIsNotNone(found_product)
        
        # Assert all properties match
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(Decimal(found_product.price), product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a product"""
        # Create a product using ProductFactory
        product = ProductFactory()
        logging.debug("Created product: %s", product)

        # Set ID to None and create product in database
        product.id = None
        product.create()
        logging.debug("Created product in database: %s", product)

        # Save the current id for later comparison
        original_id = product.id

        # Update product description
        new_description = "Updated description for testing"
        product.description = new_description
        product.update()

        # Assert id didn't change but description did
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, new_description)

        # Fetch all products and verify only one exists
        products = Product.all()
        self.assertEqual(len(products), 1)

        # Verify the fetched product has original id but updated description
        updated_product = products[0]
        self.assertEqual(updated_product.id, original_id)
        self.assertEqual(updated_product.description, new_description)

    def test_delete_a_product(self):
        """It should Delete a product from the database"""
        # Create a product using ProductFactory
        product = ProductFactory()
        product.id = None
        product.create()
        
        # Assert that there is one product in the database
        products = Product.all()
        self.assertEqual(len(products), 1)
        
        # Delete the product from the database
        product.delete()
        
        # Assert that the product was deleted
        products = Product.all()
        self.assertEqual(len(products), 0)
        
        # Verify that attempting to find the product returns None
        deleted_product = Product.find(product.id)
        self.assertIsNone(deleted_product)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        # Start with an empty database
        products = Product.all()
        self.assertEqual(len(products), 0)
        
        # Create five products
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        
        # Fetch all products and verify count
        products = Product.all()
        self.assertEqual(len(products), 5)
        
        # Verify each product is valid
        for product in products:
            self.assertIsNotNone(product.id)
            self.assertIsNotNone(product.name)
            self.assertIsNotNone(product.description)
            self.assertIsNotNone(product.price)
            self.assertIsNotNone(product.available)
            self.assertIsNotNone(product.category)

    def test_find_by_name(self):
        """It should Find Products by Name"""
        # Create a batch of 5 products
        products = []
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
            products.append(product)
        
        # Get the name of the first product
        name = products[0].name
        
        # Count how many products have this name
        name_count = sum(1 for product in products if product.name == name)
        
        # Find products with the same name
        found_products = Product.find_by_name(name)
        
        # Assert the count matches
        self.assertEqual(len(found_products), name_count)
        
        # Assert each returned product has the requested name
        for product in found_products:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        # Create a batch of 10 products
        products = []
        for _ in range(10):
            product = ProductFactory()
            product.id = None
            product.create()
            products.append(product)
        
        # Get the availability of the first product
        availability = products[0].available
        
        # Count how many products have this availability
        available_count = sum(1 for product in products if product.available == availability)
        
        # Find products with the same availability
        found_products = Product.find_by_availability(availability)
        
        # Assert the count matches
        self.assertEqual(len(found_products), available_count)
        
        # Assert each returned product has the requested availability
        for product in found_products:
            self.assertEqual(product.available, availability)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        # Create a batch of 10 products
        products = []
        for _ in range(10):
            product = ProductFactory()
            product.id = None
            product.create()
            products.append(product)
        
        # Get the category of the first product
        category = products[0].category
        
        # Count how many products have this category
        category_count = sum(1 for product in products if product.category == category)
        
        # Find products with the same category
        found_products = Product.find_by_category(category)
        
        # Assert the count matches
        self.assertEqual(len(found_products), category_count)
        
        # Assert each returned product has the requested category
        for product in found_products:
            self.assertEqual(product.category, category)
