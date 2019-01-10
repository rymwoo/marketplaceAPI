#dummyMarketplace/schema.py
import graphene
import inventory.schema, shoppingCart.schema

class Query(inventory.schema.Query,shoppingCart.schema.Query,graphene.ObjectType):
  pass

class Mutation(inventory.schema.Mutation,shoppingCart.schema.Mutation, graphene.ObjectType):
  pass

schema = graphene.Schema(query=Query, mutation=Mutation)