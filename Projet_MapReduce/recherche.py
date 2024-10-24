import os
import glob
from collections import defaultdict
from bs4 import BeautifulSoup
import streamlit as st
from unidecode import unidecode

# Fonction pour lire les fichiers HTML et extraire les liens et le contenu
def read_html_files(directory):
    pages = {}
    page_contents = {}
    all_links = set()  # Utiliser un ensemble pour éviter les doublons de liens
    for filepath in glob.glob(os.path.join(directory, '*.html')):
        with open(filepath, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            page_name = os.path.basename(filepath)
            
            # Extraire le texte du body
            body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ''
            page_contents[page_name] = body_text
            
            # Extraire les liens
            links = [a['href'] for a in soup.find_all('a', href=True)]
            pages[page_name] = links
            all_links.update(links)  # Ajouter tous les liens à l'ensemble des liens
    return pages, page_contents, all_links

# Initialisation du PageRank avec toutes les pages référencées
def initialize_page_ranks(pages, all_links):
    num_pages = len(all_links) if all_links else 1
    page_ranks = {page: 1.0 / num_pages for page in all_links}
    for links in pages.values():
        for link in links:
            if link not in page_ranks:
                page_ranks[link] = 1.0 / num_pages
    return page_ranks

# Définition des fonctions MapReduce pour le calcul du PageRank
def map_page_rank(pages, page_ranks):
    contributions = defaultdict(float)
    for page, links in pages.items():
        num_links = len(links)
        if num_links > 0 and page in page_ranks:  # Vérifier que la page source est dans page_ranks
            for link in links:
                contributions[link] += page_ranks[page] / num_links
    return contributions

def reduce_page_rank(contributions, damping_factor=0.85, num_pages=1):
    new_ranks = {page: (1 - damping_factor) / num_pages for page in contributions}
    for page, contribution in contributions.items():
        new_ranks[page] += damping_factor * contribution
    return new_ranks

# Calcul du PageRank par itérations
def calculate_page_rank(pages, all_links, iterations=10):
    page_ranks = initialize_page_ranks(pages, all_links)
    num_pages = len(page_ranks)
    for _ in range(iterations):
        contributions = map_page_rank(pages, page_ranks)
        page_ranks = reduce_page_rank(contributions, num_pages=num_pages)
    return page_ranks

# Création d'un index inversé
def create_inverted_index(page_contents):
    inverted_index = defaultdict(list)
    for page, content in page_contents.items():
        words = content.split()
        for word in words:
            normalized_word = unidecode(word.lower())  # Normaliser les termes
            inverted_index[normalized_word].append(page)
    return inverted_index

# Fonction de recherche
def search(query, inverted_index, page_ranks):
    terms = [unidecode(term.lower()) for term in query.split()]  # Normaliser les termes
    results = defaultdict(float)
    for term in terms:
        if term in inverted_index:
            for page in inverted_index[term]:
                results[page] += page_ranks.get(page, 0)
    return sorted([(page, rank) for page, rank in results.items() if rank > 0], key=lambda x: x[1], reverse=True)

# Interface utilisateur avec Streamlit
st.set_page_config(page_title="Simple Search Engine", page_icon="🔍")

st.title('🔍 Search engine with MapReduce')

directory = 'data'

if os.path.exists(directory):
    pages, page_contents, all_links = read_html_files(directory)

    # Initialisation de page_ranks
    page_ranks = initialize_page_ranks(pages, all_links)

    # Vérification et ajout des pages manquantes dans page_ranks
    for page in all_links:
        if page not in pages and page not in page_ranks:
            page_ranks[page] = 1.0 / len(all_links)

    page_ranks = calculate_page_rank(pages, all_links)
    inverted_index = create_inverted_index(page_contents)

    st.write("---")
    st.subheader("Search")

    # Récupérer la valeur actuelle de la recherche depuis st.session_state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = None

    # Afficher la zone de texte pour la recherche
    query = st.text_input('Enter your search query:', st.session_state.search_query)

    # Diviser l'espace en deux colonnes
    col1, col2 = st.columns([1, 1])

    # Gestion du bouton Search
    with col1:
        if st.button('Search'):
            st.session_state.search_query = query  # Mettre à jour la session avec la valeur de la recherche actuelle
            st.session_state.selected_page = None  # Réinitialiser la page sélectionnée

    # Gestion du bouton Reset
    with col2:
        if st.button('Initialiser'):
            st.session_state.search_query = ''  # Réinitialiser la session à une chaîne vide
            st.session_state.selected_page = None  # Réinitialiser la page sélectionnée

    # Vérifier si la recherche a été effectuée
    if st.session_state.search_query:
        results = search(st.session_state.search_query, inverted_index, page_ranks)
        if results:
            st.write('### Search Results:')
            for page, rank in results:
                percentage_rank = round(rank * 100, 2)
                if st.button(f"{page}: {percentage_rank}% Lire le contenu..."):
                    st.session_state.selected_page = page
        else:
            st.warning('No results found.')

    # Afficher le contenu de la page sélectionnée
    if st.session_state.selected_page:
        st.write(f"### Content of {st.session_state.selected_page}:")
        st.write(page_contents[st.session_state.selected_page])

else:
    st.sidebar.error(f'The directory {directory} does not exist. Please create it and add HTML files.')

st.write("---")
st.write("Developed by : AGBOTON Josué - NSELE Grace - AKADIRI Faiçole")
