# cired.digital/data directory organization

CIRED publications data at various stages of cooking. The directory follows a lifecycle-oriented approach.
Contents not versioned in git.

## source

Original files downloaded from various sources:

**hal** contains contents automatically downloaded from HAL, along with metadata.

**inari_data_CIRED_numerisation_zotero_www** contains a read-only copy of pre-1998 publications, scanned and OCRed. Remains to be processed. Note: This package includes documents with LEESU in the filename that are not relevant to CIRED.

**inari_recueil_50ans_CIRED** contains the collection of articles selected fifteen years ago by CIRED members as representative works, then refined into the 50th anniversary collection.

## prepared

Processed versions of source data ready for the RAG system:

- Extracted text from PDFs (some is already available in HF dataset)
- Text chunks, enriched
- Metadata normalization

*Currently empty.* Initial project focus is on the HAL collection for proof of concept.

## active

Live operational data for the running chatbot:

- Docker volume contents
- Database files with  generated embeddings and vector indexes
- Search indexes
- Active caches

*Managed by Docker containers.*

## archived

Timestamped snapshots of the active system state:

- Used for backup and recovery
- Used for deployment in production and rollback
- Version history of the system state

*Created by snapshot scripts for deployment.*

---

## Implementation Notes:

### Deduplication Strategy
We need smart deduplication since some documents appear in multiple source collections with different filenames.

### Pre-1998 Archives
The manually scanned archives should ideally be uploaded to HAL rather than processed separately.

### ENPC Processing
We should investigate if École des Ponts et Chaussées applied any processing to the inari data, particularly metadata indexing via Zotero.

---

## Source Note:

From:	Pottier Antonin <antonin.pottier@ehess.fr>
To:	Minh Ha Duong <minh@haduong.com>
Cc:	Naceur Chaabane <naceur.chaabane@cnrs.fr>, christophe cassen <christophe.cassen@cnrs.fr>
Subject:	Re: Archives du CIRED
Date:	Thu, 17 Apr 2025 09:49:51 +0200 (CEST)

Bonjour Minh,

il y a plusieurs choses différentes:

d'abord, les documents scannés par l'Ecole des Ponts, qui avaient été perdus et qui ont été retrouvés. Ils sont disponibles ici:
aussi sur inari:
/var/www/html/kCj0pHP0-CIRED_numerisation/zotero/www

Attention dans ce paquet il y a des documents avec LEESU dans le nom de fichier qui ne concernent pas le CIRED.

ensuite, la centaine d'articles sélectionnés il y a quinze ans par les membres du CIRED car considérés comme marquants. Nous les avons lus et avons choisis les articles qui figurent dans ce recueil.
Ils sont disponibles sur inari:
/var/www/html/Wehurei6-recueil_50ans_CIRED

Certains documents se retrouvent dans les deux, éventuellement avec des noms de fichiers différents.

A bientôt,

Antonin
