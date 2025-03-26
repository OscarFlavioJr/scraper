import mysql.connector
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT")
}

def conectar_banco():
    return mysql.connector.connect(**db_config)

def criar_tabela():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) UNIQUE,
            link VARCHAR(500) UNIQUE,
            empresa VARCHAR(100)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

criar_tabela()

options = webdriver.ChromeOptions()
options.add_argument("--headless")  
options.add_argument("user-agent=Mozilla/5.0")  
options.add_argument("--start-maximized") 
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def remover_iframes():
    driver.execute_script("""
        var iframes = document.getElementsByTagName('iframe');
        for (var i = 0; i < iframes.length; i++) {
            iframes[i].parentNode.removeChild(iframes[i]);
        }
    """)

def inserir_vaga_no_banco(titulo, link, empresa):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO vagas (titulo, link, empresa) VALUES (%s, %s, %s)", 
            (titulo, link, empresa)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Erro ao inserir no banco: {err}")

def carregar_vagas():
    empresa = "Fleury"
    print("[+] Acessando Vagas.com.br...")
    url = "https://www.vagas.com.br/vagas-de-Fleury"
    driver.get(url)
    driver.implicitly_wait(5)

    while True:
        try:
            remover_iframes() 
            botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "maisVagas")))
            driver.execute_script("arguments[0].scrollIntoView();", botao)
            time.sleep(1)  
            driver.execute_script("arguments[0].click();", botao)
            print("[+] Carregando mais vagas...")
            time.sleep(3)
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
            print("[+] Todas as vagas foram carregadas ou botão inacessível.")
            break
        except Exception as e:
            print(f"[!] Erro inesperado ao carregar mais vagas: {e}")
            break

    base_url = "https://www.vagas.com.br"
    vagas = driver.find_elements(By.CSS_SELECTOR, "h2.cargo a") 
    total_vagas = 0
    
    for vaga in vagas:
        titulo = vaga.text.strip()
        link = vaga.get_attribute("href")
        if link.startswith("/"):
            link = base_url + link
        inserir_vaga_no_banco(titulo, link, empresa)
        print(f"[+] {titulo} - {link} ({empresa})")
        total_vagas += 1

    print(f"[+] Total de vagas coletadas do Grupo Fleury: {total_vagas}")

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"\r[+] Próxima verificação em {timer}", end="", flush=True)
        time.sleep(1)
        t -= 1
    print("\n")

INTERVALO_VERIFICACAO = 51

try:
    while True:
        print("\n[+] Iniciando nova verificação...")
        carregar_vagas()
        print("[+] Verificação concluída. Aguardando próxima execução...\n")
        countdown(INTERVALO_VERIFICACAO)
finally:
    driver.quit()
    print("[+] Scraping finalizado e dados salvos no banco de dados!")
