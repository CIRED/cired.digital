# Chatbot IA pour les publications HAL du CIRED

Un outil open source pour examiner les coûts et les bénéfices de pouvoir interroger les publications scientifiques d'un laboratoire de manière conversationnelle.

For the systematic description of this repository in English, see: [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MinhHaDuong/cired.digital)

## Description

Nous développons ici un chatbot interactif permettant aux utilisateurs d'explorer les publications scientifiques du CIRED stockées dans la collection HAL via des requêtes en langage naturel.

L'outil vise à :

- Valoriser les travaux du laboratoire grâce à un accès intuitif et conversationnel.
- Contribuer à la science ouverte en fournissant un code réutilisable pour d'autres collections HAL.
- Dimensionner et connaître les coûts financiers et environnementaux d'un tel chatbot.
- Analyser les pratiques de médiation scientifique via l'étude des interactions utilisateurs.

Fonctionnalités :

-    Interface conversationnelle : Posez des questions en français ou en anglais sur les publications (auteurs, méthodologies, résultats, etc.).
-    Connexion à HAL : Interrogation dynamique de la collection HAL du CIRED.
-    Open source : Code modulable pour s'adapter à d'autres collections ou disciplines.
-    Hébergement durable : Déployé sur l'infrastructure de recherche d'une tutelle du CIRED.

Stack technique :

-    IA générative : API vers des modèles de langage (LLM) open source ou commerciaux (ex: Mistral, OpenAI, DeepSeek).
-    Backend RAG full-stack: Pour l'ingestion, la recherche, la réponse: R2R.
-    Frontend : Single page modern vanilla JavaScript with Tailwind CSS.
-    Hébergement : Déploiement docker sur un VPS commercial.

Le prototype sera déployé en ligne auprès d'une audience progressivement élargie pour une durée de quelque mois, afin d'évaluer:

-    L'expérience utilisateur
-    La pertinence des réponses
-    L'impact sur la diffusion scientifique

## Organisation de `cired.digital/`

This project's goal is to implement a chatbot with CIRED publications.

### credentials

Project's secret keys and passwords.

- Contents not versionned on GitHub because secret.
- Contents not synced by Nextcloud.
- Developer should populate their own local copy.
- For deployment, transfer keys separately

### `data/`
raw PDFs, extracted text, metadata, summaries, chunks, vector indexes...
Data contents is not versionned in the git, only the directory structure and the README.md.

data/source, data/prepared and data/archived are reserved purely for storage. Do not place processing scripts or metadata code there. All transformation logic should live under `src/`.

Consider files in `data/source` `data/prepared` and `data/archived`  as immutable: its state cannot be modified after it is created. Any “change” to an immutable yields a brand-new object, leaving the original intact.

### `docs/`
architecture docs, OpenAPI spec, runbooks, ethics guidelines,
technical documentations, diagrams.
Human‑readable, preferably markdown.
Versionned.

### `reports/`
Generated output.
Contents is not versionned, only the directory and the README.md.

### `src/`

Project's code. See `src/README.md` for an architectural overview then `docs/blueprints.md` for details. Guidelines are in `docs/CODE_STYLE.md`.

### `tests/`
unit & integration tests
Mirrors the organisation of `src/`

Pour en savoir plus: (https://deepwiki.com/MinhHaDuong/cired.digital)
