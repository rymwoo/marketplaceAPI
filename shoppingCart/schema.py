#shoppingCart/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from shoppingCart.models import ShoppingCart, OrderListing
from inventory.models import Product
from django.core.exceptions import ObjectDoesNotExist

class OrderListingType(DjangoObjectType):
  class Meta:
    model = OrderListing

class ShoppingCartType(DjangoObjectType):
  shoppingCartValue = graphene.Float()
  class Meta:
    model = ShoppingCart


#############################
##         Queries         ##
#############################

class Query(graphene.ObjectType):

  shopping_cart = graphene.Field(ShoppingCartType)

  def resolve_shopping_cart(self, info, **kwargs):
    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key
    #get Cart associated with current shoppingCartKey
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      #make new cart
      cart = ShoppingCart(shoppingCartKey = key)
      cart.save()
    return cart

  shopping_cart_is_empty = graphene.Boolean()

  def resolve_shopping_cart_is_empty(self, info, **kwargs):
    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      return True
    cart.shoppingCartItems.all().filter(productCount=0).delete()
    if len(cart.shoppingCartItems.all())>0:
      return False
    else:
      return True

#############################
##        Mutations        ##
#############################

class AddProductToCart(graphene.Mutation):
  shoppingCart   = graphene.Field(ShoppingCartType)
  orderListing   = graphene.Field(OrderListingType)
  errors         = graphene.String()

  class Arguments:
    productId = graphene.Int()
    productCount = graphene.Int()

  def mutate(self, info, productId, productCount = 1):
    errorMsg = []

    cartExists = True
    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key
    #get Cart associated with current shoppingCartKey
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      #make new cart
      cartExists = False
      cart = ShoppingCart(shoppingCartKey = key)
      cart.save()

    if productCount<=0:
      errorMsg.append("Cannot add 0 or less items from cart")
      return AddProductToCart(
        shoppingCart = cart,
        errors = errorMsg
      )

    try:
      prod = Product.objects.all().get(productId=productId)
    except ObjectDoesNotExist:
      errorMsg.append("Could not add non-existent product")
      return AddProductToCart(
        shoppingCart = cart,
        errors = errorMsg
      )

    if cartExists: #try to find existing order listing to add to
      for item in cart.shoppingCartItems.all():
        if item.product.productId == productId:
          item.productCount+= productCount
          item.save()
          return AddProductToCart(
            shoppingCart   = cart,
            orderListing   = item,
            errors         = None
            )

    #make a new order listing
    orderListing = OrderListing(product=prod, productCount=productCount, shoppingCart=cart)
    orderListing.save()

    if len(errorMsg)==0:
      errorMsg = None
    return AddProductToCart(
      shoppingCart   = cart,
      orderListing   = orderListing,
      errors         = errorMsg
      )

class RemoveProductFromCart(graphene.Mutation):
  shoppingCart = graphene.Field(ShoppingCartType)
  errors       = graphene.String()

  class Arguments:
    productId = graphene.Int()
    productCount = graphene.Int()

  def mutate(self, info, productId, productCount = 1):
    errorMsg = []

    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key
    cartExists = True
    #get Cart associated with current shoppingCartKey
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      #make new cart
      cartExists = False
      cart = ShoppingCart(shoppingCartKey = key)
      cart.save()

    if productCount<=0:
      errorMsg.append("Cannot remove 0 or less items from cart")
      return AddProductToCart(
        shoppingCart = cart,
        errors = errorMsg
      )

    if not cartExists:
      #cart is empty = newly generated
      errorMsg.append("Object does not exist in cart")
      return AddProductToCart(
        shoppingCart = cart,
        errors = errorMsg
      )

    try:
      prod = Product.objects.all().get(productId=productId)
    except ObjectDoesNotExist:
      errorMsg.append("Could not remove non-existent product")
      return AddProductToCart(
        shoppingCart = cart,
        errors = errorMsg
      )

    #cart exists AND product exists => try to find order listing in cart
    for item in cart.shoppingCartItems.all():
      if item.product == prod:
        if item.productCount > productCount:
          item.productCount-= productCount
          item.save()
        else:
          if item.productCount < productCount: #trying to remove more than exists
            errorMsg.append("Tried to remove more items than exist in cart")
          item.delete()
        if len(errorMsg) == 0:
          errorMsg = None
        return RemoveProductFromCart(
          shoppingCart   = cart,
          errors         = errorMsg
          )

    #cart Exists, but could not find product anywhere in cart
    errorMsg.append("Object does not exist in cart")
    return AddProductToCart(
      shoppingCart = cart,
      errors = errorMsg
    )

class ClearShoppingCart(graphene.Mutation):
  shoppingCart = graphene.Field(ShoppingCartType)

  class Arguments:
    pass

  def mutate(self, info):
    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key

    #get Cart associated with current shoppingCartKey
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      #make new cart and return it
      cart = ShoppingCart(shoppingCartKey = key)
      cart.save()
      return ClearShoppingCart(shoppingCart=cart)
    else: #cart exists
      cart.shoppingCartItems.all().delete()
      cart.save()    
      return ClearShoppingCart(shoppingCart=cart)

class CheckoutShoppingCart(graphene.Mutation):
  totalSpend = graphene.Float()
  shoppingCart = graphene.Field(ShoppingCartType)

  class Arguments:
    pass

  def mutate(self, info):
    if not info.context.session.session_key:
      info.context.session.save()
    key = info.context.session.session_key
    try:
      cart = ShoppingCart.objects.all().get(shoppingCartKey=key)
    except ObjectDoesNotExist:
      cart = ShoppingCart(shoppingCartKey = key)
      cart.save()
      return CheckoutShoppingCart(totalSpend = 0, shoppingCart=cart)

    totalSpend = 0
    for order in cart.shoppingCartItems.all():
      amtToPurchase = order.productCount
      if order.productCount > order.product.productInventory:
        amtToPurchase = order.product.productInventory
      totalSpend+= amtToPurchase*order.product.productPrice
      order.product.productInventory -= amtToPurchase
      order.product.save()
      order.productCount -= amtToPurchase
      order.save()

    cart.shoppingCartItems.all().filter(productCount=0).delete()

    return CheckoutShoppingCart(totalSpend=totalSpend,shoppingCart=cart)



class Mutation(graphene.ObjectType):
  add_product_to_cart = AddProductToCart.Field()
  remove_product_from_cart = RemoveProductFromCart.Field()
  clear_shopping_cart = ClearShoppingCart.Field()
  checkout_shopping_cart = CheckoutShoppingCart.Field()