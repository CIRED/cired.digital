# ✅ Plan d’action pour fiabiliser le déploiement de R2R

**Projet :** Déploiement de `cired.digital` sur Hetzner  
**Responsable :** Minh Ha-Duong  
**Dernière mise à jour :** 2025-05-16

---

## 📁 Objectifs

1. Fiabiliser le déploiement de l’application R2R (docker-compose).
2. Automatiser les snapshots/restaurations du volume de données.
3. Centraliser les chemins de configuration.
4. Documenter précisément les cas d’erreur et les codes de sortie.

---

## 🧱 Structure des scripts

| Script             | Rôle                                                  | Statut       |
|--------------------|--------------------------------------------------------|--------------|
| `up.sh`            | Lancer les conteneurs (`docker compose up -d`)        | ✅ à enrichir |
| `down.sh`          | Arrêter les conteneurs (`docker compose down`)        | ✅ à enrichir |
| `validate.sh`      | Vérifier que l’instance R2R est fonctionnelle         | ✅ robuste    |
| `common_config.sh` | Définir les chemins de base et config du projet       | ✅ bon point de départ |
| `install.sh`       | Préparer la machine (admin user, pipx, uv, secrets)   | ✅ à harmoniser avec HOWTO |
| `snapshot.sh`      | Créer une archive compressée des données R2R          | 🔲 à écrire   |
| `rollback.sh`      | Restaurer une archive, avec rollback automatique      | 🔲 à écrire   |

---

## 🔧 Étapes détaillées

### 1. Compléter la configuration centralisée

- [x] `common_config.sh` contient `ROOT_DIR`, `COMPOSE_BASE`, etc.
- [ ] Ajouter `VOLUMES_DIR` (ex: `${ROOT_DIR}/volumes`)
- [ ] Ajouter `ARCHIVES_DIR="${VOLUMES_DIR}/archived/R2R"`
- [ ] Ajouter `ACTIVE_DIR="${VOLUMES_DIR}/active/R2R"`

---

### 2. Renforcer `up.sh` et `down.sh`

**`up.sh`**
- [ ] `set -euo pipefail`
- [ ] Vérification que Docker est installé
- [ ] Affichage de `docker compose ps`

**`down.sh`**
- [ ] Idem, avec affichage des volumes

---

### 3. Fiabiliser `validate.sh`

- [x] Implémente un test `--quick`
- [ ] Ajouter un mode `--verbose` qui affiche les logs
- [ ] Ajouter test explicite sur port ouvert

---

### 4. Script `snapshot.sh`

**Responsabilités :**
- Vérifier l'état de R2R (`validate.sh --quick`)
- Arrêter R2R (`down.sh`)
- Archiver `active/R2R` → `archived/R2R/snapshot_YYYY-MM-DD.tar.gz`
- Relancer R2R (`up.sh`)
- Revalider (`validate.sh --quick`)

**Codes de sortie :**
- `0` succès
- `1` état initial invalide
- `2` état final invalide

---

### 5. Script `rollback.sh`

**Responsabilités :**
- Vérifier et décompresser une archive
- Sauvegarder `active/R2R` dans `backup_rollback/`
- Remplacer `active/R2R` par l’archive décompressée
- Relancer R2R
- Si échec → rollback, revalider

**Codes de sortie :**
- `0` Succès
- `1` Archive absente
- `2` Archive corrompue
- `3` Contenu invalide
- `4` Rollback effectué, mais update échoué
- `5` Échec complet

---

## 🧪 Tests à réaliser

| Test                                                       | Statut  |
|------------------------------------------------------------|---------|
| Snapshot sur instance saine                                | 🔲      |
| Snapshot sur instance invalide                             | 🔲      |
| Restauration avec archive valide                           | 🔲      |
| Restauration avec archive invalide                         | 🔲      |
| Restauration échouée suivie d’un rollback réussi           | 🔲      |
| Restauration échouée suivie d’un rollback échoué (edge)    | 🔲      |

---

## 📘 Documentation à inclure

- [ ] Ajouter section snapshot/rollback dans `HOWTO-deploy.md`
- [ ] Inclure instructions de test manuel
- [ ] Lister les dépendances (tar, docker, curl...)

---

## 📌 Priorités immédiates

1. Ajouter `VOLUMES_DIR` et chemins dérivés dans `common_config.sh`
2. Écrire et tester `snapshot.sh`
3. Écrire `rollback.sh` avec validations et logs
4. Enrichir `up.sh` / `down.sh` pour robustesse
5. Mettre à jour la documentation

---

