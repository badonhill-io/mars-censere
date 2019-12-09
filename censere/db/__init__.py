
import peewee

db = peewee.SqliteDatabase( None )

import censere.models


## 
# Each model (in models/) needs to have its table created
# so there should be an entry here.
def create_tables():

    censere.models.Settler.create_table()
    censere.models.Relationship.create_table()
    censere.models.Simulation.create_table()
    censere.models.Summary.create_table()
