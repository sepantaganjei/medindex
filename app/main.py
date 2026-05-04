# Main program
# Wiring and view calling.

# Create tabels in the DB
from db.database import engine
from db import models

print("Creating tables...")
models.Base.metadata.create_all(bind=engine)
print("Done.")

# Page visualization
add_dataset()
