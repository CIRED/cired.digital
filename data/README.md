# cired.digital/data directory organization

CIRED publications data at various stages of cooking. The directory follows a lifecycle-oriented approach.
Contents is not versioned in git.
We maintain a catalog + pool of files approach.

## source

Catalog and original files downloaded from various sources:

**hal** contains contents automatically downloaded from HAL, along with metadata.

These two large sources are stored out of the development tree since they are not used at the moment:

- **inari_data_CIRED_numerisation_zotero_www** holds a read-only copy of pre-1998 publications, scanned and OCRed. Note: This package includes documents with LEESU in the filename that are not relevant to CIRED.
- **inari_recueil_50ans_CIRED** holds the collection of articles selected by CIRED members as representative works, then refined into the 50th anniversary collection.

They would need deduplication and indexing. Our stance is that whoever created these archives is responsible to upload them to HAL. Using them directly would be a stopgap.

## prepared

At the moment we process the catalog only.

Later we may:
- Recompress or split oversized PDFs.
- Normalize Metadata. But cleaning up HAL is not our fight.
- Extract text from PDFs ourselves. Some is already available in HF dataset of HAL.
- Chunk and enrich ourselves.

The last to tasks only make sense if we have a way to evaluate quality, to ensure we outperform R2R build-ins.


## archived

Timestamped snapshots of the active system state:

- Used for backup and recovery
- Used for deployment in production and rollback
- Version history of the system state

*Created by snapshot scripts for deployment.*

## Live operational data

Operational data, between `prepared/` and `archived` lives in docker volumes.
We tried to use docker mounted volumes, but that led to permissions/ownership issues.
