#!/usr/bin/env python3
"""
Generate a wordcloud from CIRED document themes.

This script creates a wordcloud visualization from document themes and saves it
as a static image that can be served by the analytics server.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from r2r import R2RClient
from wordcloud import STOPWORDS, WordCloud

from intake.config import R2R_DEFAULT_BASE_URL, setup_logging
from intake.utils import get_server_documents
from deep_translator import GoogleTranslator

setup_logging()

FRENCH_STOPWORDS = {
    "le",
    "de",
    "et",
    "à",
    "un",
    "il",
    "être",
    "et",
    "en",
    "avoir",
    "que",
    "pour",
    "dans",
    "ce",
    "son",
    "une",
    "sur",
    "avec",
    "ne",
    "se",
    "pas",
    "tout",
    "plus",
    "par",
    "grand",
    "mais",
    "si",
    "ou",
    "très",
    "faire",
    "du",
    "la",
    "des",
    "les",
    "au",
    "aux",
    "cette",
    "ces",
    "ses",
    "leur",
    "leurs",
    "nos",
    "vos",
    "mes",
    "tes",
    "sa",
    "ma",
    "ta",
    "notre",
    "votre",
    "mon",
    "ton",
    "son",
    "comme",
    "aussi",
    "bien",
    "encore",
    "déjà",
    "toujours",
    "jamais",
    "souvent",
    "parfois",
    "quelquefois",
    "analyse",
    "principales",
    "thématiques",
    "couvertes",
    "corpus",
    "englobent",
    "pdf",
    "l",
    "using",
    "use",
    "s",
    "d",
    "low",
    "new",
    "toward",
    "approach",
    "co",
    "framework",
    "based",
    "multi",
    "Rapport",
    "study",
    "entre",
    "review",
    "Two",
    "Comment",
    "d'un",
    "d'une",
    "Assessing",
    "l'environnement",
    "rechearch",
    "recherche",
    "est",
    "cas",
    "vers",
    "mise",
    "mode",
    "l",
}

CIRED_THEMES = """
changement climatique transition énergétique politique climatique taxe carbone
prix carbone modélisation macro-économique CGE IMACLIM émissions CO2 efficacité énergétique
scénarios prospectifs atténuation mitigation adaptation équité justice distributive
fiscalité environnementale marchés électricité sécurité énergétique capture stockage carbone
CCS mobilité électrique agriculture usage terres bioénergies biocarburants coûts atténuation
investissements bas-carbone marchés internationaux carbone tableaux input-output hybrides
risque incertitude précarité énergétique gouvernance européenne énergie modèles équilibre général
calculable développement durable réformes prix énergie analyse répartition impacts
stratégies nationales bas-carbone économie environnement recherche CIRED développement
politiques publiques énergies renouvelables transition écologique innovation technologique
financement climat adaptation vulnérabilité résilience économie circulaire efficience
ressources naturelles biodiversité écosystèmes services écosystémiques capital naturel
évaluation économique externalités environnementales instruments économiques régulation
marché carbone mécanismes flexibilité protocole Kyoto accord Paris objectifs climatiques
trajectoires émissions budgets carbone neutralité carbone décarbonation secteurs économiques
transport bâtiment industrie agriculture foresterie usage sols changement affectation terres
LULUCF séquestration carbone puits carbone sources émissions inventaires gaz effet serre
méthane protoxyde azote gaz fluorés potentiel réchauffement global PRG équivalent CO2
modélisation intégrée évaluation impacts économiques coûts sociaux carbone taux actualisation
analyse coût-bénéfice analyse coût-efficacité instruments politiques taxes subventions
quotas échangeables systèmes cap-and-trade mécanismes marché volontaire compensation carbone
crédits carbone addictionnalité permanence fuites leakage double comptage intégrité
environnementale mesure reporting vérification MRV transparence gouvernance climatique
négociations internationales diplomatie climatique coopération internationale transferts
technologiques financement climatique fonds vert climat adaptation mitigation pertes
dommages loss damage assurance risques climatiques catastrophes naturelles événements
extrêmes sécheresse inondations tempêtes cyclones canicules vagues chaleur stress hydrique
ressources eau agriculture irriguée sécurité alimentaire rendements agricoles productivité
sols dégradation désertification érosion fertilité sols organiques matière organique
séquestration sol pratiques agricoles durables agroécologie agriculture conservation
agriculture précision technologies numériques intelligence artificielle big data
modélisation prédictive optimisation systèmes énergétiques smart grids réseaux intelligents
stockage énergie batteries hydrogène power-to-gas power-to-liquid électrolyse piles
combustible mobilité hydrogène transport maritime aviation biocarburants avancés
électrocarburants carburants synthétiques capture utilisation carbone CCU économie
hydrogène vallée hydrogène clusters industriels reconversion industrielle emplois verts
transition juste formation professionnelle compétences nouvelles technologies émergentes
rupture innovation disruptive recherche développement R&D investissement public privé
partenariats public-privé financement innovation capital-risque fonds investissement
obligations vertes green bonds taxonomie finance durable ESG critères environnementaux
sociaux gouvernance reporting extra-financier divulgation risques climatiques TCFD
stress tests climatiques banques centrales politique monétaire stabilité financière
risques systémiques transition ordonnée désordonnée actifs échoués stranded assets
désinvestissement fossiles réallocation capitaux investissements verts infrastructure
résiliente adaptation infrastructure critique réseaux transport énergie télécommunications
eau assainissement santé publique qualité air pollution atmosphérique particules fines
ozone troposphérique dioxyde azote composés organiques volatils COV santé environnementale
épidémiologie environnementale expositions environnementales biomonitoring indicateurs
santé environnement inégalités environnementales justice environnementale communautés
vulnérables populations défavorisées accès services environnementaux espaces verts
qualité vie bien-être indicateurs développement durable objectifs développement durable
ODD agenda 2030 cohérence politiques intégration sectorielle approche systémique
pensée systémique complexité incertitude robustesse résilience adaptabilité flexibilité
apprentissage adaptatif gestion adaptative expérimentation pilotes démonstrateurs
scaling up passage échelle diffusion innovations adoption technologies comportements
changement comportemental nudges incitations économiques sensibilisation communication
participation citoyenne démocratie participative gouvernance territoriale décentralisation
subsidiarité multi-niveaux gouvernance polycentriques réseaux acteurs parties prenantes
stakeholders engagement consultation concertation dialogue social acceptabilité sociale
légitimité transparence redevabilité accountability éthique responsabilité intergénérationnelle
équité intergénérationnelle développement soutenable durabilité forte faible capital
critique substituabilité complémentarité trade-offs synergies co-bénéfices effets rebond
paradoxe Jevons découplage relatif absolu dématérialisation économie fonctionnalité
économie service économie partage collaborative plateformes numériques digitalisation
transformation numérique industrie 4.0 internet objets IoT blockchain cryptomonnaies
bitcoin énergie numérique empreinte carbone numérique sobriété numérique écoconception
analyse cycle vie ACV empreinte environnementale empreinte carbone empreinte eau
empreinte terre empreinte matières premières économie circulaire boucles fermées
symbiose industrielle écologie industrielle métabolisme urbain flux matières énergie
déchets valorisation recyclage réutilisation réparation reconditionnement upcycling
obsolescence programmée durabilité produits écoconception design circulaire biomimétisme
nature-based solutions solutions fondées nature infrastructure verte bleue services
écosystémiques paiements services environnementaux PSE mécanismes REDD+ déforestation
évitée dégradation forêts conservation biodiversité aires protégées corridors écologiques
connectivité écologique fragmentation habitats restauration écologique rewilding
ensauvagement gestion écosystèmes gestion intégrée zones côtières GIZC planification
spatiale marine aménagement territoire urbanisme durable villes durables smart cities
métropoles mégapoles urbanisation périurbanisation étalement urbain densification
mixité fonctionnelle transports publics mobilité douce vélo marche intermodalité
multimodalité logistique urbaine livraisons derniers kilomètres véhicules électriques
autonomes covoiturage autopartage mobilité service MaaS planification transport
accessibilité mobilité inclusive fracture mobilité précarité mobilité rural périphérique
"""


def get_titles_from_r2r() -> list[str]:
    """Fetch the list of document titles from the R2R server."""
    client = R2RClient(base_url=R2R_DEFAULT_BASE_URL)
    df = get_server_documents(client)
    if df is None or "title" not in df.columns:
        logging.error("Could not find publication titles from the R2R server")
        return []
    raw_titles = df["title"].dropna().astype(str).tolist()
    translator = GoogleTranslator(source='auto', target='fr')
    try:
        french_titles: list[str] = []
        batch: list[str] = []
        current_len = 0
        for title in raw_titles:
            title_len = len(title) + 4  # plus délimiteur
            if current_len + title_len > 4500 and batch:
                concatenated = " /// ".join(batch)
                translated = translator.translate(concatenated)
                french_titles.extend([t.strip() for t in translated.split("///")])
                batch = []
                current_len = 0
            batch.append(title)
            current_len += title_len
        if batch:
            concatenated = " /// ".join(batch)
            translated = translator.translate(concatenated)
            french_titles.extend([t.strip() for t in translated.split("///")])
        return french_titles
    except Exception as e:
        logging.warning(f"Translation failed : {e}. Utilisation des titres originaux.")
        return raw_titles


def create_wordcloud(text: str, output_path: Path) -> None:
    """Create and save a wordcloud from the given text."""
    wordcloud = WordCloud(
        width=1024,
        height=640,
        background_color="white",
        max_words=100,
        stopwords=STOPWORDS.union(FRENCH_STOPWORDS),
        colormap="viridis",
        relative_scaling=0.4,
        min_font_size=10,
        max_font_size=60,
        prefer_horizontal=0.7,
        collocations=True,
        scale=2,
    ).generate(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12.8, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(
        output_path, dpi=80, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    logging.info(f"Wordcloud saved to: {output_path}")


def main() -> None:
    """Generate the CIRED themes wordcloud."""
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    output_path = static_dir / "cired_wordcloud.png"

    titles = get_titles_from_r2r()
    if titles:
        text = " ".join(titles)
        logging.info(
            "Generating wordcloud from a bag of %d titles (%d words)",
            len(titles),
            len(text.split()),
        )
    else:
        logging.warning("Using hardcoded themes to generate wordcloud.")
        text = CIRED_THEMES

    create_wordcloud(text, output_path)


if __name__ == "__main__":
    main()
