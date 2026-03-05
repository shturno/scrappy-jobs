from sqlmodel import create_engine
try:
    engine = create_engine("postgresql://user:pass@localhost:5432/dbname")
    print("URL parsed OK")
except Exception as e:
    print("Error:", e)
