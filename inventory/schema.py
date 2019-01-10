#inventory/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from inventory.models import Product
from django.core.exceptions import ObjectDoesNotExist

class ProductSortingField(graphene.Enum):
  PRODUCTPRICE = 0
  PRODUCTNAME = 1
  PRODUCTID = 2
  PRODUCTINVENTORY = 3

class ProductSortingOrder(graphene.Enum):
  ASCENDING = 0
  DESCENDING = 1

class ProductType(DjangoObjectType):
  class Meta:
    model = Product

#############################
##         Queries         ##
#############################

class Query(graphene.ObjectType):
  product = graphene.Field(ProductType,productId=graphene.Int())

  all_products = graphene.List(ProductType,
    in_stock_only=graphene.Boolean(),
    sort_order=ProductSortingOrder(),
    sort_by=ProductSortingField())

  def resolve_product(self, info, **kwargs):
    id = kwargs.get("productId")
    if id:
      try:
        prod = Product.objects.get(pk=id)
      except ObjectDoesNotExist:
        return None
      return prod

  def resolve_all_products(self, info,
    sort_by=ProductSortingField.PRODUCTPRICE,
    sort_order=ProductSortingOrder.ASCENDING,
    in_stock_only = False, **kwargs):
    
    if in_stock_only:
      productList = Product.objects.all().exclude(productInventory=0)
    else:
      productList = Product.objects.all()

    if sort_by == ProductSortingField.PRODUCTPRICE:
      if sort_order == ProductSortingOrder.ASCENDING:
        productList = productList.order_by("productPrice")
      else:
        productList = productList.order_by("-productPrice")
    if sort_by == ProductSortingField.PRODUCTNAME:
      if sort_order == ProductSortingOrder.ASCENDING:
        productList = productList.order_by("productName")
      else:
        productList = productList.order_by("-productName")
    if sort_by == ProductSortingField.PRODUCTID:
      if sort_order == ProductSortingOrder.ASCENDING:
        productList = productList.order_by("productId")
      else:
        productList = productList.order_by("-productId")
    if sort_by == ProductSortingField.PRODUCTINVENTORY:
      if sort_order == ProductSortingOrder.ASCENDING:
        productList = productList.order_by("produceInventory")
      else:
        productList = productList.order_by("-produceInventory")

    return productList

#############################
##        Mutations        ##
#############################

class CreateProduct(graphene.Mutation):
  productId = graphene.Int()
  productName = graphene.String()
  productPrice = graphene.Float()
  productInventory = graphene.Int()
  errors = graphene.String()

  class Arguments:
    productName = graphene.String()
    productPrice = graphene.Float()
    productInventory = graphene.Int()

  def mutate(self, info, productName, productPrice, productInventory):
    errorMsg = []
    #fail if any field is invalid
    if productInventory<0:
      errorMsg.append("Unable to set productInventory to value less than zero")
    if len(productName)==0:
      errorMsg.append("Unable to set name to empty-string")
    if productPrice<0:
      errorMsg.append("Unable to change price to negative value")
    if (abs(productPrice)*100)-int(abs(productPrice)*100)>0:
      errorMsg.append("Price cannot have more than two decimal places")

    if len(errorMsg)==0:
      errorMsg = None
      product = Product(productName=productName, productPrice=productPrice, productInventory=productInventory)
      product.save()
      return CreateProduct(
        productId = product.productId,
        productName = product.productName,
        productPrice = product.productPrice,
        productInventory = product.productInventory,
        errors = errorMsg
        )
    else: #product creation fails
      return CreateProduct(
        productId = None,
        productName = None,
        productPrice = None,
        productInventory = None,
        errors = errorMsg
        )

class DeleteProduct(graphene.Mutation):
  productId = graphene.Int()
  productName = graphene.String()
  productPrice = graphene.Float()
  productInventory = graphene.Int()
  errors = graphene.String()

  class Arguments:
    productId = graphene.Int()

  def mutate(self, info, productId):
    errorMsg = []
    try:
      product = Product.objects.get(pk=productId)
    except ObjectDoesNotExist:
      errorMsg.append("Cannot delete object that does not exist")
      return DeleteProduct(
        productId = None,
        productName = None,
        productPrice = None,
        productInventory = None,
        errors = errorMsg
        )

    product.delete()

    if len(errorMsg) == 0:
      errorMsg = None

    return DeleteProduct(
      productId = product.productId,
      productName = product.productName,
      productPrice = product.productPrice,
      productInventory = product.productInventory,
      errors = errorMsg
      )

class UpdateProduct(graphene.Mutation):
  productId = graphene.Int()
  productName = graphene.String()
  productPrice = graphene.Float()
  productInventory = graphene.Int()
  errors = graphene.String()

  class Arguments:
    productId = graphene.Int()
    productInventory = graphene.Int()
    productName = graphene.String()
    productPrice = graphene.Float()


  def mutate(self, info, productId, productInventory = None, productName = None, productPrice = None):
    errorMsg = []
    try:
      item = Product.objects.all().get(pk=productId)
    except ObjectDoesNotExist:
      errorMsg.append("Cannot mutate object that does not exist")
      return UpdateProduct(
        productId = None,
        productName = None,
        productPrice = None,
        productInventory = None,
        errors = errorMsg
        )


    if productInventory:
      if productInventory<0:
        errorMsg.append("Unable to change productInventory to value less than zero")
      else:
        item.productInventory = productInventory
    if productName is not None:
      if len(productName)==0:
        errorMsg.append("Unable to change name to empty-string")
      else:
        item.productName = productName
    if productPrice:
      validPrice=True
      if productPrice<0:
        validPrice=False
        errorMsg.append("Unable to change price to negative value")
      if (abs(productPrice)*100)-int(abs(productPrice)*100)>0:
        validPrice=False
        errorMsg.append("Price cannot have more than two decimal places")
      if validPrice:
        item.productPrice = productPrice
    item.save()
    
    if len(errorMsg)==0:
      errorMsg = None

    return UpdateProduct(
      productId = item.productId,
      productName = item.productName,
      productPrice = item.productPrice,
      productInventory = item.productInventory,
      errors = errorMsg
      )
      

class Mutation(graphene.ObjectType):
  create_product = CreateProduct.Field()
  delete_product = DeleteProduct.Field()
  update_product = UpdateProduct.Field()
