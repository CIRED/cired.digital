# Cirdi: CIRED digital documentation assistant

Un outil open source pour examiner les coûts et les bénéfices de pouvoir interroger les publications scientifiques d'un laboratoire de manière conversationnelle.

For the systematic description of this repository in English, see: [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MinhHaDuong/cired.digital)

## Description

Nous développons ici un assistant interactif permettant aux utilisateurs d'explorer les publications scientifiques du CIRED stockées dans la collection HAL via des requêtes en langage naturel.

L'outil vise à :

- Valoriser les travaux du laboratoire grâce à un accès intuitif et conversationnel.
- Contribuer à la science ouverte en fournissant un code réutilisable pour d'autres collections HAL.
- Dimensionner et connaître les coûts financiers et environnementaux d'un tel chatbot.
- Analyser les pratiques de médiation scientifique via l'étude des interactions utilisateurs.

Fonctionnalités :

-    Interface en language naturel: Posez des questions sur les publications (auteurs, méthodologies, résultats, etc.).
-    Connexion à HAL : L'assistant base ses réponses sur les documents du CIRED en archive ouverte dans HAL.
-    Open source : Code modulable pour s'adapter à d'autres collections ou disciplines.

Stack technique :

-    IA générative : API vers des modèles de langage (LLM) open source ou commerciaux.
-    Backend RAG full-stack: Pour l'ingestion, la recherche, la réponse: R2R.
-    Frontend : Single page modern vanilla JavaScript with Tailwind CSS.
-    Hébergement : Déploiement docker sur un VPS commercial.

Le prototype sera déployé en ligne auprès d'une audience progressivement élargie pour une durée de quelque mois, afin d'évaluer:

-    L'expérience utilisateur
-    La pertinence des réponses
-    L'impact sur la diffusion scientifique

## Annotated map

Note: only `cired.digital/` is versionned and open. Its sibling directories are project-confidential.

CIRED.digital/
├ accounting/       # finances
├ discussions/      # meetings and emails
├ documents/        # deliverables
├ secrets/          # keys, logins, configurations...
└ cired.digital/    # **This repo**
  ├ data/             # Raw and processed research documents
  | ├ source/           # raw downloaded files
  | ├ prepared/         # files ready to upload to R2R.
  | └ archived/         # volumes snapshots
  ├ docs/               # Technical documentation and guidelines
  ├ reports/            # Analytical outputs
  ├ src/              # Application source code
  | ├ analytics/        # Logging usage and user feedback
  | ├ frontend/         # Main user interface
  | ├ intake/           # Data retrieval and preparation
  | └ docker/            # Scripts for R2R, analytics and frontend containers
  |   ├ compose.yaml          # docker compose configuration.
  |   ├ ops/                  # Bash scripts to manage the stack state.
  |   ├ user_configs/         # Custom configuration files accessible to the application the `r2r` container.
  |   ├ user_tools/           # Custom tool files accessible to the application in the `r2r` container. Not used yet.
  |   ├ scripts/              # Scripts made available to r2r container. Copied from `config.upstream`, do not modify.
  |   └ config.upstream/      # Temporary directory - not versionned in our repo.
  └ tests/            # Automated tests


### `data/`
- Not versionned in the git, only the directory structure and the README.md.
- Do not place processing scripts or metadata code there.
- All transformation logic should live under `src/intake/`.
- Manage files in `data/source` `data/prepared` and `data/archived` as immutable: cannot be modified after it is created. Instead of changing a file, create a new one. Timestamp in the filename.

### `docs/`
- Human‑readable
- Preferably markdown.
- Versionned.
- Please read `CODE_STYLE.md` and  `CONTRIBUTING.md`.
- Early architecture in `blueprints.md` is outdated.

### `reports/`
- Generated output.
- Contents is not versionned, only the directory and the README.md.
- Contents is precious: make copies under `CIRED.digital/documents`.

### `src/`
- Versionned.
