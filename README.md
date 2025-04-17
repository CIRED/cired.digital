# Chatbot IA pour les publications HAL du CIRED

Un outil open source pour interroger les publications scientifiques de manière conversationnelle.

## Description

Ce projet expérimental développe un chatbot interactif basé sur l'intelligence artificielle, permettant aux utilisateurs d'explorer les publications scientifiques du CIRED stockées dans la collection HAL via des requêtes en langage naturel.

L'outil vise à :

- Valoriser les travaux du laboratoire grâce à un accès intuitif et conversationnel.
- Contribuer à la science ouverte en fournissant un code réutilisable pour d'autres collections HAL.
- Analyser les pratiques de médiation scientifique via l'étude des interactions utilisateurs.

Fonctionnalités

-    Interface conversationnelle : Posez des questions en français ou en anglais sur les publications (auteurs, méthodologies, résultats, etc.).
-    Connexion à HAL : Interrogation dynamique de la collection HAL du CIRED.
-    Open source : Code modulable pour s'adapter à d'autres collections ou disciplines.
-    Hébergement durable : Déployé sur l'infrastructure de recherche d'une tutelle du CIRED.

Stack technique

-    IA générative : Modèles de langage (LLM) open source ou API spécialisées (ex: OpenAI, Hugging Face).
-    Backend : Python/FastAPI ou Node.js pour la logique de recherche.
-    Frontend : Framework web léger (Streamlit, Gradio, ou React).
-    Hébergement : Serveurs institutionnels ou solution cloud (Docker possible).

Déploiement Un prototype sera testé en lignepour évaluer :

-    L'expérience utilisateur
-    La pertinence des réponses
-    L'impact sur la diffusion scientifique


## Organization du code

This project's goal is to implement a chatbot with CIRED publications.

### data/
Raw and processed data.
Organization will be updated as we develop the processing.
Not versionned in the git.

**CIRED_numerisation_RAW** contains a read-only copy of pre-1998 publications, scanned OCRed. Remains to be processed.

**pdfs** contents downloaded from HAL.

### docs/
Human‑readable docs, diagrams, README extensions.
Preferably markdown.

### reports/
Generated output.

### src/cired_chatbot/
Our module. Python >= 3.11. Passes ```ruff checks``` with no errors or warnings.

We plan to run a full RAG stack in docker as a separate service, and and deploy ours on the same machine as a use-case-specific layer.

There will be thin HTTP/gRPC wrappers, e.g. ```r2r_client.py``` to communicate with the RAG stack: push documents, ask questions, get justified answer with sources citation and chunk quotes.

We will use env‑vars (e.g. R2R_BASE_URL, R2R_API_KEY) to configure the client at runtime.

**cli** Command line interface tools. Scripts.

### tests/
unit & integration tests
