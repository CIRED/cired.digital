# cired.digital/code/data directory organization

Raw and processed data.
Contents not versionned in the git.

## raw

For the downloaded files

**hal** contains contents automatically downloaded from HAL, along with metadata.

**inari_data_CIRED_numerisation_zotero_www** contains a read-only copy of pre-1998 publications, scanned OCRed. Remains to be processed.

**inari_recueil_50ans_CIRED** will contain the selected most representative articles.

## processed

Nothing at the moment. To start the project, focus on using the HAL collection to setup the proof of concept. We can always push the manually downloaded archives later.

Ideally the manually downloaded archives should not exist. They should be sent into HAL.

Nothing at the moment. But there will be a need to smart deduplicate, the files are properly named and organized.

We should look if ENPC did anything to the data that is not on inari. Since zotero is mentionned there may be metadata indexing somewhere.

---

## Note:

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
