import streamlit as st
from streamlit_authenticator import Authenticate
from streamlit_option_menu import option_menu
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import requests
import json
import urllib.parse
import joblib
from datetime import datetime
from bs4 import BeautifulSoup 
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt 
import os 












# configuration de la page web streamlit 
st.set_page_config(page_title="Netflox", layout="wide")









# CHARGEMENT DES COMPTES UTILISATEURS

# On charge les comptes via un dataframe
compte = pd.read_parquet("F:\projet2\identification")

# on creer un dictionnaire dans lequel on vient mettre les données du dataframe 
credentials = {
    # Transforme la colonne "username" en index du DataFrame
    # "usernames":      Enveloppe le tout dans la clé "usernames" qui est exactement ce qu'attend streamlit_authenticator
    "usernames": compte.set_index("username")[
        # Garde uniquement ces colonnes, ignore les autres
        ["name", "password", "email", "failed_login_attemps", "logged_in", "role"]
    # Convertit en dictionnaire où chaque index (username) devient une clé avec ses colonnes comme sous-dictionnaire
    ].to_dict(orient="index")
}

# C'est un "moule" qui crée un objet avec des fonctionnalités prêtes à l'emploi. Ici Authenticate te fournit automatiquement :
# .login()            Affiche le formulaire de connexion
# .logout()           Déconnecte l'utilisateur
# .register_user()    Inscrit un nouvel utilisateur
# .reset_password()   Réinitialise un mot de passe
authenticator = Authenticate(
    # Dictionnaire contenant tous les utilisateurs et leurs infos (nom, mdp, email...)
    credentials,
    # Nom du cookie stocké dans le navigateur pour mémoriser la session
    "cookie_name",
    # Clé secrète utilisée pour chiffrer/signer le cookie (à garder privée !)
    "cookie_key",
    # Durée de vie du cookie en jours (ici 30 jours avant déconnexion automatique)
    0,
)












# PAGE DE CONNEXION (si non connecté)

# Vérifie si l'utilisateur N'est PAS connecté
# session_state stocke les variables qui persistent entre les rechargements de la page
if not st.session_state.get("authentication_status"):

    # Injecte du CSS personnalisé pour centrer et limiter la largeur du formulaire
    # max-width: 400px → formulaire étroit comme une vraie page de login
    # margin: auto → centré horizontalement
    # padding-top: 100px → descend le formulaire vers le milieu de l'écran
    st.markdown("""
        <style>
        .block-container { max-width: 400px; margin: auto; padding-top: 100px; }
        </style>
    """, unsafe_allow_html=True)

    # Affiche le titre principal de l'application
    st.title("🎬 NETFLOX")
    # Affiche un sous-titre en dessous du titre
    st.subheader("Connexion")
    # Affiche le formulaire de connexion (champs username + password)
    # location='main' → le formulaire s'affiche dans la page principale (pas dans la sidebar)
    authenticator.login(location='main')

    # Cas 1 : L'utilisateur a soumis le formulaire mais les identifiants sont mauvais
    if st.session_state.get("authentication_status") is False:
        st.error("Nom d'utilisateur ou mot de passe incorrect")

    # Cas 2 : La page vient de charger, l'utilisateur n'a encore rien saisi
    elif st.session_state.get("authentication_status") is None:
        st.warning("Veuillez entrer vos identifiants")

    # Bloque l'exécution du reste du code tant que l'utilisateur n'est pas connecté
    # Sans ce st.stop(), le contenu de l'application s'afficherait quand même en dessous
    st.stop()












# CONFIGURATION DE LA SIDEBAR ET DU HEADERS EN DEBUT DE SITE 

# dictionnaire d'authentification pour les requètes api 
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept-Language": "fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "application/json",
}



# CSS sidebar pour la couleur du fond et des lettres ainsi que l'espacement des lettres 
# première partie pour la couleur de la sidebar et deuxieme pour la couleur des lettres 
st.markdown("""
    <style>              
    [data-testid="stSidebar"] {
        background-color: #C8861A;
    }
    [data-testid="stSidebar"] * {
        letter-spacing: 2px;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)





# configuration de la sidebar et on donne le titre 
st.sidebar.title("NETFLOX")

# on creer le menu dans la sidebar avec streamlite option menu 
with st.sidebar:
    # on vient nommer les paties dans la variable page pour ensuite les selectionner et afficher du contenu
    page = option_menu(
        # pas de titre juste les boutons 
        menu_title= None,
        # on définis les boutons 
        options= ["Accueil", "Recommandation", "Ma liste", "Statistiques", "Données"],
        # on definis des icons 
        icons= ["house", "film", "bookmark", "bar-chart", "database"],
        # on vient modifié le style et la couleur de fond avec du CSS
        styles={
            "container":         {"background-color": "#C8861A"},
            "nav-link":          {"color": "black", "letter-spacing": "1px"},
            "nav-link-selected": {"background-color": "#a06b10", "color": "black"},
        }
    )

    # Sous-menus selon la page sélectionnée avec les icons 
    sous_sections = {
        "Accueil": {
            "options": ["Accueil", "Equipe"],
            "icons":   ["house", "house"]
        },
        "Recommandation": {
            "options": ["Films", "Séries"],
            "icons":   ["film", "tv"]
        },
        "Ma liste": {
            "options": ["Films", "Séries"],
            "icons":   ["film", "tv"]
        },
        "Statistiques": {
            "options": ["Général", "Films", "Séries", "Creuse", "Réalisateurs"],
            "icons":   ["graph-up", "film", "tv", "geo-alt", "person-video"]
        },
        "Données": {
            "options": ["Films", "Séries", "Creuse"],
            "icons":   ["film", "tv", "geo-alt"]
        },
    }

    # Affiche le sous-menu uniquement si la page en a un
    if page in sous_sections:
        # on vient creer une divisions pour les sous pages 
        st.sidebar.divider()
        # on vient nommer les paties dans la variable sous page pour ensuite les selectionner et afficher du contenu
        sous_page = option_menu(
            # pas de titre juste les boutons
            menu_title= None,
            # on définis les boutons 
            options=sous_sections[page]["options"],
            # on definis des icons 
            icons=sous_sections[page]["icons"],
            # on vient modifié le style et la couleur de fond avec du CSS
            styles={
                "container":         {"background-color": "#C8861A"},
                "menu-title":        {"color": "black", "font-size": "13px"},
                "nav-link":          {"color": "black", "font-size": "13px"},
                "nav-link-selected": {"background-color": "#a06b10"},
            }
        )
    # si pas de sous section on dit qu'iln'affiche rien 
    else:
        sous_page = None




# on vient creer une divisions pour le bouton de deconnexion 
st.sidebar.divider()
# on affichue le nom de l'utilisateurs
st.sidebar.markdown(f"👤 {st.session_state['name']}")
# on creer le boutons de deconnexion 
authenticator.logout("Déconnexion", location="sidebar")
# on vient creer une divisions pour le bouton de deconnexion 
st.sidebar.divider()




# Date et heure en bas de sidebar
maintenant = datetime.now()
st.sidebar.markdown(
    f"""
    <style>
    .date-heure {{
        position: fixed;
        bottom: 20px;
        left: 15px;
        font-size: 13px;
        color: black;
        letter-spacing: 1px;
        z-index: 9999;
    }}
    </style>
    <div class="date-heure">📅 {maintenant.strftime("%d/%m/%Y")}<br>🕐 {maintenant.strftime("%H:%M")}</div>
    """,
    unsafe_allow_html=True
)











# PAGE D ACCEUIL PARTIE ACCEUIL 

# si le bouton page égale aceuille alors 
if page == "Accueil" and sous_page == "Accueil":
    # titre de la page 
    st.title("NETFLOX")
    # sous titre 
    st.subheader("Actualités :")
    # on creer un objet container dans lequel on vient creer 4 colonnes 
    with st.container(horizontal_alignment="center", vertical_alignment="top", border=True):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], vertical_alignment = "center")
        # on défini se qu'il y a dans chaque colonnes 
        with col1:
            st.badge("les news de la semaine", color="red")

        with col1:
            st.image("https://www.eklecty-city.fr/wp-content/uploads/2026/06/fall-2-deadpoint-696x391.jpg")
            st.text("Fall 2 : Deadpoint dévoile sa bande-annonce")
        
        with col2:
            st.space('large')
            st.image("https://www.eklecty-city.fr/wp-content/uploads/2026/06/age-de-glace-le-reveil-du-volcan-696x353.jpg")
            st.text("L Âge de Glace: Le Réveil du Volcan dévoile sa bande-annonce")
        
        with col3:
            st.space('xsmall')
            st.image("https://www.eklecty-city.fr/wp-content/uploads/2025/12/supergirl-woman-of-tomorrow-2026-movie-picture-02-696x391.jpg")
            st.text("Supergirl dévoile sa nouvelle bande-annonce")
        
        with col4:
            st.space('xsmall')
            st.image("https://www.eklecty-city.fr/wp-content/uploads/2022/11/streets-of-rage-696x391.jpg")
            st.text("Streets of Rage: adaptation du jeu Sega !")
    # on mets un espace entre le containers et la section suivante 
    st.space('medium')
    # sous titre de partie
    st.subheader("Les films les plus populaires")
    # on mets un espace 
    st.space('xsmall')
    # on définis 5 colonnes pour la partie populaires 
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1], vertical_alignment = "center")
    # on mets des affiches de films et les titres dans chaques colonnes 
    with col1:
        st.image("https://media.senscritique.com/media/000004710747/300/inception.jpg")
        st.text("Inception")
        
    with col2:
        st.image("https://media.senscritique.com/media/000020072264/300/le_parrain.jpg")
        st.text("Le Parrain")
        
    with col3:
        st.image("https://media.senscritique.com/media/000022091644/300/forrest_gump.png")
        st.text("Forrest Gump")
        
    with col4:
        #st.space('xsmall')
        st.image("https://media.senscritique.com/media/000022933408/300/the_dark_knight_le_chevalier_noir.png")
        st.text("The Dark Knight - Le Chevalier noir")
    
    with col5:
        st.image("https://media.senscritique.com/media/000004699879/300/le_prestige.jpg")
        st.text("Le Prestige")

    # on mets un espace entre la section et le sous titre 
    st.space('medium')
    # sous titre de partie
    st.subheader("Les recomandations de l'équipe")
    # on mets un espace 
    st.space('xsmall')
    # on définis 5 colonnes 
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1], vertical_alignment = "center")
    # on mets des affiches de films et les titres dans chaques colonnes 
    with col1:
        st.image("https://fr.web.img4.acsta.net/pictures/210/552/21055250_20131106114016251.jpg")
        st.text("Le Hobbit: La désolation de Smaug")
        
    with col2:
        st.image("https://fr.web.img6.acsta.net/c_310_420/pictures/210/081/21008110_20130524125237634.jpg")
        st.text("Man of Steel")
        
    with col3:
        st.image("https://fr.web.img2.acsta.net/pictures/18/07/02/17/25/3643090.jpg")
        st.text("Harry Potter a l'ecole des sorcier")
        
    with col4:
        #st.space('xsmall')
        st.image("https://m.media-amazon.com/images/M/MV5BYTViYTE3ZGQtNDBlMC00ZTAyLTkyODMtZGRiZDg0MjA2YThkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg")
        st.text("Pulp Fiction")
    
    with col5:
        st.image("https://m.media-amazon.com/images/I/91vIHsL-zjL._AC_UF1000,1000_QL80_.jpg")
        st.text("Interstellar")











# PAGE D ACCEUIL PARTIE EQUIPE 

if page == "Accueil" and sous_page == "Equipe":
    # espace 
    st.space(size = "small")
    st.title("Bienvenue sur Netflox !", text_alignment = "center")

    # on creer des colonnes 
    col1, col2, col3 = st.columns([1, 4, 1])
    
    # on dit que dans la colonne 2 (qui represente une échelle de 4 sur 6) on mets l'image 
    with col2:
        st.image("F:/projet2/Netflox.png")
    # espace entre l'image et la description
    st.space(size = "small")

    # text avec html pour modifié la taille de la police 
    # unsafe_allow_html=True nous permet de mettre du text html
    st.markdown("""
        <p style='font-size:25px;'>
        Ce site a pour objectif de recommander des films et des séries aux utilisateurs 
        en fonction de leurs dernières visualisations.\n
        <p style='font-size:25px;'>
        Ce projet a été réalisé pour permettre une recommandation efficace.
        </p>
    """, unsafe_allow_html=True, text_alignment = "center")
    # espace entre la description et le sous titre
    st.space(size = "medium")



    # deuxime partie avec titre et text 
    st.subheader("Equipe", text_alignment = "center")

    # on mets en gras avec <b>exemple</b> et on passe à la ligne avec \n
    # on augmente la taille de la police avec <p style='font-size:20px;'>
    st.markdown("""
                <p style='font-size:20px;'>
                Pour la réalisation de ce projet nous avons éffectué différentes taches : \n
    <p style='font-size:20px;'>
    la Première partie à été réalisé par <b>Daniele</b> pour l'analyse et la recommandation des films \n
    <p style='font-size:20px;'>
    la Deuxieme partie à été réalisé par <b>Luck</b> pour l'analyse et la recommandation des séries \n
    <p style='font-size:20px;'>
    la Troisieme partie à été réalisé par <b>Nazir</b> pour l'analyse des acteurs et réalisateur \n
    <p style='font-size:20px;'>
    la Quatrieme partie à été rélisé par <b>Lissandru</b> pour l'analyse des données de la creuse
                </p>
                """
                ,unsafe_allow_html=True, text_alignment = "center")
    st.space(size = "small")


    #on mets l'image 
    # on creer des colonnes 
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # on dit que dans la colonne 2 (qui represente une échelle de 4 sur 6) on mets l'image 
    with col2:
        # on affiche une image dans la page acceuille 
        st.image("F:\projet2\Image1.png")
# fin de la page d'acceuille 















# PAGE FILMS RECOMMANDATIONS 

# Nouvelle page pour les Films et le systeme de recommandation  #fonction selcelect
elif page == "Recommandation" and sous_page == "Films":

    st.space(size = "small")
    # on mets le nom de la page 
    st.subheader("Recommandation de Films :")
    st.space(size = "small")
    # on vient creer un cache dat pour load le dataframe une seule fois 
    @st.cache_data
    #on vient faire une fonction de loadage 
    def load_data():
    # definition de data frame 
        #df = pd.read_csv("F:/projet2/recommandationfilmfinal.csv")
        # .parquet = .csv comprésser
        df = pd.read_parquet("F:/projet2/recommandationfilmfinal.parquet")
        return df
    # on vient recupérer le df loadé 
    df = load_data()
    # on definis la colonne titre du df dans la variable movie_name
    movie_name = "titre"
    # on definis la colonne director_name du df dans la variable realisateur
    realisateur = "director_name"
    # on défini 2 colonnes pour les selectbox
    col1, col2 = st.columns([1, 1], vertical_alignment = "center")
    # dans la colonnes 1 on vient choisir le nom du film
    with col1:
        # on laisse le choix à l'utilisateur de choisir un films ou non  
        choix = st.selectbox(
        "Choisi un film et je te proposerai des recommandation qui te plairont 🎥",
        df[movie_name], None)

    # dans la colonnes 2 on vient choisir le nom du realisateur 
    with col2:
        # on laisse le choix à l'utilisateur de choisir un realisateur ou non 
        choix2 = st.selectbox(
        "Choisi un realisateur et je te proposerai des recommandation qui te plairont 🎬",
        df[realisateur], None)
     
    # on mets un espace entre les selections et l'image 
    st.space(size = "small")
    # on vient dire que si un des 2 choix a été selectionné alors on fait le recco
    if choix != None or choix2 != None:
        # on prgramme 3 colonnes pour centrer l'image 
        col1, col2, col3 = st.columns([1, 1, 1])

        # si films selectionné alors 
        if choix != None:
            # si films selectionné alors numero de la ligne = index du choix 
            numeroDelaLigne = df[df[movie_name] == choix].index[0]
            # on affiche l'affiche du films selectionné 
            try:
                # on vient encoder le films dans la version que l'api comprend
                titre_encode = urllib.parse.quote(choix)
                # on vient demander a l'api omdb le lien du poster 
                #infosDuFilm = json.loads(requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}").text)
                request = requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}", headers = headers)
                infosDuFilm = json.loads(request.text)
                image = infosDuFilm.get("Poster", None)

                # on mets l'image dans la colonne 2 
                with col2:
                    # si l'api renvoi pas de reponse 
                    if image == "N/A" or image is None or image == 0 or requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}").status_code == 404 or infosDuFilm.get(request) == "False" or infosDuFilm.get(request) == "N/A":
                        st.write("Ton choix :")
                        # on affiche l'image de secours 
                        st.image("F:/projet2/pasaffiche.png")
                        st.write(choix)

                    else:
                        # affichage du choix
                        st.write("Ton choix :")
                        # on affiche l'image 
                        st.image(image)
                        st.write(choix)

            # si pas d'affiche alors on affiche cette image  
            except:
                with col2:
                    st.image("F:/projet2/pasaffiche.png")



        # si pas de films selectionné alors numero de la ligne = premier films du réalisateur 
        elif choix2 != None:
            # affichage du choix
            st.write("Ton choix :", choix2)
            numeroDelaLigne = df[df[realisateur] == choix2].index[0]
        

    
        # on mets un espace entre l'image  et les recommandations 
        st.space(size = "medium")
        
        # on choisit cet algorithme parce qu'on veut faire des recommendations (clustering)
        # son fonctionement est de rechercher les plus proche voisin par calcul de l'angle (ce qui ressemble plus) de notre cible 
        nn = NearestNeighbors(n_neighbors=6, metric="cosine")

        # on défini les colonnes X en retirant movie name et relisateur 
        # équivalent de : X = df.drop(["movie_name", "realisateur"], axis=1)
        X = df.drop(columns=[movie_name, realisateur])
        # on définis la cible de notre algorithme 
        y = df[movie_name] 
        
        # on entraine la modèle mais Clustering, donc pas de y
        # joblib module permettant de scoket un algo ml dans un fichier pour le loads une seule fois 
        nn = joblib.load("F:/projet2/site_projet2/recommandation.joblib") 

        # Ça sélectionne le vecteur de features du film choisi, qui sera ensuite comparé aux autres pour trouver les films du même cluster.
        # On récupère le profil du film choisi (ses genres, type, etc.)
        featuresAPredire = X.iloc[numeroDelaLigne, :]
        # On cherche les N films les plus proches dans l'espace des features
        distances, index = nn.kneighbors([featuresAPredire])
        # On récupère les titres des films voisins grâce à leurs index
        listeDesRecommandations = df[movie_name][index[0]]
        # sous titre pour présenter les recommandations 
        st.subheader("les films recommander selon ta selection sont :")
        # on mets un espace 
        st.space("small")
        # on definis le nombre de colonnes en fonction du nombre de recommandation de films 
        cols = st.columns(len(listeDesRecommandations.values[1:]))
        # on boucle sur chaque colonne et sur chaque films recommander 
        # zip(cols, films) associe chaque film à sa colonne
        for col, cfilms in zip(cols, listeDesRecommandations.values[1:]):
            # with col: place le films dans la colonne associé 
            # dans la colonne i on affiche le code si dessous donc l'affiche 
            with col:
                try:
                    # on vient encoder le films dans la version que l'api comprend
                    titre_encode2 = urllib.parse.quote(cfilms)
                    # On demande à l'API OMDB le lien du poster
                    #infosDuFilm = json.loads(requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode2}").text)
                    request = requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode2}", headers = headers)
                    infosDuFilm = json.loads(request.text)
                    image = infosDuFilm.get("Poster", None)

                    # OMDB retourne "N/A" quand il n'y a pas de poster
                    if image == "N/A" or image is None or image == 0 or requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}").status_code == 404 or infosDuFilm.get(request) == "False" or infosDuFilm.get(request) == "N/A":
                        # on affiche l'image de secours 
                        st.image("F:/projet2/pasaffiche.png")
                    else :
                        # On affiche l'image en dessous
                        st.image(image)
                    # On affiche le titre
                    st.caption(cfilms)

                except:
                    #si pas d'affiche on affiche :
                    st.image("F:/projet2/pasaffiche.png")
                    st.caption(cfilms)
    # si aucune selection choisit on creer des colonnes (3)
    else:
        # on défini la taille des colonnes 
        col1, col2, col3 = st.columns([1, 2, 1])
        # dans la colonnes 2 on vient mettre l'affiche de secours 
        with col2:
            st.badge("Vous n'avez choisit ni réalisateurs, ni films", color="red")
            st.space(size = "small")
            st.image("F:/projet2/pasaffiche.png")












# PAGE FILMS RECOMMANDATIONS 

elif page == "Recommandation" and sous_page == "Séries":
    # on vient mettre le titre 
    st.space(size = "small")
    st.subheader("Recommandation de séries")
    st.space(size = "small")
    # on vient creer un cache dat pour load le dataframe une seule fois 
    @st.cache_data
    def load_data():
    # definition de data frame 
        df = pd.read_parquet("F:/projet2/recommandationsériesfinal.parquet")
        return df
    df = load_data()
    # on definis la colonne titre du df dans la variable movie_name
    series_name = "titre"
    # on definis la colonne director_name du df dans la variable realisateur
    realisateur = "director_name"
    
    col1, col2 = st.columns([1, 1], vertical_alignment = "center")

    with col1:
        # on laisse le choix à l'utilisateur de choisir un films ou non  
        choix = st.selectbox(
        "Choisi un film et je te proposerai des recommandation qui te plairont 🎥",
        df[series_name], None)

   
    with col2:
        # on laisse le choix à l'utilisateur de choisir un realisateur ou non 
        choix2 = st.selectbox(
        "Choisi un realisateur et je te proposerai des recommandation qui te plairont 🎬",
        df[realisateur], None)

    # on mets un espace entre les selections et l'image 
    st.space(size = "small")

    
    if choix != None or choix2 != None:
        # on prgramme 3 colonnes pour centrer l'image 
        col1, col2, col3 = st.columns([1, 1, 1])

        # si films selectionné alors 
        if choix != None:
            # si films selectionné alors numero de la ligne = index du choix 
            numeroDelaLigne = df[df[series_name] == choix].index[0]
            # on affiche l'affiche du films selectionné 
            try:
                # on vient encoder le films dans la version que l'api comprend
                titre_encode = urllib.parse.quote(choix)
                # on vient demander a l'api omdb le lien du poster 
                infosDuFilm = json.loads(requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}&type=series", headers = headers).text)
                #image = infosDuFilm["Poster"]
                image = infosDuFilm.get("Poster", None)

                with col2:
                    # OMDB retourne "N/A" quand il n'y a pas de poster
                    if image == "N/A" or image is None:
                        st.write("Ton choix :")
                        # on affiche l'image de secours 
                        st.image("F:/projet2/pasaffiche.png")
                        st.write(choix)

                    else :
                    # affichage du choix
                        st.write("Ton choix :")
                        # on affiche l'image 
                        st.image(image)
                        st.write(choix)
                        
            # si pas d'affiche alors on affiche cette image  
            except:
                st.image("F:/projet2/pasaffiche.png")

    
        # si pas de films selectionné alors numero de la ligne = premier films du réalisateur 
        elif choix2 != None:
            # affichage du choix
            st.write("Ton choix :", choix2)
            numeroDelaLigne = df[df[realisateur] == choix2].index[0]
        

        # on mets un espace entre les selections et l'image 
        st.space(size = "medium")


        
        # on choisit cet algorithme parce qu'on veut faire des recommendations (clustering)
        # son fonctionement est de rechercher les plus proche voisin (ce qui ressemble plus) de notre cible 
        nn = NearestNeighbors(n_neighbors=6, metric="cosine")
        # on défini les colonnes X en retirant movie name et relisateur 
        # équivalent de : X = df.drop(["movie_name", "realisateur"], axis=1)
        X = df.drop(columns=[series_name, realisateur])
        # on définis la cible de notre algorithme 
        y = df[series_name] 
        # on entraine la modèle mais Clustering, donc pas de y
        nn.fit(X)
        # Ça sélectionne le vecteur de features du film choisi, qui sera ensuite comparé aux autres pour trouver les films du même cluster.
        # On récupère le profil du film choisi (ses genres, type, etc.)
        featuresAPredire = X.iloc[numeroDelaLigne, :]
        # On cherche les N films les plus proches dans l'espace des features
        distances, index = nn.kneighbors([featuresAPredire])
        # On récupère les titres des films voisins grâce à leurs index
        listeDesRecommandations = df[series_name][index[0]]
        # Affiche les voisins SANS le film lui-même (il est toujours index [0])
        st.subheader("les films recommander selon ta selection sont :")
        st.space("small")
        # on definis le nombre de colonnes en fonction du nombre de recommandation de films 
        cols = st.columns(len(listeDesRecommandations.values[1:]))
        # on boucle sur chaque colonne et sur chaque films recommander 
        # zip(cols, films) associe chaque film à sa colonne
        for col, cfilms in zip(cols, listeDesRecommandations.values[1:]):
            # with col: place le films dans la colonne associé 
            # dans la colonne i on affiche le code si dessous donc l'affiche 
            with col:
                try:
                    # on vient encoder le films dans la version que l'api comprend
                    titre_encode2 = urllib.parse.quote(cfilms)
                    # On demande à l'API OMDB le lien du poster
                    #infosDuFilm = json.loads(requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode2}").text)
                    request = requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode2}", headers = headers)
                    infosDuFilm = json.loads(request.text)
                    image = infosDuFilm.get("Poster", None)

                    # OMDB retourne "N/A" quand il n'y a pas de poster
                    if image == "N/A" or image is None or image == 0 or requests.get(f"http://www.omdbapi.com/?apikey=ba1b6295&t={titre_encode}").status_code == 404 or infosDuFilm.get(request) == "False" or infosDuFilm.get(request) == "N/A":
                        # on affiche l'image de secours 
                        st.image("F:/projet2/pasaffiche.png")
                    else :
                        # On affiche l'image en dessous
                        st.image(image)
                    # On affiche le titre
                    st.caption(cfilms)

                except:
                    #si pas d'affiche on affiche :
                    st.image("F:/projet2/pasaffiche.png")
                    st.caption(cfilms)

    else:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.badge("Vous n'avez choisit ni réalisateurs, ni films", color="red")
            st.space(size = "small")
            st.image("F:/projet2/pasaffiche.png")















# PAGE MA LISTE


elif page == "Ma liste":
    # FONCTIONS DE GESTION DE LA LISTE
    
    # on définit le dossier où seront sauvegardées les listes de chaque utilisateur
    LISTE_DIR = "F:/projet2/listes_utilisateurs/"
    # on crée le dossier s'il n'existe pas déjà (exist_ok=True évite une erreur si il existe)
    os.makedirs(LISTE_DIR, exist_ok=True)

    def chemin_liste(username, type_contenu):
        # on construit le chemin du fichier parquet propre à chaque utilisateur et type (films/series)
        # exemple : "F:/projet2/listes_utilisateurs/luck_films.parquet"
        return f"{LISTE_DIR}{username}_{type_contenu}.parquet"

    def charger_liste(username, type_contenu):
        # on récupère le chemin du fichier de cet utilisateur
        chemin = chemin_liste(username, type_contenu)
        # on vérifie si le fichier existe déjà sur le disque
        if os.path.exists(chemin):
            # si oui, on le charge et on retourne le DataFrame
            return pd.read_parquet(chemin)
        else:
            # si non (première fois), on retourne un DataFrame vide avec les bonnes colonnes
            return pd.DataFrame(columns=["titre", "annee", "genre", "note", "date_ajout"])

    def sauvegarder_liste(username, type_contenu, df):
        # on sauvegarde le DataFrame dans le fichier parquet de l'utilisateur
        # index=False pour ne pas sauvegarder les numéros de lignes
        df.to_parquet(chemin_liste(username, type_contenu), index=False)

    def ajouter_element(username, type_contenu, titre, annee, genre, note):
        # on charge la liste actuelle de l'utilisateur
        df = charger_liste(username, type_contenu)
        # on vérifie si le titre est déjà présent dans la liste pour éviter les doublons
        if titre in df["titre"].values:
            # si déjà présent on retourne False et un message d'erreur
            return False, "déjà dans ta liste"
        # on crée une nouvelle ligne avec les infos du film/série
        nouvelle_ligne = pd.DataFrame([{
            "titre":      titre,                                    # le titre saisi par l'utilisateur
            "annee":      annee,                                    # l'année saisie
            "genre":      genre,                                    # le genre saisi
            "note":       note,                                     # la note donnée par l'utilisateur
            "date_ajout": datetime.now().strftime("%d/%m/%Y")       # la date d'aujourd'hui automatiquement
        }])
        # on ajoute la nouvelle ligne au DataFrame existant
        # ignore_index=True pour recalculer les numéros de lignes proprement
        df = pd.concat([df, nouvelle_ligne], ignore_index=True)
        # on sauvegarde la liste mise à jour sur le disque
        sauvegarder_liste(username, type_contenu, df)
        # on retourne True et un message de succès
        return True, "ajouté avec succès"

    def supprimer_element(username, type_contenu, titre):
        # on charge la liste actuelle de l'utilisateur
        df = charger_liste(username, type_contenu)
        # on garde toutes les lignes SAUF celle dont le titre correspond
        df = df[df["titre"] != titre]
        # on sauvegarde la liste mise à jour sans la ligne supprimée
        sauvegarder_liste(username, type_contenu, df)









    # on récupère le nom d'utilisateur connecté depuis la session streamlit
    username = st.session_state["username"]
    # on détermine si on affiche les films ou les séries selon la sous-page choisie
    type_contenu = "films" if sous_page == "Films" else "series"
    # on affiche le titre de la page
    st.title(f"Ma liste — {sous_page}")
    # ── Formulaire d'ajout ──────────────────
    st.subheader("➕ Ajouter un titre")
    # on crée deux colonnes pour organiser le formulaire
    col1, col2 = st.columns(2)

    with col1:
        # champ texte pour saisir le titre
        titre = st.text_input("Titre")
        # champ numérique pour l'année, entre 1900 et 2100, valeur par défaut 2024
        annee = st.number_input("Année", min_value=1900, max_value=2100, step=1)

    with col2:
        # champ texte pour le genre
        genre = st.text_input("Genre (ex: Action, Comédie...)")
        # curseur de note entre 0 et 10, valeur par défaut 5
        note = st.slider("Ta note", min_value=0, max_value=10, value=5)

    # bouton pour valider l'ajout, use_container_width=True pour qu'il prenne toute la largeur
    if st.button("Ajouter à ma liste", use_container_width=True):

        # on vérifie que le titre n'est pas vide (strip() supprime les espaces inutiles)
        if titre.strip() == "":
            # on affiche un avertissement si le titre est vide
            st.warning("Veuillez entrer un titre")
        else:
            # on appelle la fonction d'ajout avec les infos saisies
            ok, message = ajouter_element(username, type_contenu, titre.strip(), annee, genre, note)
            if ok:
                # si l'ajout a réussi on affiche un message de succès en vert
                st.success(f"✅ **{titre}** {message} !")
            else:
                # si le titre existe déjà on affiche un avertissement en orange
                st.warning(f"⚠️ **{titre}** est {message}")

    # on affiche un séparateur horizontal
    st.divider()

    # ── Affichage de la liste ───────────────
    st.subheader(f"📋 Mes {sous_page} sauvegardés")
    # on charge la liste de l'utilisateur connecté
    df_liste = charger_liste(username, type_contenu)

    # on vérifie si la liste est vide
    if df_liste.empty:
        # si vide on affiche un message informatif en bleu
        st.info(f"Ta liste de {sous_page.lower()} est vide. Ajoute des titres !")
    else:
        # menu déroulant pour choisir le critère de tri
        tri = st.selectbox("Trier par", ["date_ajout", "titre", "note", "annee"])
        # on trie le DataFrame selon le critère choisi
        # ascending=False uniquement pour la note (on veut les meilleures en premier)
        df_liste = df_liste.sort_values(tri, ascending=(tri != "note"))

        # on boucle sur chaque ligne du DataFrame pour afficher une carte par film/série
        for _, row in df_liste.iterrows():

            # on crée un conteneur avec bordure pour chaque film/série
            with st.container(border=True):

                # on crée deux colonnes : une grande pour les infos, une petite pour le bouton
                col1, col2 = st.columns([5, 1])

                with col1:
                    # on affiche le titre et l'année en grand
                    st.markdown(f"### 🎬 {row['titre']} ({int(row['annee'])})")
                    # on affiche le genre, la note et la date d'ajout sur une ligne
                    st.markdown(f"🎭 **Genre :** {row['genre']}  |  ⭐ **Note :** {row['note']}/10  |  📅 **Ajouté le :** {row['date_ajout']}")

                with col2:
                    # bouton supprimer avec une clé unique par film pour éviter les conflits streamlit
                    if st.button("🗑️ Supprimer", key=f"suppr_{row['titre']}"):
                        # on appelle la fonction de suppression
                        supprimer_element(username, type_contenu, row["titre"])
                        # on recharge la page pour mettre à jour l'affichage immédiatement
                        st.rerun()

        # on affiche un séparateur avant les statistiques
        st.divider()
        # on crée trois colonnes pour afficher les statistiques rapides
        col1, col2, col3 = st.columns(3)
        # nombre total de films/séries dans la liste
        col1.metric(f"Total {sous_page}", len(df_liste))
        # moyenne des notes arrondie à 1 décimale
        col2.metric("Note moyenne", f"{df_liste['note'].mean():.1f}/10")
        # titre ayant la note la plus haute (idxmax retourne l'index de la valeur max)
        col3.metric("Mieux noté", df_liste.loc[df_liste['note'].idxmax(), 'titre'])













# PAGE STATISTIQUE GENERAL 

elif page == "Statistiques" and sous_page == "Général":

    @st.cache_data
    def load_data():
    # definition de data frame 
        df = pd.read_csv("F:/projet2/films/nombre_de_films_genre.csv")
        return df
    df = load_data()

    @st.cache_data
    def load_data():
    # definition de data frame 
        df = pd.read_csv("F:/projet2/films/note_par_type.csv")
        return df
    df2 = load_data()

    @st.cache_data
    def load_data():
    # definition de data frame 
        df = pd.read_csv("F:/projet2/series/series_par_genres.csv")
        return df
    df3 = load_data()

    @st.cache_data
    def load_data():
    # definition de data frame 
        df = pd.read_csv("F:/projet2/series/notes_genres.csv")
        return df
    df4 = load_data()
    

    col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center")
    
    with col1:
        with st.container():

            fig = px.pie(df2, 
                        names='type',        # les catégories
                        values='note',        # les valeurs
                        title="Répartition des notes par type",
                        color_discrete_sequence=[
                 "#BD9205",   # jaune or
                 "#FFC300",   # jaune vif
                 "#745F04",   # jaune orangé
                 "#C8861A",   # jaune clair
                 "#997101",   # jaune foncé
             ])
            
            st.plotly_chart(fig)
    
    with col2:
        with st.container():

            st.write("Nombres de séries par genres")

            st.bar_chart(df3, 
                        x = 'genres', 
                        y = 'nombre',
                        color = "#D4A509")  
            
    with col3:
        with st.container():

            st.write("Nombres de votants par genres pour les séries")

            st.bar_chart(df4, 
                        x = 'genres', 
                        y = 'nombre_votant',
                        color = "#D4A509")

    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] {
        gap: 0rem;        /* ← réduit l'espace entre les blocs */
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], vertical_alignment="center")

    with col1:
        with st.container():

            st.write("Nombre de films par genres")

            st.bar_chart(df, 
                        x = 'genres', 
                        y = 'nombre_de_film',
                        color = "#D4A509")
            
    with col2:
        with st.container():

            st.write("Moyenne par genres")

            st.bar_chart(df, 
                        x = 'genres', 
                        y = 'moyenne',
                        color = "#D4A509")  
















# PAGE DONNEES FILMS 

# creer la sous page données films 
elif page == "Données" and sous_page == "Films":
    st.title("Exploration des données", text_alignment = "center")
    # creer un espace entre le titre et les données 
    st.space(size = "medium")


    # on import les graphiques 
    image = {
        "genres" : "F:/projet2/films/Image13.png", 
        "Fr" : "F:/projet2/films/Image14.png",
        "note" : "F:/projet2/films/Image15.png"
    }
    

    # on ecrit la description des graphiques associés 
    text = {
        "descrption1" : "Cette slide nous montre un nombre de films total de 10 milions, on remarque que la catégorie ayant les mailleurs votes sont le documentaire "
        ", on remarque que 57 pourcents des films font entre 30 et 90 minutes",
        "descrption2" : "Cette slide nous montre que la majorité des films se situe entre une note de 6 à 8 de moyenne, le réalisateur le mieux noté est 'Bert De Leon'",
        "descrption3" : "Cette slide nous montre que la catégorie aynt le plus de vote sont les films d'action vient ensuite les dramas"
    }



    # on defini le nombre de colonne par la longueur du dictionnaire image 
    cols = st.columns(len(image))
    # on boucle les colonnes, les graphiques, et les descriptions 
    # puis on les associe avec zip on vient extraire les valeurs avec .values()
    for col, stats, desc in zip(cols, image.values(), text.values()):
        with col:
            st.image(stats)
            st.text(desc)
    
    # on met un espace entre les lignes de graphiques 
    st.space(size= "medium")

    










# PAGE DONNEES SERIES 

# creer la sous page données series 
elif page == "Données" and sous_page == "Séries":
    st.title("Exploration des données", text_alignment = "center")
    # creer un espace entre le titre et les données 
    st.space(size = "medium")


    # on import les graphiques 
    image = {
        "genres" : "F:\projet2\series\Image6.png", 
        "Fr" : "F:\projet2\series\Image7.png",
        "note" : "F:\projet2\series\Image8.png"
    }
     # on import les graphiques pour la deuxieme ligne
    image2 = {
        "catégorie" : "F:\projet2\series\Image9.png"
    }

    # on ecrit la description des graphiques associés 
    text = {
        "descrption1" : "Dans cette slide, on peut observer que 81 pourcents de séries sont classé en tant que tvséries, les minis séries représente 19%, des données"
        "les 3 genres avec le plusde séries sont : les comedies, les drama, et les documentaires",
        "descrption2" : "Dans cette slide, on constate qu'il y as une forte évolution du nombre de séries depuis les années 1980, pour cause le nombre de series sortie en france avant l'an 2000 "
        "représente seulement 16%",
        "descrption3" : "Cette slide, nous montre que la moyenne n'a aucune corrélation avec le nombre d'épisode d'une series. La majorité des séries ont une note entre 6 et 8"
    }
    # on ecrit la description des graphiques associés pour la deuxieme lignes 
    text2 = {
        "descrption4" : "Cette slide, la majorité des séries ont un score IMDB entre 6 et 8. le genre le plus apprécié sont les commédies",
    }



    # on defini le nombre de colonne par la longueur du dictionnaire image 
    cols = st.columns(len(image))
    # on boucle les colonnes, les graphiques, et les descriptions 
    # puis on les associe avec zip on vient extraire les valeurs avec .values()
    for col, stats, desc in zip(cols, image.values(), text.values()):
        with col:
            st.image(stats)
            st.text(desc)
    
    # on met un espace entre les lignes de graphiques 
    st.space(size= "medium")


    # on defini le nombre de colonne par la longueur du dictionnaire image pour la deuxieme ligne  
    cols = st.columns(len(image2)+2)
    # on boucle les colonnes, les graphiques, et les descriptions 
    # puis on les associe avec zip on vient extraire les valeurs avec .values()
    for col, stats, desc in zip(cols, image2.values(), text2.values()):
        with col:
            st.image(stats)
            st.text(desc) 













# PAGE DONNEES SERIES 

# creer la sous page données creuse 
elif page == "Données" and sous_page == "Creuse":
    # creer le titre 
    st.title("Exploration des données", text_alignment = "center")
    # creer un espace entre le titre et les données 
    st.space(size = "medium")


    
    # on import les graphiques 
    image = {
        "age" : "F:/projet2/creuse/age_creuse.png", 
        "salaire" : "F:/projet2/creuse/salaire_creuse.png",
        "tranche" : "F:/projet2/creuse/Image5.png"
    }
    # on import les graphiques pour la deuxieme ligne
    image2 = {
        "catégorie" : "F:\projet2\creuse\Image4.png", 
    }
    
    # on ecrit la description des graphiques associés 
    text = {
        "descrption1" : "Dans ce graphique, on peut obeserver que la majorité de la population se site entre 30 et 89 ans." 
        " Toutefois la tranche d'age la plus présente est celle entre 60 et 74 ans. On constate donc la précsence d'une population assez agée",
        "descrption2" : "Cet histogramme nous offre une comparaison du salaire moyen annuel de la creuse par rapport à celui national."
        " On peut rearquer que celui-ci est inférieur au salaire moyen national. Il est éffectivement de 20150 € ",
        "descrption3" : "Comme nous pouvons le voir la grande majoritée des habitants habitent dans des petits villages hors des grandes villes"
    }
    # on ecrit la description des graphiques associés pour la deuxieme lignes 
    text2 = {
        "descrption4" : "Dans ce graphique, on constate que pres de 40 pourcents de la population est retraité",
    }
    


    # on defini le nombre de colonne par la longueur du dictionnaire image 
    cols = st.columns(len(image))
    # on boucle les colonnes, les graphiques, et les descriptions 
    # puis on les associe avec zip on vient extraire les valeurs avec .values()
    for col, stats, desc in zip(cols, image.values(), text.values()):
        with col:
            st.image(stats)
            st.text(desc) 

    # on met un espace entre les lignes de graphiques 
    st.space(size= "medium")


    # on defini le nombre de colonne par la longueur du dictionnaire image pour la deuxieme ligne  
    cols = st.columns(len(image2)+2)
    # on boucle les colonnes, les graphiques, et les descriptions 
    # puis on les associe avec zip on vient extraire les valeurs avec .values()
    for col, stats, desc in zip(cols, image2.values(), text2.values()):
        with col:
            st.image(stats)
            st.text(desc) 