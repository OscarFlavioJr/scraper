from fastapi import FastAPI
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT")
}

@app.get("/vagas")
def get_vagas():
    # Conectando ao MySQL
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT titulo, link, empresa FROM vagas")
        vagas = [{"titulo": row[0], "link": row[1], "empresa": row[2]} for row in cursor.fetchall()]
        return vagas
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()