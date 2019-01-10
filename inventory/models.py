from django.db import models

class Product(models.Model):
  productId = models.AutoField(primary_key=True)
  productName = models.CharField(max_length = 100)
  productPrice = models.DecimalField(max_digits=10,decimal_places=2)
  productInventory = models.IntegerField(default = 0)

  def __str__(self):
    return self.name