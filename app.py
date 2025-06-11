
import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import qrcode
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title='ERP Hydranet', layout='wide')
st.title('🌐 ERP Hydranet - Gestion Complète')

menu = ['Accueil', 'Produits', 'Clients', 'Commandes', 'Statistiques', 'Facturation', 'Export CSV', 'Historique', 'Notifications', 'Scraping']
choix = st.sidebar.selectbox('Menu', menu)

if 'produits' not in st.session_state:
    st.session_state.produits = []
if 'clients' not in st.session_state:
    st.session_state.clients = []
if 'commandes' not in st.session_state:
    st.session_state.commandes = []
if 'historique' not in st.session_state:
    st.session_state.historique = []

def afficher_table(data, colonnes):
    df = pd.DataFrame(data, columns=colonnes)
    st.dataframe(df)

def exporter_pdf(data, colonnes, titre):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    pdf.cell(200, 10, txt=titre, ln=True, align='C')
    for row in data:
        for i, item in enumerate(row):
            pdf.cell(40, 10, txt=f'{colonnes[i]}: {item}', ln=1)
        pdf.cell(200, 10, txt='----------------------', ln=1)
    output_file = f"{titre}.pdf"
    pdf.output(output_file)
    with open(output_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{output_file}">📄 Télécharger {titre}.pdf</a>'
    st.markdown(href, unsafe_allow_html=True)

def envoyer_notification(email, sujet, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = "votre_email@example.com"
        msg['To'] = email
        msg['Subject'] = sujet
        msg.attach(MIMEText(message, 'plain'))
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login("votre_email@example.com", "votre_mot_de_passe")
            server.send_message(msg)
        st.success("E-mail envoyé avec succès.")
    except Exception as e:
        st.error(f"Erreur: {e}")

def generer_qr_code(data):
    qr = qrcode.make(data)
    path = "facture_qr.png"
    qr.save(path)
    return path

def comparer_prix(url, produit):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        prix = soup.find('span', class_='product-price')
        if prix:
            return float(prix.text.strip().replace('DT', '').replace(',', '.'))
        return None
    except Exception as e:
        st.error(f"Erreur scraping : {e}")
        return None

if choix == 'Accueil':
    st.subheader('Bienvenue dans le système ERP de Hydranet.')
    st.image('https://hydranet.tn/wp-content/uploads/2024/01/cropped-logo-site-1.png', width=200)

elif choix == 'Produits':
    st.header('📦 Gestion des Produits')
    nom = st.text_input('Nom')
    prix = st.number_input('Prix', min_value=0.0)
    stock = st.number_input('Stock', min_value=0)
    if st.button('Ajouter Produit'):
        st.session_state.produits.append([nom, prix, stock])
        st.session_state.historique.append(f"Produit ajouté: {nom}")
    afficher_table(st.session_state.produits, ['Nom', 'Prix', 'Stock'])
    if st.button('📄 Exporter PDF'):
        exporter_pdf(st.session_state.produits, ['Nom', 'Prix', 'Stock'], 'Produits')

elif choix == 'Clients':
    st.header('👥 Clients')
    nom = st.text_input('Nom client')
    email = st.text_input('Email')
    tel = st.text_input('Téléphone')
    if st.button('Ajouter Client'):
        st.session_state.clients.append([nom, email, tel])
        st.session_state.historique.append(f"Client ajouté: {nom}")
    afficher_table(st.session_state.clients, ['Nom', 'Email', 'Téléphone'])

elif choix == 'Commandes':
    st.header('🛒 Commandes')
    client = st.selectbox('Client', [c[0] for c in st.session_state.clients] or [''])
    produit = st.selectbox('Produit', [p[0] for p in st.session_state.produits] or [''])
    qte = st.number_input('Quantité', min_value=1)
    if st.button('Ajouter Commande'):
        st.session_state.commandes.append([client, produit, qte])
        st.session_state.historique.append(f"Commande: {client} - {produit} x{qte}")
    afficher_table(st.session_state.commandes, ['Client', 'Produit', 'Quantité'])

elif choix == 'Statistiques':
    st.header('📊 Statistiques')
    st.metric("Produits", len(st.session_state.produits))
    st.metric("Clients", len(st.session_state.clients))
    st.metric("Commandes", len(st.session_state.commandes))
    ca = sum([cmd[2] * next((p[1] for p in st.session_state.produits if p[0] == cmd[1]), 0) for cmd in st.session_state.commandes])
    st.metric("Chiffre d'affaires", f"{ca:.2f} DT")

elif choix == 'Facturation':
    st.header("📃 Facture PDF + QR")
    if st.session_state.commandes:
        for i, cmd in enumerate(st.session_state.commandes):
            st.markdown(f"Commande {i+1}: {cmd[0]} - {cmd[1]} x {cmd[2]}")
        if st.button("📤 Générer Facture"):
            exporter_pdf(st.session_state.commandes, ['Client', 'Produit', 'Quantité'], 'Facture')
            path = generer_qr_code(str(st.session_state.commandes))
            st.image(path)

elif choix == 'Export CSV':
    st.header("📁 Export CSV")
    df = pd.DataFrame(st.session_state.commandes, columns=["Client", "Produit", "Quantité"])
    st.download_button("⬇️ Télécharger CSV", df.to_csv(index=False).encode(), "commandes.csv", "text/csv")

elif choix == 'Historique':
    st.header("📝 Historique")
    for h in st.session_state.historique:
        st.write(h)

elif choix == 'Notifications':
    st.header("📧 Envoyer une notification")
    email = st.text_input("Email")
    sujet = st.text_input("Sujet")
    message = st.text_area("Message")
    if st.button("Envoyer"):
        envoyer_notification(email, sujet, message)

elif choix == 'Scraping':
    st.header("🔎 Scraping")
    url = st.text_input("URL du produit")
    nom = st.text_input("Nom du produit")
    if st.button("Comparer Prix"):
        prix_site = comparer_prix(url, nom)
        st.write(f"Prix trouvé : {prix_site}")
