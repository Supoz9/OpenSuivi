import sqlite3
import os

# Configuration des chemins
DB_DIR = "data"
DB_NAME = "openn_suivi.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def init_db():
    """Initialise la base de données et crée les tables si elles n'existent pas."""
    
    # Création du dossier 'data' s'il n'existe pas
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    # Connexion à la base (le fichier est créé s'il n'existe pas)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Activation des clés étrangères (indispensable pour le ON DELETE CASCADE)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table 1 : Eleves
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Eleves (
        id_eleve INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        photo_path TEXT,
        regime TEXT,
        statut_alerte TEXT DEFAULT 'VERT'
    )
    """)

    # Table 2 : Responsables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Responsables (
        id_responsable INTEGER PRIMARY KEY AUTOINCREMENT,
        id_eleve INTEGER,
        nom TEXT,
        prenom TEXT,
        lien_parente TEXT,
        telephone TEXT,
        email TEXT,
        FOREIGN KEY (id_eleve) REFERENCES Eleves(id_eleve) ON DELETE CASCADE
    )
    """)

    # Table 3 : Pfmp (Stages)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pfmp (
        id_pfmp INTEGER PRIMARY KEY AUTOINCREMENT,
        id_eleve INTEGER,
        periode TEXT,
        statut_recherche TEXT DEFAULT 'En recherche',
        entreprise_nom TEXT,
        entreprise_adresse TEXT,
        tuteur_nom TEXT,
        tuteur_tel TEXT,
        visite_faite INTEGER DEFAULT 0,
        FOREIGN KEY (id_eleve) REFERENCES Eleves(id_eleve) ON DELETE CASCADE
    )
    """)

    # Table 4 : Suivi_Journal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Suivi_Journal (
        id_note INTEGER PRIMARY KEY AUTOINCREMENT,
        id_eleve INTEGER,
        date_note TEXT NOT NULL,
        categorie TEXT,
        contenu TEXT NOT NULL,
        FOREIGN KEY (id_eleve) REFERENCES Eleves(id_eleve) ON DELETE CASCADE
    )
    """)

    # Table 5 : Checklist_Admin
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Checklist_Admin (
        id_check INTEGER PRIMARY KEY AUTOINCREMENT,
        id_eleve INTEGER,
        document_nom TEXT,
        statut_rendu INTEGER DEFAULT 0,
        FOREIGN KEY (id_eleve) REFERENCES Eleves(id_eleve) ON DELETE CASCADE
    )
    """)

    # Table 6 : Orientation (Spécifique TNE : CIEL / MELEC)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Orientation (
        id_orientation INTEGER PRIMARY KEY AUTOINCREMENT,
        id_eleve INTEGER UNIQUE,
        voeu_1 TEXT,
        voeu_2 TEXT,
        detail_reorientation TEXT,
        avis_equipe TEXT,
        classement_ciel INTEGER,
        classement_melec INTEGER,
        affectation_finale TEXT,
        FOREIGN KEY (id_eleve) REFERENCES Eleves(id_eleve) ON DELETE CASCADE
    )
    """)

    # Validation et fermeture
    conn.commit()
    conn.close()
    print(f"Succès : Base de données '{DB_NAME}' initialisée dans le dossier '{DB_DIR}'.")

# Ce bloc permet d'exécuter le script directement pour tester
if __name__ == "__main__":
    init_db()