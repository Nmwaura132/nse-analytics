from database import Base, engine
import os

if os.path.exists("portfolio.db"):
    print("DB exists.")
else:
    print("DB does not exist. Creating...")
    Base.metadata.create_all(engine)
    if os.path.exists("portfolio.db"):
        print("DB created successfully.")
    else:
        print("Failed to create DB.")
