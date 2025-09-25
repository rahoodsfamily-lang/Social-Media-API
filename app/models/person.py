from neomodel import StructuredNode, StringProperty, IntegerProperty

class Person(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    age = IntegerProperty(required=True)
