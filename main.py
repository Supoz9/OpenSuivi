import customtkinter as ctk
from tkinter import messagebox, filedialog
import sqlite3
import os
import json
from PIL import Image

# --- Gestion de la Configuration ---
CONFIG_FILE = os.path.join("data", "config.json")

def load_theme():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("theme", "System")
        except Exception:
            pass
    return "System"

def save_theme(theme):
    os.makedirs("data", exist_ok=True)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"theme": theme}, f)
    except Exception:
        pass

# Configuration de base de CustomTkinter
ctk.set_appearance_mode(load_theme())  # S'adapte au mode sombre/clair de l'OS ou config sauvegardée
ctk.set_default_color_theme("green")  # Thème vert (Open Source vibe)

class OpenSuiviApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        from database import init_db
        init_db()

        # --- CONFIGURATION DE LA FENÊTRE ---
        self.title("OpenSuivi - Gestion de Classe 2TNE")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # --- Favicon ---
        try:
            import tkinter as tk
            icon_img = tk.PhotoImage(file=os.path.join("assets", "favicon.png"))
            self.iconphoto(False, icon_img)
        except Exception as e:
            print("Erreur favicon:", e)

        # Grille principale : 1 ligne, 2 colonnes (Menu à gauche, Contenu à droite)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # 1. LA BARRE LATÉRALE (SIDEBAR)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Pousse le bouton Quitter vers le bas

        # Titre de l'application (Logo)
        try:
            img_logo = Image.open(os.path.join("assets", "logo.png"))
            ratio = img_logo.width / img_logo.height
            new_width = 180
            new_height = int(new_width / ratio)
            
            logo_img_ctk = ctk.CTkImage(light_image=img_logo, dark_image=img_logo, size=(new_width, new_height))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=logo_img_ctk)
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        except Exception as e:
            print("Erreur logo:", e)
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="OpenSuivi", font=ctk.CTkFont(size=26, weight="bold"))
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Boutons de navigation
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Tableau de Bord", command=lambda: [self.rafraichir_dashboard(), self.afficher_page("dashboard")])
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_eleves = ctk.CTkButton(self.sidebar_frame, text="Mes Élèves", command=lambda: self.afficher_page("eleves"))
        self.btn_eleves.grid(row=2, column=0, padx=20, pady=10)

        self.btn_pfmp = ctk.CTkButton(self.sidebar_frame, text="Suivi PFMP", command=lambda: self.afficher_page("pfmp"))
        self.btn_pfmp.grid(row=3, column=0, padx=20, pady=10)

        self.btn_orientation = ctk.CTkButton(self.sidebar_frame, text="Orientation", command=lambda: self.afficher_page("orientation"))
        self.btn_orientation.grid(row=4, column=0, padx=20, pady=10)

        # On s'assure que la ligne 5 prend tout l'espace vide pour pousser la suite vers le bas
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.sidebar_frame.grid_rowconfigure(6, weight=0)

        # Bouton Configuration (Engrenage)
        self.btn_config = ctk.CTkButton(self.sidebar_frame, text="⚙️ Configuration", fg_color="transparent", text_color=("gray10", "#DCE4EE"), hover_color=("gray70", "gray30"), command=lambda: self.afficher_page("configuration"))
        self.btn_config.grid(row=6, column=0, padx=20, pady=(20, 5))

        # Bouton Quitter
        self.btn_quitter = ctk.CTkButton(self.sidebar_frame, text="Quitter", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.destroy)
        self.btn_quitter.grid(row=7, column=0, padx=20, pady=(5, 20))


        # ==========================================
        # 2. LES ZONES DE CONTENU (PAGES)
        # ==========================================
        # Dictionnaire pour stocker toutes nos "pages"
        self.pages = {}
        
        # --- Création des vues détaillées du dashboard ---
        self.pages["details_suivi"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.pages["details_pfmp"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.pages["details_ori"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # Page : Tableau de bord
        self.pages["dashboard"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        header_dash = ctk.CTkFrame(self.pages["dashboard"], fg_color="transparent")
        header_dash.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header_dash, text="Tableau de Bord", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        self.btn_export_pdf = ctk.CTkButton(header_dash, text="📄 Exporter en PDF", font=ctk.CTkFont(weight="bold"), fg_color="#10b981", hover_color="#059669", command=self.exporter_pdf_dashboard)
        self.btn_export_pdf.pack(side="right")
        
        self.dash_content = ctk.CTkScrollableFrame(self.pages["dashboard"], fg_color="transparent")
        self.dash_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.card_suivi = ctk.CTkFrame(self.dash_content, corner_radius=15, border_width=2, border_color="#3b82f6")
        self.card_suivi.pack(fill="x", pady=15)
        
        self.card_pfmp = ctk.CTkFrame(self.dash_content, corner_radius=15, border_width=2, border_color="#10b981")
        self.card_pfmp.pack(fill="x", pady=15)
        
        self.card_ori = ctk.CTkFrame(self.dash_content, corner_radius=15, border_width=2, border_color="#8b5cf6")
        self.card_ori.pack(fill="x", pady=15)

        # Page : Élèves
        self.pages["eleves"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # --- En-tête de la page ---
        header_eleves = ctk.CTkFrame(self.pages["eleves"], fg_color="transparent")
        header_eleves.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header_eleves, text="Gestion des Élèves", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Le bouton d'ajout
        btn_ajouter_eleve = ctk.CTkButton(header_eleves, text="+ Ajouter un élève", font=ctk.CTkFont(weight="bold"), command=self.ouvrir_formulaire_ajout)
        btn_ajouter_eleve.pack(side="right")

        # --- Zone de liste des élèves ---
        # On utilise un CTkScrollableFrame pour pouvoir faire défiler si tu as beaucoup d'élèves
        self.liste_eleves_frame = ctk.CTkScrollableFrame(self.pages["eleves"], corner_radius=10)
        self.liste_eleves_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Petit texte temporaire pour voir la zone
        ctk.CTkLabel(self.liste_eleves_frame, text="La liste de tes élèves apparaîtra ici.", text_color="gray").pack(pady=20)

        # Page : Fiche Élève (Détails)
        self.pages["fiche_eleve"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # En-tête Fiche Élève
        self.header_fiche = ctk.CTkFrame(self.pages["fiche_eleve"], fg_color="transparent")
        self.header_fiche.pack(fill="x", pady=20, padx=20)
        
        self.btn_retour_liste = ctk.CTkButton(self.header_fiche, text="⬅ Retour", width=80, fg_color="gray", hover_color="darkgray", command=lambda: self.afficher_page("eleves"))
        self.btn_retour_liste.pack(side="left")
        
        self.titre_fiche = ctk.CTkLabel(self.header_fiche, text="Fiche Élève", font=ctk.CTkFont(size=24, weight="bold"))
        self.titre_fiche.pack(side="left", padx=20)
        
        self.eleve_actuel_id = None
        
        # Page : PFMP
        self.pages["pfmp"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # En-tête de la page PFMP
        header_pfmp = ctk.CTkFrame(self.pages["pfmp"], fg_color="transparent")
        header_pfmp.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header_pfmp, text="Suivi des Stages (PFMP)", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Layout 2 colonnes : Liste gauche (30%), Détails droite (70%)
        self.pfmp_grid = ctk.CTkFrame(self.pages["pfmp"], fg_color="transparent")
        self.pfmp_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.pfmp_grid.columnconfigure(0, weight=1) # 30%
        self.pfmp_grid.columnconfigure(1, weight=3) # 70%
        self.pfmp_grid.rowconfigure(0, weight=1)
        
        # Colonne gauche : Liste des élèves
        self.pfmp_frame_gauche = ctk.CTkScrollableFrame(self.pfmp_grid, corner_radius=10)
        self.pfmp_frame_gauche.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Colonne droite : Détails des stages de l'élève sélectionné
        self.pfmp_frame_droite = ctk.CTkFrame(self.pfmp_grid, corner_radius=10, fg_color=("gray85", "gray20"))
        self.pfmp_frame_droite.grid(row=0, column=1, sticky="nsew")
        
        # Header colonne droite
        self.pfmp_header_droite = ctk.CTkFrame(self.pfmp_frame_droite, fg_color="transparent")
        self.pfmp_header_droite.pack(fill="x", pady=10, padx=10)
        
        self.pfmp_titre_eleve = ctk.CTkLabel(self.pfmp_header_droite, text="👈 Sélectionnez un élève", font=ctk.CTkFont(size=20, weight="bold"))
        self.pfmp_titre_eleve.pack(side="left", padx=10)
        
        self.btn_ajouter_stage = ctk.CTkButton(self.pfmp_header_droite, text="+ Ajouter un stage", state="disabled", command=self.ouvrir_ajout_stage)
        self.btn_ajouter_stage.pack(side="right", padx=10)
        
        self.pfmp_stages_liste = ctk.CTkScrollableFrame(self.pfmp_frame_droite, fg_color="transparent")
        self.pfmp_stages_liste.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.pfmp_eleve_actuel = None

        # Page : Orientation
        self.pages["orientation"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # En-tête
        header_ori = ctk.CTkFrame(self.pages["orientation"], fg_color="transparent")
        header_ori.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header_ori, text="Orientation 2TNE (CIEL / MELEC)", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Layout 2 colonnes
        self.ori_grid = ctk.CTkFrame(self.pages["orientation"], fg_color="transparent")
        self.ori_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.ori_grid.columnconfigure(0, weight=1)
        self.ori_grid.columnconfigure(1, weight=3)
        self.ori_grid.rowconfigure(0, weight=1)
        
        # Colonne gauche
        self.ori_frame_gauche = ctk.CTkScrollableFrame(self.ori_grid, corner_radius=10)
        self.ori_frame_gauche.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Colonne droite
        self.ori_frame_droite = ctk.CTkScrollableFrame(self.ori_grid, corner_radius=10, fg_color=("gray85", "gray20"))
        self.ori_frame_droite.grid(row=0, column=1, sticky="nsew")
        
        self.ori_titre_eleve = ctk.CTkLabel(self.ori_frame_droite, text="👈 Sélectionnez un élève", font=ctk.CTkFont(size=20, weight="bold"))
        self.ori_titre_eleve.pack(pady=20)
        
        self.ori_formulaire = ctk.CTkFrame(self.ori_frame_droite, fg_color="transparent")
        # Sera packé quand un élève est sélectionné
        
        self.ori_eleve_actuel = None

        # Page : Configuration
        self.pages["configuration"] = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.pages["configuration"], text="⚙️ Configuration", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20, padx=20, anchor="w")

        # --- Section Apparence ---
        ctk.CTkLabel(self.pages["configuration"], text="Apparence", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.menu_theme = ctk.CTkOptionMenu(self.pages["configuration"], values=["System", "Dark", "Light"], command=self.changer_theme)
        self.menu_theme.set(load_theme())
        self.menu_theme.pack(pady=5, padx=20, anchor="w")

        # --- Section À propos ---
        ctk.CTkLabel(self.pages["configuration"], text="À propos de OpenSuivi", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(40, 5), padx=20, anchor="w")
        
        description = (
            "OpenSuivi est un outil gratuit conçu par un enseignant, pour les enseignants, dans le but de simplifier "
            "le suivi individualisé, les recherches de stages (PFMP) et l'orientation des élèves de 2TNE."
        )
        ctk.CTkLabel(self.pages["configuration"], text=description, justify="left", wraplength=700).pack(pady=5, padx=20, anchor="w")

        info_logiciel = (
            " Version : 1.0.0\n"
            " Licence : MIT (Open Source)\n"
            " Auteur : Mennock Barthélémy (Supoz9) - Professeur de CIEL\n"
            " Établissement : Lycée Claude Chappe - Arnage\n"
            " Développé pour la Forge des Communs Numériques de l'Éducation Nationale"
        )
        ctk.CTkLabel(self.pages["configuration"], text=info_logiciel, justify="left", text_color="gray").pack(pady=10, padx=20, anchor="w")
        
        import webbrowser
        btn_github = ctk.CTkButton(self.pages["configuration"], text="🌐 Voir sur GitHub", fg_color="#333333", hover_color="#555555", command=lambda: webbrowser.open("https://github.com/Supoz9"))
        btn_github.pack(pady=5, padx=20, anchor="w")

        # Charger les données initiales
        self.charger_liste_eleves()
        self.charger_pfmp_liste_eleves()
        self.charger_orientation_liste_eleves()
        self.rafraichir_dashboard()

        # Afficher le tableau de bord par défaut au démarrage
        self.afficher_page("dashboard")

    def afficher_page(self, nom_page):
        """Cache toutes les pages et affiche uniquement celle demandée."""
        for page in self.pages.values():
            page.grid_forget() # Retire la page de l'affichage
        
        # Affiche la page sélectionnée dans la colonne de droite (colonne 1)
        self.pages[nom_page].grid(row=0, column=1, sticky="nsew")
    
    def changer_theme(self, nouveau_theme: str):
        """Change le thème de l'application à la volée et sauvegarde le choix."""
        ctk.set_appearance_mode(nouveau_theme)
        save_theme(nouveau_theme)
    
    def ouvrir_formulaire_ajout(self):
        """Ouvre une fenêtre modale pour ajouter un nouvel élève."""
        # On garde une référence à la fenêtre principale
        app_principale = self
        
        # 1. Création de la fenêtre par-dessus la principale
        fenetre_ajout = ctk.CTkToplevel(self)
        fenetre_ajout.title("Ajouter un élève")
        fenetre_ajout.geometry("400x450")
        fenetre_ajout.resizable(False, False) # On empêche de redimensionner
        
        # 2. Rendre la fenêtre "modale"
        # grab_set() empêche de cliquer sur la fenêtre principale tant que la pop-up est ouverte
        fenetre_ajout.update()
        fenetre_ajout.grab_set()

        # --- CONTENU DU FORMULAIRE ---
        ctk.CTkLabel(fenetre_ajout, text="Nouvel Élève", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 20))

        # Champ Nom
        ctk.CTkLabel(fenetre_ajout, text="Nom :").pack(anchor="w", padx=40)
        entree_nom = ctk.CTkEntry(fenetre_ajout, width=320, placeholder_text="Ex: DUPONT")
        entree_nom.pack(pady=(0, 15), padx=40)

        # Champ Prénom
        ctk.CTkLabel(fenetre_ajout, text="Prénom :").pack(anchor="w", padx=40)
        entree_prenom = ctk.CTkEntry(fenetre_ajout, width=320, placeholder_text="Ex: Lucas")
        entree_prenom.pack(pady=(0, 15), padx=40)

        # Champ Régime (Menu déroulant)
        ctk.CTkLabel(fenetre_ajout, text="Régime :").pack(anchor="w", padx=40)
        combo_regime = ctk.CTkOptionMenu(fenetre_ajout, values=["Externe", "Demi-pensionnaire", "Interne"], width=320)
        combo_regime.pack(pady=(0, 30), padx=40)

        # 3. Fonction interne pour récupérer les données et les envoyer en BDD
        def valider_saisie():
            nom = entree_nom.get().strip().upper()
            prenom = entree_prenom.get().strip().capitalize()
            regime = combo_regime.get()
            
            if not nom or not prenom:
                messagebox.showerror("Erreur", "Veuillez remplir le nom et le prénom.")
                fenetre_ajout.lift() 
                return

            # On désactive le bouton pour éviter les clics multiples rapides
            btn_enregistrer.configure(state="disabled")

            # --- CONNEXION À LA BASE DE DONNÉES ---
            try:
                db_path = os.path.join("data", "openn_suivi.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Vérification des doublons
                cursor.execute("SELECT id_eleve FROM Eleves WHERE nom = ? AND prenom = ?", (nom, prenom))
                if cursor.fetchone():
                    messagebox.showwarning("Doublon", f"L'élève {prenom} {nom} existe déjà dans la base !")
                    btn_enregistrer.configure(state="normal")
                    fenetre_ajout.lift()
                    conn.close()
                    return
                    
                # Insertion sécurisée (les ? empêchent les injections SQL)
                cursor.execute("INSERT INTO Eleves (nom, prenom, regime) VALUES (?, ?, ?)", (nom, prenom, regime))
                conn.commit()
                conn.close()
                    
                # Succès ! On ferme la pop-up
                fenetre_ajout.destroy()
                    
                # On rafraîchit la liste pour voir le nouvel élève apparaître !
                self.charger_liste_eleves()
                self.charger_pfmp_liste_eleves()
                self.charger_orientation_liste_eleves()
                
                messagebox.showinfo("Succès", f"L'élève {prenom} {nom} a été ajouté avec succès !")
                    
            except Exception as e:
                messagebox.showerror("Erreur BDD", f"Impossible d'enregistrer l'élève : {e}")
                btn_enregistrer.configure(state="normal")
                fenetre_ajout.lift()

        # Bouton d'enregistrement
        btn_enregistrer = ctk.CTkButton(fenetre_ajout, text="Enregistrer l'élève", command=valider_saisie)
        btn_enregistrer.pack(pady=10)

    def charger_liste_eleves(self):
        """Lit la BDD et affiche les élèves dans la liste."""
        # 1. On vide la zone d'affichage actuelle
        for widget in self.liste_eleves_frame.winfo_children():
            widget.destroy()

        # 2. Récupération des données depuis SQLite
        try:
            db_path = os.path.join("data", "openn_suivi.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id_eleve, nom, prenom, regime, photo_path FROM Eleves")
            eleves = cursor.fetchall()
            conn.close()

            # 3. Création d'une ligne pour chaque élève trouvé
            for eleve in eleves:
                id_el, nom, prenom, regime, photo_path = eleve
                
                ligne_frame = ctk.CTkFrame(self.liste_eleves_frame, fg_color=("gray85", "gray20"))
                ligne_frame.pack(fill="x", pady=5, padx=5)

                # --- Photo Avatar ---
                img_size = 40
                avatar_img = None
                try:
                    if photo_path and os.path.exists(photo_path):
                        pil_img = Image.open(photo_path)
                        avatar_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(img_size, img_size))
                except Exception:
                    pass

                if avatar_img:
                    btn_avatar = ctk.CTkButton(ligne_frame, text="", image=avatar_img, width=img_size, height=img_size, corner_radius=img_size//2, fg_color="transparent", hover_color=("gray70", "gray30"), command=lambda i=id_el, p=photo_path: self.changer_photo(i, p))
                else:
                    btn_avatar = ctk.CTkButton(ligne_frame, text=f"{prenom[0]}{nom[0]}", font=ctk.CTkFont(weight="bold"), width=img_size, height=img_size, corner_radius=img_size//2, command=lambda i=id_el, p=photo_path: self.changer_photo(i, p))
                btn_avatar.pack(side="left", padx=10, pady=10)

                infos = f"{nom} {prenom}  •  {regime}"
                ctk.CTkLabel(ligne_frame, text=infos, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=12)

                # Bouton Supprimer
                btn_suppr = ctk.CTkButton(
                    ligne_frame, 
                    text="🗑️ Supprimer", 
                    fg_color="#ef4444", 
                    hover_color="#b91c1c", 
                    width=100,
                    command=lambda i=id_el, n=nom, p=prenom: self.supprimer_eleve(i, n, p)
                )
                btn_suppr.pack(side="right", padx=15, pady=10)

                # Bouton Détails
                btn_details = ctk.CTkButton(
                    ligne_frame,
                    text="🔍 Détails",
                    width=100,
                    command=lambda i=id_el, n=nom, p=prenom, r=regime: self.ouvrir_fiche_eleve(i, n, p, r)
                )
                btn_details.pack(side="right", padx=(0, 10), pady=10)

        except Exception as e:
            print(f"Erreur lors du chargement : {e}")

    def supprimer_eleve(self, id_eleve, nom, prenom):
        """Demande confirmation et supprime l'élève de la BDD."""
        confirmation = messagebox.askyesno(
            "⚠️ Confirmation", 
            f"Es-tu sûr de vouloir supprimer définitivement {prenom} {nom} ?"
        )
        
        if confirmation:
            try:
                db_path = os.path.join("data", "openn_suivi.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Activer les clés étrangères pour ce connecteur afin d'appliquer le CASCADE
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Nettoyage des orphelins (au cas où des élèves auraient été supprimés avant cette mise à jour)
                cursor.execute("DELETE FROM Responsables WHERE id_eleve NOT IN (SELECT id_eleve FROM Eleves)")
                cursor.execute("DELETE FROM Pfmp WHERE id_eleve NOT IN (SELECT id_eleve FROM Eleves)")
                cursor.execute("DELETE FROM Suivi_Journal WHERE id_eleve NOT IN (SELECT id_eleve FROM Eleves)")
                cursor.execute("DELETE FROM Checklist_Admin WHERE id_eleve NOT IN (SELECT id_eleve FROM Eleves)")
                cursor.execute("DELETE FROM Orientation WHERE id_eleve NOT IN (SELECT id_eleve FROM Eleves)")
                
                # Suppression de l'élève (les dépendances seront supprimées automatiquement désormais)
                cursor.execute("DELETE FROM Eleves WHERE id_eleve = ?", (id_eleve,))
                
                conn.commit()
                conn.close()
                
                # On rafraîchit la liste pour supprimer la ligne visuellement
                self.charger_liste_eleves()
                self.charger_pfmp_liste_eleves()
                self.charger_orientation_liste_eleves()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer l'élève : {e}")

    def changer_photo(self, id_eleve, ancien_chemin):
        import datetime
        chemin_fichier = filedialog.askopenfilename(
            title="Choisir une photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        
        if chemin_fichier:
            try:
                # Créer le dossier si nécessaire
                dossier_photos = os.path.join("data", "photos")
                os.makedirs(dossier_photos, exist_ok=True)
                
                # Nom de fichier unique
                ext = os.path.splitext(chemin_fichier)[1]
                nouveau_nom = f"eleve_{id_eleve}_{int(datetime.datetime.now().timestamp())}{ext}"
                nouveau_chemin = os.path.join(dossier_photos, nouveau_nom)
                
                # Rogner en carré
                img = Image.open(chemin_fichier)
                taille_min = min(img.size)
                left = (img.width - taille_min) // 2
                top = (img.height - taille_min) // 2
                right = (img.width + taille_min) // 2
                bottom = (img.height + taille_min) // 2
                img_carree = img.crop((left, top, right, bottom))
                img_carree.save(nouveau_chemin)
                
                # Mettre à jour la BDD
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("UPDATE Eleves SET photo_path = ? WHERE id_eleve = ?", (nouveau_chemin, id_eleve))
                conn.commit()
                conn.close()
                
                # Supprimer l'ancienne
                if ancien_chemin and os.path.exists(ancien_chemin):
                    try:
                        os.remove(ancien_chemin)
                    except Exception:
                        pass
                        
                # Rafraîchir
                self.charger_liste_eleves()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de changer la photo : {e}")

    # ==========================================
    # MÉTHODES FICHE ÉLÈVE
    # ==========================================
    def ouvrir_fiche_eleve(self, id_eleve, nom, prenom, regime):
        self.eleve_actuel_id = id_eleve
        fenetre_fiche = ctk.CTkToplevel(self)
        fenetre_fiche.title(f"Fiche : {prenom} {nom}")
        fenetre_fiche.geometry("800x600")
        
        self.titre_fiche.configure(text=f"{prenom} {nom} ({regime})")
        
        # Onglets
        tabview = ctk.CTkTabview(fenetre_fiche)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)

        tabview.add("Infos & Responsables")
        tabview.add("Journal de Suivi")
        tabview.add("Bilan Global")
        
        # Contenu Onglet Responsables
        self.frame_responsables = ctk.CTkScrollableFrame(tabview.tab("Infos & Responsables"))
        self.frame_responsables.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.btn_ajouter_resp = ctk.CTkButton(tabview.tab("Infos & Responsables"), text="+ Ajouter un responsable", command=self.ouvrir_ajout_responsable)
        self.btn_ajouter_resp.pack(pady=10)

        # Contenu Onglet Journal
        self.frame_journal = ctk.CTkScrollableFrame(tabview.tab("Journal de Suivi"))
        self.frame_journal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.btn_ajouter_note = ctk.CTkButton(tabview.tab("Journal de Suivi"), text="+ Ajouter une note", command=self.ouvrir_ajout_journal)
        self.btn_ajouter_note.pack(pady=10)

        self.charger_responsables()
        self.charger_journal()
        
        # ==================================
        # ONGLET 3 : Bilan Global
        # ==================================
        onglet_bilan = tabview.tab("Bilan Global")
        
        sf_bilan = ctk.CTkScrollableFrame(onglet_bilan, fg_color="transparent")
        sf_bilan.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_export = ctk.CTkButton(sf_bilan, text="📄 Exporter le Bilan (PDF)", font=ctk.CTkFont(weight="bold"), fg_color="#8b5cf6", hover_color="#7c3aed", command=lambda: self.exporter_bilan_pdf(id_eleve, nom, prenom))
        btn_export.pack(pady=(0, 20))
        
        self.charger_bilan_eleve(id_eleve, sf_bilan)
        
        # On affiche la fenêtre
        fenetre_fiche.after(100, fenetre_fiche.grab_set)

    def charger_responsables(self):
        for widget in self.frame_responsables.winfo_children():
            widget.destroy()
            
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id_responsable, nom, prenom, lien_parente, telephone, email FROM Responsables WHERE id_eleve = ?", (self.eleve_actuel_id,))
            responsables = cursor.fetchall()
            conn.close()
            
            if not responsables:
                ctk.CTkLabel(self.frame_responsables, text="Aucun responsable renseigné.", text_color="gray").pack(pady=10)
            else:
                for resp in responsables:
                    id_resp, nom, prenom, lien, tel, email = resp
                    cadre = ctk.CTkFrame(self.frame_responsables)
                    cadre.pack(fill="x", pady=5, padx=5)
                    texte = f"👤 {prenom} {nom} ({lien})\n📞 {tel}  |  ✉️ {email}"
                    ctk.CTkLabel(cadre, text=texte, justify="left").pack(side="left", padx=15, pady=10)
                    
                    btn_suppr = ctk.CTkButton(cadre, text="🗑️", width=40, fg_color="#ef4444", hover_color="#b91c1c", command=lambda i=id_resp: self.supprimer_responsable(i))
                    btn_suppr.pack(side="right", padx=10, pady=10)
        except Exception as e:
            print("Erreur chargement responsables:", e)

    def supprimer_responsable(self, id_responsable):
        if messagebox.askyesno("Confirmation", "Supprimer ce responsable ?"):
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("DELETE FROM Responsables WHERE id_responsable = ?", (id_responsable,))
                conn.commit()
                conn.close()
                self.charger_responsables()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de suppression: {e}")

    def ouvrir_ajout_responsable(self):
        fen = ctk.CTkToplevel(self)
        fen.title("Ajouter Responsable")
        fen.geometry("400x450")
        
        ctk.CTkLabel(fen, text="Nom :").pack(pady=(10, 0))
        e_nom = ctk.CTkEntry(fen, width=300)
        e_nom.pack()
        
        ctk.CTkLabel(fen, text="Prénom :").pack(pady=(10, 0))
        e_prenom = ctk.CTkEntry(fen, width=300)
        e_prenom.pack()
        
        ctk.CTkLabel(fen, text="Lien (ex: Père, Mère, Tuteur) :").pack(pady=(10, 0))
        e_lien = ctk.CTkEntry(fen, width=300)
        e_lien.pack()
        
        ctk.CTkLabel(fen, text="Téléphone :").pack(pady=(10, 0))
        e_tel = ctk.CTkEntry(fen, width=300)
        e_tel.pack()
        
        ctk.CTkLabel(fen, text="Email :").pack(pady=(10, 0))
        e_email = ctk.CTkEntry(fen, width=300)
        e_email.pack()
        
        def valider():
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("INSERT INTO Responsables (id_eleve, nom, prenom, lien_parente, telephone, email) VALUES (?, ?, ?, ?, ?, ?)", 
                             (self.eleve_actuel_id, e_nom.get(), e_prenom.get(), e_lien.get(), e_tel.get(), e_email.get()))
                conn.commit()
                conn.close()
                fen.destroy()
                self.charger_responsables()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur BDD: {e}")
                
        ctk.CTkButton(fen, text="Enregistrer", command=valider).pack(pady=20)
        fen.after(100, fen.grab_set)

    def charger_journal(self):
        for widget in self.frame_journal.winfo_children():
            widget.destroy()
            
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id_note, date_note, categorie, contenu FROM Suivi_Journal WHERE id_eleve = ? ORDER BY id_note DESC", (self.eleve_actuel_id,))
            notes = cursor.fetchall()
            conn.close()
            
            if not notes:
                ctk.CTkLabel(self.frame_journal, text="Aucune note dans le journal.", text_color="gray").pack(pady=10)
            else:
                # Définition des couleurs et emojis par catégorie
                styles_cat = {
                    "Comportement": {"emoji": "⚠️", "color": "#f59e0b"}, # Orange
                    "Travail": {"emoji": "📚", "color": "#3b82f6"},      # Bleu
                    "Absence/Retard": {"emoji": "⏰", "color": "#ef4444"}, # Rouge
                    "Autre": {"emoji": "📌", "color": "gray"}            # Gris
                }

                for note in notes:
                    id_note, date_n, cat, contenu = note
                    style = styles_cat.get(cat, {"emoji": "📝", "color": "gray"})
                    
                    cadre = ctk.CTkFrame(self.frame_journal, border_width=2, border_color=style["color"])
                    cadre.pack(fill="x", pady=5, padx=5)
                    
                    header = ctk.CTkFrame(cadre, fg_color="transparent")
                    header.pack(fill="x", padx=10, pady=(5, 0))
                    
                    titre = f"{style['emoji']} [{date_n}] {cat}"
                    ctk.CTkLabel(header, text=titre, font=ctk.CTkFont(weight="bold"), text_color=style["color"]).pack(side="left")
                    
                    btn_suppr = ctk.CTkButton(header, text="🗑️", width=40, fg_color="#ef4444", hover_color="#b91c1c", command=lambda i=id_note: self.supprimer_note_journal(i))
                    btn_suppr.pack(side="right")
                    
                    ctk.CTkLabel(cadre, text=contenu, justify="left", wraplength=800).pack(anchor="w", padx=10, pady=(0, 5))
        except Exception as e:
            print("Erreur chargement journal:", e)

    def supprimer_note_journal(self, id_note):
        if messagebox.askyesno("Confirmation", "Supprimer cette note ?"):
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("DELETE FROM Suivi_Journal WHERE id_note = ?", (id_note,))
                conn.commit()
                conn.close()
                self.charger_journal()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de suppression: {e}")

    def ouvrir_ajout_journal(self):
        import datetime
        fen = ctk.CTkToplevel(self)
        fen.title("Ajouter une note")
        fen.geometry("400x350")
        
        ctk.CTkLabel(fen, text="Catégorie :").pack(pady=(10, 0))
        e_cat = ctk.CTkOptionMenu(fen, values=["Comportement", "Travail", "Absence/Retard", "Autre"], width=300)
        e_cat.pack()
        
        ctk.CTkLabel(fen, text="Détails :").pack(pady=(10, 0))
        e_contenu = ctk.CTkTextbox(fen, width=300, height=150)
        e_contenu.pack()
        
        def valider():
            try:
                date_jour = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("INSERT INTO Suivi_Journal (id_eleve, date_note, categorie, contenu) VALUES (?, ?, ?, ?)", 
                             (self.eleve_actuel_id, date_jour, e_cat.get(), e_contenu.get("1.0", "end").strip()))
                conn.commit()
                conn.close()
                fen.destroy()
                self.charger_journal()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur BDD: {e}")
                
        ctk.CTkButton(fen, text="Enregistrer", command=valider).pack(pady=20)
        fen.after(100, fen.grab_set)

    # ==========================================
    # MÉTHODES PFMP
    # ==========================================
    def charger_pfmp_liste_eleves(self):
        for widget in self.pfmp_frame_gauche.winfo_children():
            widget.destroy()
            
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id_eleve, nom, prenom FROM Eleves ORDER BY nom")
            eleves = cursor.fetchall()
            conn.close()
            
            for eleve in eleves:
                id_el, nom, prenom = eleve
                btn = ctk.CTkButton(
                    self.pfmp_frame_gauche, 
                    text=f"{nom} {prenom}", 
                    fg_color="transparent", 
                    text_color=("black", "white"),
                    hover_color=("gray70", "gray30"),
                    anchor="w",
                    command=lambda i=id_el, n=nom, p=prenom: self.afficher_stages_eleve(i, n, p)
                )
                btn.pack(fill="x", pady=2, padx=5)
        except Exception as e:
            print("Erreur PFMP:", e)

    def afficher_stages_eleve(self, id_eleve, nom, prenom):
        self.pfmp_eleve_actuel = id_eleve
        self.pfmp_titre_eleve.configure(text=f"Stages de {prenom} {nom}")
        self.btn_ajouter_stage.configure(state="normal")
        
        self.rafraichir_stages_droite()

    def rafraichir_stages_droite(self):
        for widget in self.pfmp_stages_liste.winfo_children():
            widget.destroy()
            
        if not self.pfmp_eleve_actuel:
            return
            
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id_pfmp, periode, statut_recherche, entreprise_nom, entreprise_adresse, tuteur_nom, tuteur_tel, visite_faite FROM Pfmp WHERE id_eleve = ?", (self.pfmp_eleve_actuel,))
            stages = cursor.fetchall()
            conn.close()
            
            if not stages:
                ctk.CTkLabel(self.pfmp_stages_liste, text="Aucun stage enregistré.", text_color="gray").pack(pady=20)
            else:
                for stage in stages:
                    id_pfmp, periode, statut, e_nom, e_adr, t_nom, t_tel, visite = stage
                    
                    couleurs_statut = {
                        "En recherche": "#ef4444",      # Rouge
                        "En attente": "#f59e0b",        # Orange
                        "Trouvé": "#10b981",            # Vert
                        "Terminé": "#3b82f6"            # Bleu
                    }
                    c_statut = couleurs_statut.get(statut, "gray")
                    
                    cadre = ctk.CTkFrame(self.pfmp_stages_liste, border_width=2, border_color=c_statut)
                    cadre.pack(fill="x", pady=10, padx=5)
                    
                    header = ctk.CTkFrame(cadre, fg_color="transparent")
                    header.pack(fill="x", padx=10, pady=5)
                    
                    ctk.CTkLabel(header, text=f"📅 {periode}", font=ctk.CTkFont(weight="bold", size=16)).pack(side="left")
                    ctk.CTkLabel(header, text=statut, text_color=c_statut, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20)
                    
                    btn_suppr = ctk.CTkButton(header, text="🗑️", width=40, fg_color="#ef4444", hover_color="#b91c1c", command=lambda i=id_pfmp: self.supprimer_stage(i))
                    btn_suppr.pack(side="right")
                    
                    btn_edit = ctk.CTkButton(header, text="✏️ Modifier", width=80, command=lambda s=stage: self.ouvrir_edition_stage(s))
                    btn_edit.pack(side="right", padx=10)
                    
                    corps = ctk.CTkFrame(cadre, fg_color="transparent")
                    corps.pack(fill="x", padx=10, pady=(0, 10))
                    
                    info_texte = f"🏢 Entreprise : {e_nom or 'Non définie'}\n"
                    info_texte += f"📍 Adresse : {e_adr or 'Non définie'}\n"
                    info_texte += f"👤 Tuteur : {t_nom or 'Non défini'} (📞 {t_tel or 'Non défini'})\n"
                    info_texte += f"✅ Visite effectuée : {'Oui' if visite else 'Non'}"
                    
                    ctk.CTkLabel(corps, text=info_texte, justify="left").pack(anchor="w")
        except Exception as e:
            print("Erreur:", e)

    def ouvrir_ajout_stage(self):
        fen = ctk.CTkToplevel(self)
        fen.title("Ajouter un stage")
        fen.geometry("400x250")
        
        ctk.CTkLabel(fen, text="Période / Dates du stage :").pack(pady=(10, 0))
        e_periode = ctk.CTkEntry(fen, width=300, placeholder_text="Ex: Du 12/11 au 24/11")
        e_periode.pack()
        
        def valider():
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("INSERT INTO Pfmp (id_eleve, periode, statut_recherche) VALUES (?, ?, 'En recherche')", (self.pfmp_eleve_actuel, e_periode.get()))
                conn.commit()
                conn.close()
                fen.destroy()
                self.rafraichir_stages_droite()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                
        ctk.CTkButton(fen, text="Créer la fiche de stage", command=valider).pack(pady=20)
        fen.after(100, fen.grab_set)

    def ouvrir_edition_stage(self, stage):
        id_pfmp, periode, statut, e_nom, e_adr, t_nom, t_tel, visite = stage
        
        fen = ctk.CTkToplevel(self)
        fen.title("Modifier le stage")
        fen.geometry("450x650")
        
        ctk.CTkLabel(fen, text="Période :").pack(pady=(10, 0))
        e_periode = ctk.CTkEntry(fen, width=350)
        e_periode.insert(0, periode if periode else "")
        e_periode.pack()
        
        ctk.CTkLabel(fen, text="Statut :").pack(pady=(10, 0))
        e_statut = ctk.CTkOptionMenu(fen, values=["En recherche", "En attente", "Trouvé", "Terminé"], width=350)
        e_statut.set(statut if statut else "En recherche")
        e_statut.pack()
        
        ctk.CTkLabel(fen, text="Entreprise (Nom) :").pack(pady=(10, 0))
        e_enom = ctk.CTkEntry(fen, width=350)
        e_enom.insert(0, e_nom if e_nom else "")
        e_enom.pack()
        
        ctk.CTkLabel(fen, text="Entreprise (Adresse) :").pack(pady=(10, 0))
        e_eadr = ctk.CTkEntry(fen, width=350)
        e_eadr.insert(0, e_adr if e_adr else "")
        e_eadr.pack()
        
        ctk.CTkLabel(fen, text="Tuteur (Nom) :").pack(pady=(10, 0))
        e_tnom = ctk.CTkEntry(fen, width=350)
        e_tnom.insert(0, t_nom if t_nom else "")
        e_tnom.pack()
        
        ctk.CTkLabel(fen, text="Tuteur (Téléphone) :").pack(pady=(10, 0))
        e_ttel = ctk.CTkEntry(fen, width=350)
        e_ttel.insert(0, t_tel if t_tel else "")
        e_ttel.pack()
        
        var_visite = ctk.IntVar(value=visite if visite else 0)
        cb_visite = ctk.CTkCheckBox(fen, text="Visite de stage effectuée", variable=var_visite)
        cb_visite.pack(pady=20)
        
        def valider():
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("""
                    UPDATE Pfmp SET 
                    periode=?, statut_recherche=?, entreprise_nom=?, entreprise_adresse=?, 
                    tuteur_nom=?, tuteur_tel=?, visite_faite=?
                    WHERE id_pfmp=?
                """, (e_periode.get(), e_statut.get(), e_enom.get(), e_eadr.get(), e_tnom.get(), e_ttel.get(), var_visite.get(), id_pfmp))
                conn.commit()
                conn.close()
                fen.destroy()
                self.rafraichir_stages_droite()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                
        ctk.CTkButton(fen, text="Enregistrer les modifications", command=valider).pack(pady=10)
        fen.after(100, fen.grab_set)

    def supprimer_stage(self, id_pfmp):
        if messagebox.askyesno("Confirmation", "Supprimer ce stage ?"):
            try:
                conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
                conn.execute("DELETE FROM Pfmp WHERE id_pfmp = ?", (id_pfmp,))
                conn.commit()
                conn.close()
                self.rafraichir_stages_droite()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    # ==========================================
    # MÉTHODES ORIENTATION
    # ==========================================
    def charger_orientation_liste_eleves(self):
        for widget in self.ori_frame_gauche.winfo_children():
            widget.destroy()
            
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id_eleve, nom, prenom FROM Eleves ORDER BY nom")
            eleves = cursor.fetchall()
            conn.close()
            
            for eleve in eleves:
                id_el, nom, prenom = eleve
                btn = ctk.CTkButton(
                    self.ori_frame_gauche, 
                    text=f"{nom} {prenom}", 
                    fg_color="transparent", 
                    text_color=("black", "white"),
                    hover_color=("gray70", "gray30"),
                    anchor="w",
                    command=lambda i=id_el, n=nom, p=prenom: self.afficher_orientation_eleve(i, n, p)
                )
                btn.pack(fill="x", pady=2, padx=5)
        except Exception as e:
            print("Erreur Orientation:", e)

    def construire_formulaire_orientation(self):
        for widget in self.ori_formulaire.winfo_children():
            widget.destroy()
            
        self.var_choix1 = ctk.StringVar(value="-")
        self.var_choix2 = ctk.StringVar(value="-")
        self.var_choix3 = ctk.StringVar(value="-")
        
        def on_choix_change(choix, entry_widget):
            if choix == "Autre":
                entry_widget.pack(fill="x", pady=(5, 0))
            else:
                entry_widget.pack_forget()

        def creer_bloc_choix(parent, titre, variable):
            cadre = ctk.CTkFrame(parent, fg_color="transparent")
            cadre.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(cadre, text=titre, font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            
            e_autre = ctk.CTkEntry(cadre, placeholder_text="Précisez la filière/le domaine...")
            
            menu = ctk.CTkOptionMenu(cadre, values=["-", "1ère CIEL", "1ère MELEC", "Autre"], variable=variable, command=lambda c: on_choix_change(c, e_autre))
            menu.pack(fill="x", pady=(5, 0))
            
            return e_autre
            
        self.e_autre1 = creer_bloc_choix(self.ori_formulaire, "Vœu n°1 :", self.var_choix1)
        self.e_autre2 = creer_bloc_choix(self.ori_formulaire, "Vœu n°2 :", self.var_choix2)
        self.e_autre3 = creer_bloc_choix(self.ori_formulaire, "Vœu n°3 :", self.var_choix3)
        
        # Remarques
        cadre_notes = ctk.CTkFrame(self.ori_formulaire, fg_color="transparent")
        cadre_notes.pack(fill="both", expand=True, pady=20, padx=20)
        ctk.CTkLabel(cadre_notes, text="Notes d'entretien / Remarques générales :", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.t_notes_ori = ctk.CTkTextbox(cadre_notes, height=150)
        self.t_notes_ori.pack(fill="both", expand=True, pady=(5, 0))
        
        # Bouton Save
        btn_save = ctk.CTkButton(self.ori_formulaire, text="💾 Enregistrer l'orientation", command=self.sauvegarder_orientation, height=40)
        btn_save.pack(pady=20)

    def afficher_orientation_eleve(self, id_eleve, nom, prenom):
        self.ori_eleve_actuel = id_eleve
        self.ori_titre_eleve.configure(text=f"Fiche Orientation de {prenom} {nom}")
        
        self.construire_formulaire_orientation()
        self.ori_formulaire.pack(fill="both", expand=True)
        
        # Charger données
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT voeu_1, voeu_2, detail_reorientation, avis_equipe FROM Orientation WHERE id_eleve = ?", (id_eleve,))
            data = cursor.fetchone()
            conn.close()
            
            def set_choix(val, var, entry_widget):
                if not val or val == "-":
                    var.set("-")
                    entry_widget.pack_forget()
                elif val in ["1ère CIEL", "1ère MELEC"]:
                    var.set(val)
                    entry_widget.pack_forget()
                else:
                    var.set("Autre")
                    entry_widget.delete(0, 'end')
                    entry_widget.insert(0, val)
                    entry_widget.pack(fill="x", pady=(5, 0))
                    
            if data:
                c1, c2, c3, notes = data
                set_choix(c1, self.var_choix1, self.e_autre1)
                set_choix(c2, self.var_choix2, self.e_autre2)
                set_choix(c3, self.var_choix3, self.e_autre3)
                if notes:
                    self.t_notes_ori.insert("1.0", notes)
            else:
                set_choix("-", self.var_choix1, self.e_autre1)
                set_choix("-", self.var_choix2, self.e_autre2)
                set_choix("-", self.var_choix3, self.e_autre3)
                
        except Exception as e:
            print("Erreur chargement orientation:", e)

    def sauvegarder_orientation(self):
        if not self.ori_eleve_actuel:
            return
            
        def get_choix(var, entry_widget):
            val = var.get()
            if val == "Autre":
                return entry_widget.get().strip()
            return val
            
        c1 = get_choix(self.var_choix1, self.e_autre1)
        c2 = get_choix(self.var_choix2, self.e_autre2)
        c3 = get_choix(self.var_choix3, self.e_autre3)
        notes = self.t_notes_ori.get("1.0", "end").strip()
        
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT id_orientation FROM Orientation WHERE id_eleve = ?", (self.ori_eleve_actuel,))
            existe = cursor.fetchone()
            
            if existe:
                cursor.execute("""
                    UPDATE Orientation 
                    SET voeu_1=?, voeu_2=?, detail_reorientation=?, avis_equipe=?
                    WHERE id_eleve=?
                """, (c1, c2, c3, notes, self.ori_eleve_actuel))
            else:
                cursor.execute("""
                    INSERT INTO Orientation (id_eleve, voeu_1, voeu_2, detail_reorientation, avis_equipe)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.ori_eleve_actuel, c1, c2, c3, notes))
                
            conn.commit()
            conn.close()
            messagebox.showinfo("Succès", "Les données d'orientation ont été enregistrées avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # ==========================================
    # MÉTHODES DASHBOARD & EXPORT
    # ==========================================
    def rafraichir_dashboard(self):
        for widget in self.card_suivi.winfo_children(): widget.destroy()
        for widget in self.card_pfmp.winfo_children(): widget.destroy()
        for widget in self.card_ori.winfo_children(): widget.destroy()
        
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            # --- 1. Suivi Journal ---
            cursor.execute("SELECT categorie, COUNT(*) FROM Suivi_Journal WHERE categorie != 'Absence/Retard' GROUP BY categorie")
            stats_suivi = dict(cursor.fetchall())
            
            h_suivi = ctk.CTkFrame(self.card_suivi, fg_color="transparent")
            h_suivi.pack(fill="x", padx=20, pady=15)
            ctk.CTkLabel(h_suivi, text="📊 Journal de Suivi (Alertes)", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
            ctk.CTkButton(h_suivi, text="Voir le classement", font=ctk.CTkFont(weight="bold"), command=self.afficher_details_suivi).pack(side="right")
            
            c_suivi = ctk.CTkFrame(self.card_suivi, fg_color="transparent")
            c_suivi.pack(fill="x", padx=20, pady=(0, 20))
            
            ctk.CTkLabel(c_suivi, text=f"⚠️ Comportement : {stats_suivi.get('Comportement', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#f59e0b").pack(side="left", padx=20)
            ctk.CTkLabel(c_suivi, text=f"📚 Travail : {stats_suivi.get('Travail', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b82f6").pack(side="left", padx=20)
            ctk.CTkLabel(c_suivi, text=f"📌 Autre : {stats_suivi.get('Autre', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="gray").pack(side="left", padx=20)
            
            # --- 2. PFMP ---
            cursor.execute("SELECT COUNT(id_eleve) FROM Eleves")
            tot_eleves = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT id_eleve) FROM Pfmp WHERE statut_recherche IN ('Trouvé', 'Terminé')")
            el_trouve = cursor.fetchone()[0] or 0
            el_non = tot_eleves - el_trouve
            
            h_pfmp = ctk.CTkFrame(self.card_pfmp, fg_color="transparent")
            h_pfmp.pack(fill="x", padx=20, pady=15)
            ctk.CTkLabel(h_pfmp, text="💼 Recherche de Stages (PFMP)", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
            ctk.CTkButton(h_pfmp, text="Voir la liste", font=ctk.CTkFont(weight="bold"), command=self.afficher_details_pfmp).pack(side="right")
            
            c_pfmp = ctk.CTkFrame(self.card_pfmp, fg_color="transparent")
            c_pfmp.pack(fill="x", padx=20, pady=(0, 20))
            
            ctk.CTkLabel(c_pfmp, text=f"✅ {el_trouve} avec un stage", font=ctk.CTkFont(size=18, weight="bold"), text_color="#10b981").pack(side="left", padx=20)
            ctk.CTkLabel(c_pfmp, text=f"❌ {el_non} cherchent encore", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ef4444").pack(side="left", padx=20)
            
            # --- 3. Orientation ---
            cursor.execute("SELECT voeu_1, COUNT(*) FROM Orientation GROUP BY voeu_1")
            stats_ori = dict(cursor.fetchall())
            
            h_ori = ctk.CTkFrame(self.card_ori, fg_color="transparent")
            h_ori.pack(fill="x", padx=20, pady=15)
            ctk.CTkLabel(h_ori, text="🧭 Orientation (Vœux n°1)", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
            ctk.CTkButton(h_ori, text="Détails Orientation", font=ctk.CTkFont(weight="bold"), command=self.afficher_details_ori).pack(side="right")
            
            c_ori = ctk.CTkFrame(self.card_ori, fg_color="transparent")
            c_ori.pack(fill="x", padx=20, pady=(0, 20))
            
            ctk.CTkLabel(c_ori, text=f"💻 CIEL : {stats_ori.get('1ère CIEL', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b82f6").pack(side="left", padx=20)
            ctk.CTkLabel(c_ori, text=f"⚡ MELEC : {stats_ori.get('1ère MELEC', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#eab308").pack(side="left", padx=20)
            ctk.CTkLabel(c_ori, text=f"🔄 Autre : {stats_ori.get('Autre', 0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color="gray").pack(side="left", padx=20)
            
            conn.close()
        except Exception as e:
            print("Erreur refresh dashboard:", e)

    def afficher_details_suivi(self):
        for w in self.pages["details_suivi"].winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.pages["details_suivi"], fg_color="transparent")
        h.pack(fill="x", pady=20, padx=20)
        ctk.CTkButton(h, text="⬅ Retour", width=80, fg_color="gray", command=lambda: self.afficher_page("dashboard")).pack(side="left")
        ctk.CTkLabel(h, text="Classement : Journal de Suivi", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)
        
        g = ctk.CTkFrame(self.pages["details_suivi"], fg_color="transparent")
        g.pack(fill="both", expand=True, padx=20, pady=10)
        g.columnconfigure((0,1,2), weight=1)
        
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            def c_col(titre, cat, col):
                f = ctk.CTkScrollableFrame(g, corner_radius=10)
                f.grid(row=0, column=col, sticky="nsew", padx=5)
                ctk.CTkLabel(f, text=titre, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
                cursor.execute("""
                    SELECT Eleves.nom, Eleves.prenom, COUNT(Suivi_Journal.id_note) as nb
                    FROM Eleves JOIN Suivi_Journal ON Eleves.id_eleve = Suivi_Journal.id_eleve
                    WHERE Suivi_Journal.categorie = ? GROUP BY Eleves.id_eleve ORDER BY nb DESC
                """, (cat,))
                res = cursor.fetchall()
                if not res: ctk.CTkLabel(f, text="Aucune note.", text_color="gray").pack()
                for nom, p, nb in res: ctk.CTkLabel(f, text=f"{nom} {p} : {nb} note(s)").pack(anchor="w", padx=10, pady=2)
                    
            c_col("⚠️ Comportement", "Comportement", 0)
            c_col("📚 Travail", "Travail", 1)
            c_col("📌 Autre", "Autre", 2)
            conn.close()
        except Exception as e: print("Err details suivi:", e)
        self.afficher_page("details_suivi")

    def afficher_details_pfmp(self):
        for w in self.pages["details_pfmp"].winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.pages["details_pfmp"], fg_color="transparent")
        h.pack(fill="x", pady=20, padx=20)
        ctk.CTkButton(h, text="⬅ Retour", width=80, fg_color="gray", command=lambda: self.afficher_page("dashboard")).pack(side="left")
        ctk.CTkLabel(h, text="Détails : Recherche de Stages", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)
        
        g = ctk.CTkFrame(self.pages["details_pfmp"], fg_color="transparent")
        g.pack(fill="both", expand=True, padx=20, pady=10)
        g.columnconfigure((0,1), weight=1)
        
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT Eleves.nom, Eleves.prenom FROM Eleves JOIN Pfmp ON Eleves.id_eleve = Pfmp.id_eleve WHERE Pfmp.statut_recherche IN ('Trouvé', 'Terminé') ORDER BY Eleves.nom")
            trv = cursor.fetchall()
            cursor.execute("SELECT nom, prenom FROM Eleves ORDER BY nom")
            ts = cursor.fetchall()
            ntrv = [e for e in ts if e not in trv]
            
            f1 = ctk.CTkScrollableFrame(g, corner_radius=10, border_width=2, border_color="#10b981")
            f1.grid(row=0, column=0, sticky="nsew", padx=10)
            ctk.CTkLabel(f1, text="✅ Ont un stage", text_color="#10b981", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            for n, p in trv: ctk.CTkLabel(f1, text=f"{n} {p}").pack(anchor="w", padx=20, pady=2)
            
            f2 = ctk.CTkScrollableFrame(g, corner_radius=10, border_width=2, border_color="#ef4444")
            f2.grid(row=0, column=1, sticky="nsew", padx=10)
            ctk.CTkLabel(f2, text="❌ Cherchent encore", text_color="#ef4444", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            for n, p in ntrv: ctk.CTkLabel(f2, text=f"{n} {p}").pack(anchor="w", padx=20, pady=2)
            conn.close()
        except Exception as e: print("Err details pfmp:", e)
        self.afficher_page("details_pfmp")

    def afficher_details_ori(self):
        for w in self.pages["details_ori"].winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.pages["details_ori"], fg_color="transparent")
        h.pack(fill="x", pady=20, padx=20)
        ctk.CTkButton(h, text="⬅ Retour", width=80, fg_color="gray", command=lambda: self.afficher_page("dashboard")).pack(side="left")
        ctk.CTkLabel(h, text="Détails : Orientation", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)
        
        g = ctk.CTkFrame(self.pages["details_ori"], fg_color="transparent")
        g.pack(fill="both", expand=True, padx=20, pady=10)
        g.columnconfigure((0,1,2), weight=1)
        
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            def c_col_o(titre, v, col, a=False):
                f = ctk.CTkScrollableFrame(g, corner_radius=10)
                f.grid(row=0, column=col, sticky="nsew", padx=5)
                ctk.CTkLabel(f, text=titre, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
                if a:
                    cursor.execute("SELECT Eleves.nom, Eleves.prenom, Orientation.detail_reorientation FROM Eleves JOIN Orientation ON Eleves.id_eleve = Orientation.id_eleve WHERE Orientation.voeu_1 = 'Autre' ORDER BY Eleves.nom")
                    for n, p, d in cursor.fetchall(): ctk.CTkLabel(f, text=f"• {n} {p} -> {d or '?'}").pack(anchor="w", padx=10, pady=2)
                else:
                    cursor.execute("SELECT Eleves.nom, Eleves.prenom FROM Eleves JOIN Orientation ON Eleves.id_eleve = Orientation.id_eleve WHERE Orientation.voeu_1 = ? ORDER BY Eleves.nom", (v,))
                    for n, p in cursor.fetchall(): ctk.CTkLabel(f, text=f"• {n} {p}").pack(anchor="w", padx=10, pady=2)
            c_col_o("💻 1ère CIEL", "1ère CIEL", 0)
            c_col_o("⚡ 1ère MELEC", "1ère MELEC", 1)
            c_col_o("🔄 Autre", "Autre", 2, True)
            conn.close()
        except Exception as e: print("Err details ori:", e)
        self.afficher_page("details_ori")

    def exporter_pdf_dashboard(self):
        try:
            from fpdf import FPDF
            import datetime
            
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            cursor.execute("SELECT categorie, COUNT(*) FROM Suivi_Journal WHERE categorie != 'Absence/Retard' GROUP BY categorie")
            s_suivi = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(id_eleve) FROM Eleves")
            t_el = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT id_eleve) FROM Pfmp WHERE statut_recherche IN ('Trouvé', 'Terminé')")
            t_pfmp = cursor.fetchone()[0] or 0
            nt_pfmp = t_el - t_pfmp
            
            cursor.execute("SELECT voeu_1, COUNT(*) FROM Orientation GROUP BY voeu_1")
            s_ori = dict(cursor.fetchall())
            conn.close()
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("helvetica", "B", 22)
            pdf.cell(0, 20, "OpenSuivi - Rapport de la Classe", align="C", new_x="LMARGIN", new_y="NEXT")
            
            date_str = datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
            pdf.set_font("helvetica", "I", 12)
            pdf.cell(0, 10, f"Edite le {date_str}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            
            pdf.set_font("helvetica", "B", 16)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(0, 10, " 1. Notes de Comportement / Travail", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"   - Avertissements Comportement : {s_suivi.get('Comportement', 0)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"   - Remarques Travail : {s_suivi.get('Travail', 0)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"   - Autre : {s_suivi.get('Autre', 0)}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, " 2. Recherches de Stages (PFMP)", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"   - Eleves ayant trouve un stage : {t_pfmp}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"   - Eleves sans stage : {nt_pfmp}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, " 3. Voeux d'Orientation (Choix n 1)", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"   - Filiere 1ere CIEL : {s_ori.get('1ère CIEL', 0)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"   - Filiere 1ere MELEC : {s_ori.get('1ère MELEC', 0)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"   - Autre voie / Reorientation : {s_ori.get('Autre', 0)}", new_x="LMARGIN", new_y="NEXT")
            
            os.makedirs("exports", exist_ok=True)
            nom_fichier = os.path.join("exports", f"Rapport_Classe_{int(datetime.datetime.now().timestamp())}.pdf")
            pdf.output(nom_fichier)
            
        except ImportError:
            messagebox.showerror("Erreur", "La bibliotheque fpdf2 n'est pas installee. L'export PDF est impossible.")
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))

    # ==========================================
    # MÉTHODES BILAN INDIVIDUEL (ÉLÈVE)
    # ==========================================
    def charger_bilan_eleve(self, id_eleve, parent_frame):
        try:
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            # --- 1. Orientation ---
            ctk.CTkLabel(parent_frame, text="🧭 Orientation", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(10, 5))
            f_ori = ctk.CTkFrame(parent_frame, corner_radius=10)
            f_ori.pack(fill="x", padx=10, pady=5)
            
            cursor.execute("SELECT voeu_1, voeu_2 FROM Orientation WHERE id_eleve = ?", (id_eleve,))
            ori = cursor.fetchone()
            if ori:
                v1, v2 = ori
                ctk.CTkLabel(f_ori, text=f"• Vœu 1 : {v1 or 'Non défini'}").pack(anchor="w", padx=10, pady=2)
                ctk.CTkLabel(f_ori, text=f"• Vœu 2 : {v2 or 'Non défini'}").pack(anchor="w", padx=10, pady=2)
            else:
                ctk.CTkLabel(f_ori, text="Aucune donnée d'orientation.").pack(anchor="w", padx=10, pady=5)
                
            # --- 2. PFMP ---
            ctk.CTkLabel(parent_frame, text="💼 Stages (PFMP)", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(20, 5))
            f_pfmp = ctk.CTkFrame(parent_frame, corner_radius=10)
            f_pfmp.pack(fill="x", padx=10, pady=5)
            
            cursor.execute("SELECT periode, statut_recherche, entreprise_nom FROM Pfmp WHERE id_eleve = ?", (id_eleve,))
            stages = cursor.fetchall()
            if stages:
                for p, s, e in stages:
                    ctk.CTkLabel(f_pfmp, text=f"• {p} : {s} - {e or 'Entreprise inconnue'}").pack(anchor="w", padx=10, pady=2)
            else:
                ctk.CTkLabel(f_pfmp, text="Aucun stage enregistré.").pack(anchor="w", padx=10, pady=5)
                
            # --- 3. Journal de Suivi ---
            ctk.CTkLabel(parent_frame, text="📊 Journal de Suivi", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(20, 5))
            
            cursor.execute("SELECT date_note, categorie, contenu FROM Suivi_Journal WHERE id_eleve = ? ORDER BY date_note DESC", (id_eleve,))
            notes = cursor.fetchall()
            if notes:
                for d, c, t in notes:
                    f_note = ctk.CTkFrame(parent_frame, corner_radius=10)
                    f_note.pack(fill="x", padx=10, pady=5)
                    ctk.CTkLabel(f_note, text=f"[{d}] {c}", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
                    ctk.CTkLabel(f_note, text=t, justify="left", wraplength=500).pack(anchor="w", padx=10, pady=(0, 10))
            else:
                f_note = ctk.CTkFrame(parent_frame, corner_radius=10)
                f_note.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(f_note, text="Aucune note dans le journal.").pack(anchor="w", padx=10, pady=5)
                
            conn.close()
        except Exception as e:
            print("Erreur bilan:", e)

    def exporter_bilan_pdf(self, id_eleve, nom, prenom):
        try:
            from fpdf import FPDF
            import datetime
            import os
            
            def sanitize(text):
                if not text: return ""
                return str(text).replace("œ", "oe").replace("Œ", "Oe")
            
            conn = sqlite3.connect(os.path.join("data", "openn_suivi.db"))
            cursor = conn.cursor()
            
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("helvetica", "B", 24)
            pdf.cell(0, 20, sanitize(f"Bilan Individuel - {nom} {prenom}"), align="C", new_x="LMARGIN", new_y="NEXT")
            
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            pdf.set_font("helvetica", "I", 12)
            pdf.cell(0, 10, sanitize(f"Édité le {date_str}"), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            
            # 1. Orientation
            pdf.set_font("helvetica", "B", 18)
            pdf.set_fill_color(230, 230, 250)
            pdf.cell(0, 10, " 1. Orientation", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            cursor.execute("SELECT voeu_1, voeu_2 FROM Orientation WHERE id_eleve = ?", (id_eleve,))
            ori = cursor.fetchone()
            if ori:
                pdf.cell(0, 8, sanitize(f"   - Voeu 1 : {ori[0] or 'Non défini'}"), new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 8, sanitize(f"   - Voeu 2 : {ori[1] or 'Non défini'}"), new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 8, "   - Aucune donnée d'orientation enregistrée.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            # 2. PFMP
            pdf.set_font("helvetica", "B", 18)
            pdf.set_fill_color(220, 240, 220)
            pdf.cell(0, 10, " 2. Stages (PFMP)", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            cursor.execute("SELECT periode, statut_recherche, entreprise_nom FROM Pfmp WHERE id_eleve = ?", (id_eleve,))
            stages = cursor.fetchall()
            if stages:
                for p, s, e in stages:
                    pdf.cell(0, 8, sanitize(f"   - Période : {p}"), new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 8, sanitize(f"     Statut : {s} | Entreprise : {e or 'Non définie'}"), new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 8, "   - Aucun stage enregistré.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            # 3. Journal
            pdf.set_font("helvetica", "B", 18)
            pdf.set_fill_color(250, 230, 230)
            pdf.cell(0, 10, " 3. Journal de Suivi", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            cursor.execute("SELECT date_note, categorie, contenu FROM Suivi_Journal WHERE id_eleve = ? ORDER BY date_note DESC", (id_eleve,))
            notes = cursor.fetchall()
            if notes:
                for d, c, t in notes:
                    if c == "Comportement":
                        pdf.set_text_color(220, 38, 38) # Rouge
                    elif c == "Travail":
                        pdf.set_text_color(37, 99, 235) # Bleu
                    elif c == "Absence/Retard":
                        pdf.set_text_color(217, 119, 6) # Orange
                    else:
                        pdf.set_text_color(100, 100, 100) # Gris
                        
                    pdf.set_font("helvetica", "B", 12)
                    pdf.cell(0, 8, sanitize(f"   [{d}] {c} :"), new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_text_color(0, 0, 0) # Retour au noir pour le texte
                    pdf.set_font("helvetica", "", 12)
                    pdf.multi_cell(0, 8, sanitize(f"     {t}"), new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 8, "   - Aucune note dans le journal.", new_x="LMARGIN", new_y="NEXT")
            
            conn.close()
            
            os.makedirs("exports", exist_ok=True)
            fichier_pdf = os.path.join("exports", f"Bilan_{nom}_{prenom}.pdf")
            pdf.output(fichier_pdf)
            
        except ImportError:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Erreur", "La bibliothèque fpdf2 n'est pas installée.")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Erreur PDF", f"Erreur : {e}")

if __name__ == "__main__":
    app = OpenSuiviApp()
    app.mainloop()