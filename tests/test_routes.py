######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_read_a_product(self):
        """It should Read a single Product"""
        # Create a test product
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the response data
        data = response.get_json()
        self.assertEqual(data["id"], test_product.id)
        self.assertEqual(data["name"], test_product.name)
        self.assertEqual(data["description"], test_product.description)
        self.assertEqual(Decimal(data["price"]), test_product.price)
        self.assertEqual(data["available"], test_product.available)
        self.assertEqual(data["category"], test_product.category.name)

    def test_read_a_product_not_found(self):
        """It should not Read a Product that is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found", data["message"])

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        """It should Update an existing Product"""
        # create a product to update
        test_product = self._create_products(1)[0]
        
        # Change it and send it back
        test_product.description = "Updated Description"
        response = self.client.put(
            f"{BASE_URL}/{test_product.id}",
            json=test_product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the update was successful
        updated_product = response.get_json()
        self.assertEqual(updated_product["description"], "Updated Description")

    def test_update_product_not_found(self):
        """It should not Update a Product that's not found"""
        # Create a product and prepare it for update
        test_product = ProductFactory()
        
        # Send the update to a non-existent product
        response = self.client.put(
            f"{BASE_URL}/0",
            json=test_product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_bad_content_type(self):
        """It should not Update a Product with wrong content type"""
        # Create a product to update
        test_product = self._create_products(1)[0]
        
        # Send wrong media type
        response = self.client.put(
            f"{BASE_URL}/{test_product.id}",
            data="wrong media type",
            content_type="plain/text"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a Product"""
        # Create a product to delete
        test_product = self._create_products(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check if it was really deleted
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should return 204 even if Product not found"""
        # Delete a product that doesn't exist
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------
    def test_list_all_products(self):
        """It should List all Products"""
        # Create 5 test products
        products = self._create_products(5)
        
        # Test listing all products
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the response data
        data = response.get_json()
        self.assertEqual(len(data), len(products))

    def test_query_by_name(self):
        """It should Query Products by Name"""
        products = self._create_products(5)
        test_name = products[0].name
        name_count = len([product for product in products if product.name == test_name])
        
        # Test query for products by name
        response = self.client.get(
            BASE_URL,
            query_string=f"name={test_name}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the data matches
        data = response.get_json()
        self.assertEqual(len(data), name_count)
        for product in data:
            self.assertEqual(product["name"], test_name)

    def test_list_by_name(self):
        """It should List Products by Name"""
        # Create two products with the same name
        products = []
        for _ in range(2):
            product = ProductFactory()
            product.name = "same-name"
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            products.append(response.get_json())

        # Create a product with a different name
        different_product = ProductFactory()
        different_product.name = "different-name"
        response = self.client.post(BASE_URL, json=different_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # List products by the same name
        response = self.client.get(
            BASE_URL,
            query_string="name=same-name"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for product in data:
            self.assertEqual(product["name"], "same-name")

    def test_query_by_category(self):
        """It should Query Products by Category"""
        products = self._create_products(5)
        test_category = products[0].category
        category_count = len([product for product in products if product.category == test_category])
        
        # Test query for products by category
        response = self.client.get(
            BASE_URL,
            query_string=f"category={test_category.name}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the data matches
        data = response.get_json()
        self.assertEqual(len(data), category_count)
        for product in data:
            self.assertEqual(product["category"], test_category.name)

    def test_list_by_category(self):
        """It should List Products by Category"""
        # Create two products with TOOLS category
        products = []
        for _ in range(2):
            product = ProductFactory()
            product.category = Category.TOOLS
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            products.append(response.get_json())

        # Create a product with FOOD category
        different_product = ProductFactory()
        different_product.category = Category.FOOD
        response = self.client.post(BASE_URL, json=different_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # List products by TOOLS category
        response = self.client.get(
            BASE_URL,
            query_string="category=TOOLS"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for product in data:
            self.assertEqual(product["category"], "TOOLS")

    def test_query_by_availability(self):
        """It should Query Products by Availability"""
        products = self._create_products(10)
        test_available = products[0].available
        available_count = len([product for product in products if product.available == test_available])
        
        # Test query for products by availability
        response = self.client.get(
            BASE_URL,
            query_string=f"available={test_available}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the data matches
        data = response.get_json()
        self.assertEqual(len(data), available_count)
        for product in data:
            self.assertEqual(product["available"], test_available)

    def test_list_by_availability(self):
        """It should List Products by Availability"""
        # Create two available products
        available_products = []
        for _ in range(2):
            product = ProductFactory()
            product.available = True
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            available_products.append(response.get_json())

        # Create one unavailable product
        unavailable_product = ProductFactory()
        unavailable_product.available = False
        response = self.client.post(BASE_URL, json=unavailable_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # List available products
        response = self.client.get(
            BASE_URL,
            query_string="available=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for product in data:
            self.assertEqual(product["available"], True)

        # List unavailable products
        response = self.client.get(
            BASE_URL,
            query_string="available=false"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data
        data = response.get_json()
        self.assertEqual(len(data), 1)
        for product in data:
            self.assertEqual(product["available"], False)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
