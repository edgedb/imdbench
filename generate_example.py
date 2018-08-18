import dataset
from edgedb.importer import generate_eql


dgen = dataset.DataGenerator(people=100, users=100, reviews=300)
eql = generate_eql(dgen)

print(eql)
