#shoppingCart/tests.py

import json, unittest
from django.test import TestCase, RequestFactory
from graphene.test import Client
from dummyMarketplace.schema import schema
from django.contrib.sessions.middleware import SessionMiddleware

#######################
##  Testing Queries  ##
#######################

class GQLTestShoppingCartIsEmptyQuery(TestCase):
  '''
  shoppingCartIsEmpty(): Boolean!
  '''
  fixtures = ['dummyDB.json']
  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def test_shoppingCartIsEmpty(self):
    resp = self.query('''
      query {
        shoppingCartIsEmpty
      }''')
    self.assertEqual(resp["shoppingCartIsEmpty"],True)
  
  def test_shoppingCartIsEmptyToBeFalse(self):
    resp = self.query('''
      mutation{
        addProductToCart(productId:1) {
          errors
      }}''')
    resp = self.query('''
      query {
        shoppingCartIsEmpty
      }''')
    self.assertEqual(resp["shoppingCartIsEmpty"],False)


class GQLTestShoppingCartQuery(TestCase):
  '''
  shoppingCart(): ShoppingCart

  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def test_newShoppingCartQuery(self):
    resp = self.query('''
      query {
        shoppingCart {
          shoppingCartId,
          shoppingCartKey,
          shoppingCartItems {
            product {productName},
            productCount
          }
          shoppingCartValue
          }}''')
    self.assertEqual(resp["shoppingCart"]["shoppingCartValue"], 0)
    self.assertEqual(resp["shoppingCart"]["shoppingCartId"], '1')
    self.assertEqual(resp["shoppingCart"]["shoppingCartItems"], [])

  def test_existingShoppingCartQuery(self):
    #add 3 pens at $1.25 each
    resp = self.query('''
    mutation {
      addProductToCart(productId:2, productCount:3) {
        shoppingCart { shoppingCartId},
        orderListing {productCount},
        errors
        }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["shoppingCart"]["shoppingCartId"]), 1)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 3)

    #add 2 sheets of paper at $0.89 each
    resp = self.query('''
    mutation {
      addProductToCart(productId:3, productCount:2) {
        shoppingCart {shoppingCartId},
        orderListing {
          productCount},
        errors
        }}''')

    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["shoppingCart"]["shoppingCartId"]), 1)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 2)

    #check shopping cart
    resp = self.query('''
      query {
        shoppingCart {
          shoppingCartId,
          shoppingCartKey,
          shoppingCartItems {
            product {productName},
            productCount
          }
          shoppingCartValue
          }}''')
    self.assertEqual(resp["shoppingCart"]["shoppingCartValue"], 3*1.25+2*0.89)
    self.assertEqual(resp["shoppingCart"]["shoppingCartId"], '1')
    self.assertEqual(resp["shoppingCart"]["shoppingCartItems"][0]["productCount"], 3)
    self.assertEqual(resp["shoppingCart"]["shoppingCartItems"][1]["productCount"], 2)

#########################
##  Testing Mutations  ##
#########################

class GQLCheckoutShoppingCart(TestCase):
  '''
  checkOutShoppingCart(): totalSpend!, shoppingCart!

  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def test_checkoutShoppingCartNormal(self):
    #add 7 sheets of paper (100 in cart)
    resp = self.query('''
      mutation {
        addProductToCart(productId:3, productCount:7) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},  
          errors
        }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartValue"], 0.89*7)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartItems"][0]["productCount"], 7)
  
    resp = self.query('''   
      mutation {
        checkoutShoppingCart {
          totalSpend,
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},  
        }}''')
    self.assertEqual(resp["checkoutShoppingCart"]["totalSpend"], 0.89*7)
    self.assertEqual(len(resp["checkoutShoppingCart"]["shoppingCart"]["shoppingCartItems"]), 0)  
    self.assertEqual(resp["checkoutShoppingCart"]["shoppingCart"]["shoppingCartValue"], 0)  


  def test_checkoutShoppingCartOutOfStock(self):
    #add 5 pens to cart (0 in cart)
    resp = self.query('''
      mutation {
        addProductToCart(productId:2, productCount:5) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},
          errors
        }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartValue"], 1.25*5)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartItems"][0]["productCount"], 5)

  def test_checkoutShoppingCartSomeItemsInStock(self):
    #add 3 pens AND 5 sheets paper
    self.query('''
      mutation {
        addProductToCart(productId:2, productCount:3) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},
          errors
        }}''')
    self.query('''
      mutation {
        addProductToCart(productId:3, productCount:5) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},  
          errors
        }}''')
    resp = self.query('''   
      mutation {
        checkoutShoppingCart {
          totalSpend,
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},  
        }}''')

    self.assertEqual(resp["checkoutShoppingCart"]["totalSpend"], 0.89*5)
    self.assertEqual(len(resp["checkoutShoppingCart"]["shoppingCart"]["shoppingCartItems"]), 1)  
    self.assertEqual(resp["checkoutShoppingCart"]["shoppingCart"]["shoppingCartValue"], 3*1.25)  

class GQLClearShoppingCart(TestCase):
  '''
  clearShoppingCart(): shoppingCart!

  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def setUp(self):
    #add 5 pens to cart
    resp = self.query('''
      mutation {
        addProductToCart(productId:2, productCount:5) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},
          errors
        }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartValue"], 1.25*5)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartItems"][0]["productCount"], 5)

  def test_clearShoppingCart(self):
    resp = self.query('''
      mutation {
        clearShoppingCart{
          shoppingCart {shoppingCartValue,shoppingCartItems{productCount}}
      }}''')
    self.assertEqual(resp["clearShoppingCart"]["shoppingCart"]["shoppingCartValue"],0)
    self.assertEqual(len(resp["clearShoppingCart"]["shoppingCart"]["shoppingCartItems"]),0)

class GQLTestRemoveProductFromCart(TestCase):
  '''
  removeProductFromCart(productId: Int!, productCount: Int = 1): shoppingCart!, errors

  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def setUp(self):
    #add 5 pens to cart
    resp = self.query('''
      mutation {
        addProductToCart(productId:2, productCount:5) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},
          errors
        }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartValue"], 1.25*5)
    self.assertEqual(resp["addProductToCart"]["shoppingCart"]["shoppingCartItems"][0]["productCount"], 5)

  def test_removeNonExistentProduct(self):
    resp = self.query('''
      mutation {
        removeProductFromCart(productId:99) {
          errors
        }
      }''')
    self.assertEqual(resp["removeProductFromCart"]["errors"],"['Could not remove non-existent product']")

  def test_removeNotInCartProduct(self):
    resp = self.query('''
      mutation {
        removeProductFromCart(productId:3) {
          shoppingCart { shoppingCartValue
          },
          errors
        }
      }''')
    self.assertEqual(resp["removeProductFromCart"]["errors"],"['Object does not exist in cart']")
    self.assertEqual(resp["removeProductFromCart"]["shoppingCart"]["shoppingCartValue"], 1.25*5)

  def test_removeProductNormally(self):
    resp = self.query('''
      mutation {
        removeProductFromCart(productId:2) {
          shoppingCart { shoppingCartValue, shoppingCartItems{productCount}},
          errors
        }
      }''')
    self.assertEqual(resp["removeProductFromCart"]["shoppingCart"]["shoppingCartValue"], 1.25*4)
    self.assertEqual(len(resp["removeProductFromCart"]["shoppingCart"]["shoppingCartItems"]), 1)

  def test_removeMoreProductsThanExist(self):
    resp = self.query('''
      mutation {
        removeProductFromCart(productId:2,productCount:9) {
          shoppingCart { shoppingCartValue,shoppingCartItems{orderListingId}},
          errors
        }
      }''')
    self.assertEqual(resp["removeProductFromCart"]["shoppingCart"]["shoppingCartValue"], 0)
    self.assertEqual(len(resp["removeProductFromCart"]["shoppingCart"]["shoppingCartItems"]), 0)
  
class GQLTestAddProductToCart(TestCase):
  '''
  addProductToCart(productId: Int!, itemCount: Int = 1): ShoppingCart

  '''

  fixtures = ['dummyDB.json']

  def query(self, query):
    '''returns ordered dictionary, without data wrapper'''
    client = Client(schema)
    request = RequestFactory().get('/')
    middleware = SessionMiddleware().process_request(request)
    request.session.save()
    resp = client.execute(query,context_value=request)
    return resp["data"]

  def test_increaseAmountInCart(self):
    resp = self.query('''
      mutation {
        addProductToCart(productId:2) {
          shoppingCart {shoppingCartId},
          orderListing {
            orderListingId
            productCount
            product {
              productId,
              productName,
            }
          },
          errors
          }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["shoppingCart"]["shoppingCartId"]), 1)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["orderListingId"]), 1)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["product"]["productId"]), 2)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["product"]["productName"], "Pen")
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 1)
    resp = self.query('''
      mutation {
        addProductToCart(productId:2, productCount:6) {
          shoppingCart {shoppingCartId},
          orderListing {
            orderListingId
            productCount
            product {
              productId,
              productName,
            }
          },
          errors
          }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["shoppingCart"]["shoppingCartId"]), 1)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["orderListingId"]), 1)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["product"]["productId"]), 2)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["product"]["productName"], "Pen")
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 7)

  def test_addProductToCart(self):
    resp = self.query('''
      mutation {
        addProductToCart(productId:2) {
          shoppingCart {shoppingCartId},
          orderListing {
            orderListingId
            product {productName}
            productCount
            },
          errors
          }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["shoppingCart"]["shoppingCartId"]), 1)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["orderListingId"]), 1)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["product"]["productName"], "Pen")
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 1)

  def test_addSeveralProductsToCart(self):
    #add 10 diaries
    resp = self.query('''
      mutation {
        addProductToCart(productId:1,productCount:10) {
          shoppingCart {shoppingCartId},
          orderListing {orderListingId},
          errors
          }}''')
    cart = resp["addProductToCart"]["shoppingCart"] 
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["orderListingId"]), 1)
    #add 5 rulers  
    resp = self.query('''
      mutation {
        addProductToCart(productId:4,productCount:5) {
          shoppingCart {shoppingCartId},
          orderListing {
            orderListingId,
            productCount,
            product {productId, productName}
            },
          errors
          }}''')
    self.assertEqual(resp["addProductToCart"]["errors"], None)
    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["orderListingId"]), 2)

    #same ShoppingCart as before
    self.assertEqual(resp["addProductToCart"]["shoppingCart"], cart)

    self.assertEqual(int(resp["addProductToCart"]["orderListing"]["product"]["productId"]), 4)
    self.assertEqual(resp["addProductToCart"]["orderListing"]["product"]["productName"], "Ruler")
    self.assertEqual(resp["addProductToCart"]["orderListing"]["productCount"], 5)

  def test_addNonExistentProductToCart(self):
    resp = self.query('''
      mutation {
        addProductToCart(productId:99) {
          errors
          }}''')
    self.assertNotEqual(resp["addProductToCart"]["errors"],
      {
        None
      })