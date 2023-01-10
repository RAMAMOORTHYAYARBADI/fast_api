# install the packages
pip install -r requirement.txt

# Alembic Initialization 
alembic init alembic

# Alembic migration 
alembic revision --autogenerate  -m "new1migration" (or) alembic revision --autogenerate
alembic upgrade head

# Run the fastapi 
uvicorn main:app --reload