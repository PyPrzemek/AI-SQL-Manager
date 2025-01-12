from PyQt6.QtWidgets import *
import requests
import os
import zipfile
import sqlite3
import requests
import zipfile
import os
from fpdf import FPDF
from cryptography.fernet import Fernet
import openai


# ----------------------------
# AI-Powered SQL Query Generation
# ----------------------------

def generate_sql_query(prompt: str, table_schema: str) -> str:
    """Generuje zapytanie SQL na podstawie opisu użytkownika i schematu tabeli."""
    try:
        openai.api_key = "YOUR_OPENAI_API_KEY"  # Wprowadź swój klucz API OpenAI

        full_prompt = (
            f"Opis użytkownika: {prompt}\n"
            f"Schemat tabeli:\n{table_schema}\n"
            "Wygeneruj poprawne zapytanie SQL."
        )

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=200,
            temperature=0.3
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Błąd w generowaniu zapytania SQL: {e}"


# ----------------------------
# Obsługa SQL Server
# ----------------------------

def connect_to_sql_server(server: str, database: str, username: str, password: str) -> str:
    """Łączenie z SQL Server."""
    try:
        import pyodbc
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        conn = pyodbc.connect(connection_string)
        conn.close()
        return "Połączono z SQL Server pomyślnie."
    except Exception as e:
        return f"Błąd podczas łączenia z SQL Server: {e}"


# ----------------------------
# Szyfrowanie danych uwierzytelniających
# ----------------------------

def generate_encryption_key() -> bytes:
    """Generuje klucz szyfrowania."""
    return Fernet.generate_key()


def encrypt_credentials(key: bytes, data: str) -> bytes:
    """Szyfruje dane uwierzytelniające."""
    return Fernet(key).encrypt(data.encode())


def decrypt_credentials(key: bytes, encrypted_data: bytes) -> str:
    """Deszyfruje dane uwierzytelniające."""
    return Fernet(key).decrypt(encrypted_data).decode()


# ----------------------------
# Automatyczne aktualizacje
# ----------------------------

def check_for_updates(current_version: str) -> str:
    """Sprawdza dostępność nowej wersji aplikacji na GitHubie."""
    try:
        repo_api_url = "https://api.github.com/repos/PyPrzemek/AI-SQL-Manager/releases/latest"
        download_url = "https://github.com/PyPrzemek/AI-SQL-Manager/archive/refs/heads/main.zip"


        response = requests.get(repo_api_url)
        response.raise_for_status()
        latest_version = response.json()["tag_name"]

        if latest_version > current_version:
            download_response = requests.get(download_url, stream=True)
            download_response.raise_for_status()
            
            zip_path = "update.zip"
            with open(zip_path, "wb") as f:
                f.write(download_response.content)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)

            return f"Zaktualizowano do wersji {latest_version}."
        else:
            return "Aplikacja jest aktualna."
    except Exception as e:
        return f"Błąd podczas sprawdzania aktualizacji: {e}"


# ----------------------------
# Aplikacja PyQt6
# ----------------------------

class MainWindow(QMainWindow):
    """Główne okno aplikacji."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Powered SQL Manager")
        self.setGeometry(200, 200, 800, 600)

        # Połączenie z lokalną bazą danych SQLite
        self.local_db_connection = sqlite3.connect('ai_long_term_memory.db')

        # Główne layouty
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        # Zakładki
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Zakładka SQL Query Generation
        self.query_tab = self.create_query_tab()
        self.tabs.addTab(self.query_tab, "Generowanie SQL")

        # Zakładka Aktualizacje
        self.update_tab = self.create_update_tab()
        self.tabs.addTab(self.update_tab, "Aktualizacje")

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # Sprawdzenie aktualizacji przy uruchomieniu
        self.check_for_updates_on_startup()

    def create_query_tab(self):
        """Tworzy zakładkę Generowania SQL."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Opisz, co chcesz zrobić (np. Pobierz wszystkie dane użytkowników).")
        layout.addWidget(self.query_input)

        self.schema_input = QTextEdit()
        self.schema_input.setPlaceholderText("Podaj schemat tabeli (np. Tabela: Users, Kolumny: id, name, email).")
        layout.addWidget(self.schema_input)

        self.generate_button = QPushButton("Generuj zapytanie SQL")
        self.generate_button.clicked.connect(self.generate_query)
        layout.addWidget(self.generate_button)

        self.result_label = QLabel("Wynik zapytania SQL:")
        layout.addWidget(self.result_label)

        tab.setLayout(layout)
        return tab

    def create_update_tab(self):
        """Tworzy zakładkę Aktualizacji."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.update_button = QPushButton("Sprawdź aktualizacje")
        self.update_button.clicked.connect(self.check_for_updates_on_click)
        layout.addWidget(self.update_button)

        self.update_status_label = QLabel("Status aktualizacji: Nie sprawdzono.")
        layout.addWidget(self.update_status_label)

        tab.setLayout(layout)
        return tab

    def generate_query(self):
        """Generuje zapytanie SQL na podstawie opisu użytkownika."""
        prompt = self.query_input.toPlainText()
        schema = self.schema_input.toPlainText()

        if not prompt or not schema:
            QMessageBox.warning(self, "Błąd", "Wprowadź opis i schemat tabeli.")
            return

        query = generate_sql_query(prompt, schema)
        self.result_label.setText(f"Wynik zapytania SQL:\n{query}")

    def check_for_updates_on_click(self):
        """Sprawdza aktualizacje po kliknięciu."""
        current_version = "1.0.0"
        status = check_for_updates(current_version)
        self.update_status_label.setText(f"Status aktualizacji: {status}")

    def check_for_updates_on_startup(self):
        """Sprawdza aktualizacje przy uruchomieniu aplikacji."""
        current_version = "1.0.0"
        status = check_for_updates(current_version)
        QMessageBox.information(self, "Aktualizacja", status)


# Uruchomienie aplikacji
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
