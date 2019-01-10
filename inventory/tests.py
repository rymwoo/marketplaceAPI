#inventory/tests.py
import json, unittest
from django.test import TestCase
from graphene.test import Client
from dummyMarketplace.schema import schema

#######################
##  Testing Queries  ##
#######################

class GQLTestProductQuery(TestCase):
  '''
  product(productId: Int): Product
  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    resp = client.execute(query)
    return resp["data"]


  def test_accessingItem(self):
    resp = self.query('''
      query {
        product(productId:3) {
          productName
          productPrice
          productInventory
          productId}}''')
    self.assertEqual(resp["product"],
      {
        'productName': 'Sheet of Paper',
        'productPrice': 0.89,
        'productInventory':100,
        'productId':'3'
      })

  def test_itemIndexOutOfRange(self):
    resp = self.query('''
      query {
        product(productId:-3) {
          productId
          productInventory }}''')
    self.assertEqual(resp,
      {
        "product": None       
      })


class GQTestAllProductsQuery(TestCase):
  '''
  allProducts(
    sortBy: ProductSortingField = PRICE,
    sortOrder: ProductSortingOrder = ASCENDING
    inStockOnly: Boolean = false
    ): [Product!]!
  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    return client.execute(query)["data"]

  def test_allProducts(self):
    resp = self.query('''
      query {
        allProducts {
          productId
          productName
          productInventory
          productPrice
        }}''')
    self.assertEqual(len(resp["allProducts"]), 4)
    self.assertEqual(resp["allProducts"][0]["productPrice"], 0.89)
    self.assertEqual(resp["allProducts"][3]["productName"],"Diary")

  def test_allProductsByName(self):
    resp = self.query('''
      query {
        allProducts(sortBy: PRODUCTNAME) {
          productName
      }}''')
    self.assertEqual(resp["allProducts"][0]["productName"],"Diary")
    self.assertEqual(resp["allProducts"][3]["productName"],"Sheet of Paper")

  def test_allProductsDescendingOrder(self):
    resp = self.query('''
      query {
        allProducts(sortOrder:DESCENDING) {
          productPrice
      }}''')
    self.assertEqual(resp["allProducts"][0]["productPrice"],12.50)
    self.assertEqual(resp["allProducts"][3]["productPrice"],0.89)

  def test_allProductsInStockOnly(self):
    resp = self.query('''
      query {
        allProducts(inStockOnly: true) {
          productName
      }}''')
    self.assertEqual(len(resp["allProducts"]), 3)
    self.assertEqual("Pen" in json.dumps(resp), False)

#########################
##  Testing Mutations  ##
#########################

class GQTestCreateProductMutation(TestCase):
  '''
  createProduct(productName: String!, productPrice: Float!, productInventory: Int!): Product!
  '''
  
  #start with empty DB

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    resp = client.execute(query)
    return resp["data"]

  def test_createNewProductWithInvalidName(self):
    resp = self.query('''
      mutation {
        createProduct(productName: "", productPrice: 2.75, productInventory: 10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["createProduct"]["errors"],
      {
        None
      })

  def test_createNewProductWithInvalidPrice(self):
    resp = self.query('''
      mutation {
        createProduct(productName: "ABC", productPrice: -2.75, productInventory: 10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["createProduct"]["errors"],
      {
        None
      })

  def test_createNewProductWithInvalidproductInventory(self):
    resp = self.query('''
      mutation {
        createProduct(productName: "ABC", productPrice: 2.75, productInventory: -4) {
          errors
        }
      }''')
    self.assertNotEqual(resp["createProduct"]["errors"],
      {
        None
      })

  def test_createNewProduct(self):
    resp = self.query('''
      mutation {
        createProduct(productName: "Comb", productPrice: 2.75, productInventory: 10) {
          productName
          productPrice
          productId
          errors
        }
      }''')
    self.assertEqual(resp["createProduct"],
      {
        'productName':'Comb',
        'productPrice':2.75,
        'productId':1,
        'errors':None
      })

    resp = self.query('''
      query {
        allProducts {
          productName
      }}''')
    self.assertEqual(len(resp["allProducts"]),1);
    #add another item    
    self.query('''
      mutation {
        createProduct(productName: "Comb", productPrice: 2.75, productInventory: 10) {
          productName
          productPrice
          productId
        }
      }''')
    resp = self.query('''
      query {
        allProducts {
          productName
      }}''')
    self.assertEqual(len(resp["allProducts"]),2);

class GQTestUpdateProductMutation(TestCase):
  '''
  updateProduct(productId: Int!, productInventory: Int, productName: String, productPrice: Float): Product!
  '''
  
  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    return client.execute(query)["data"]

  def test_updateProductWithInvalidName(self):
    resp = self.query('''
      mutation {
        updateProduct(productId:1, productName: "", productPrice: 2.75, productInventory: 10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["updateProduct"]["errors"],
      {
        None
      })

  def test_updateProductWithInvalidPrice(self):
    resp = self.query('''
      mutation {
        updateProduct(productId:1, productName: "ABC", productPrice: -2.75, productInventory: 10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["updateProduct"]["errors"],
      {
        None
      })

  def test_updateProductWithInvalidproductInventory(self):
    resp = self.query('''
      mutation {
        updateProduct(productId:1, productName: "ABC", productPrice: 2.75, productInventory: -10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["updateProduct"]["errors"],
      {
        None
      })

  def test_updateProductWithInvalidProductId(self):
    resp = self.query('''
      mutation {
        updateProduct(productId:-5, productName: "ABC", productPrice: 2.75, productInventory: -10) {
          errors
        }
      }''')
    self.assertNotEqual(resp["updateProduct"]["errors"],
      {
        None
      })


  def test_updateProduct(self):
    resp = self.query('''
      mutation {
        updateProduct(productId:1, productName: "Comb", productPrice: 2.75, productInventory: 10) {
          productName
          productPrice
          productId
          productInventory
          errors
        }
      }''')
    self.assertEqual(resp["updateProduct"],
      {
        'productName':'Comb',
        'productPrice':2.75,
        'productId':1,
        'productInventory':10,
        'errors':None
      })

class GQTestDeleteProductMutation(TestCase):
  '''
  deleteProduct(productId: Int!): Product
  '''
  
  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    return client.execute(query)["data"]

  def test_deleteProductWithId(self):
    resp = self.query('''
      mutation {
        deleteProduct(productId:1) {
          productName
          productPrice
          productInventory
          errors
        }
      }''')
    self.assertEqual(resp["deleteProduct"],
      {
        'productName':'Diary',
        'productPrice':12.50,
        'productInventory':8,
        'errors':None
      })

  def test_deleteProductWithInvalidProductId(self):
    resp = self.query('''
      mutation {
        deleteProduct(productId:-5) {
          errors
        }
      }''')
    self.assertNotEqual(resp["deleteProduct"]["errors"],
      {
        None
      })