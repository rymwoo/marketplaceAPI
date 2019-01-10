#shoppingCart/models.py

from django.db import models
from inventory.models import Product
from django.contrib.sessions.models import Session
from functools import reduce

class ShoppingCart(models.Model):
  shoppingCartId = models.AutoField(primary_key=True)
  #django generated session key is 38 chars long
  shoppingCartKey = models.CharField(max_length=38)
  @property
  def shoppingCartValue(self):
    val = 0
    for order in self.shoppingCartItems.all():
      val+= order.productCount*order.product.productPrice
    return val

class OrderListing(models.Model):
  orderListingId = models.AutoField(primary_key=True)
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  shoppingCart = models.ForeignKey(ShoppingCart, related_name="shoppingCartItems",on_delete=models.CASCADE)
  productCount = models.IntegerField(default=0)

  def __str__(self):
    return (str(self.amount)+" "+str(self.product.name))
