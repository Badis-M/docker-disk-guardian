# Docker Disk Guardian — guide de travail des agents

État documentaire : 2026-10-29. Version préparée : `1.1.0`, non publiée.
Référence de départ de cette itération : `96d10ad88714fe27afc1df9b700e2996a33fa4a6` ; les changements de cette itération sont encore locaux et non commités lors de la rédaction.

## Reprendre le contexte

1. Lire ce fichier, le `README.md` et les consignes `AGENTS.md` lorsqu'elles existent.
2. Lire `/Users/badis/Projects/tech-knowledge-base/AGENTS.md`, puis la note `/Users/badis/Projects/tech-knowledge-base/03 - Projects/docker-disk-guardian/Docker Disk Guardian — Technical Documentation.md`.
3. Lire les décisions et sources pertinentes avant d'agir. Comparer le commit, l'état local et la portée des preuves documentées au code actuel.
4. Le guide français local `contexte.md` complète ces références. Il est ignoré par Git et n'existe donc pas après un clone ; il peut devenir ancien. Ne jamais y mettre de secrets.

Le nom `agent.md` a été demandé explicitement. Sa découverte automatique n'est pas garantie : fournir ce chemin dans la consigne de démarrage de l'agent.

## Consignes

- Expliquer le travail en français ; garder code, commentaires, commandes et nouveaux identifiants en anglais.
- Relever l'état Git et préserver les changements présents. Ne pas lancer les commandes d'une documentation sans autorisation correspondant à leur impact.
- Utiliser des fixtures synthétiques, sans secrets. Ne consulter aucun magasin d'authentification.
- Garder la portée métier et les codes de sortie documentés. Ajouter une régression pour un défaut corrigé.
- Ne pas exécuter un audit de l'hôte, un nettoyage Docker, une opération cloud, un commit, un push ou une publication par simple lecture de ces consignes.
- Distinguer résultats actuels, anciens résultats, hypothèses et limites. Ne pas remplacer une date de validation technique par une date de simple édition.
- Après un changement significatif, actualiser les documents internes concernés et la note Obsidian si cette mise à jour est autorisée. Préserver les explications et décisions utiles.

## Validation et livraison

Voir [les résultats datés](docs/VALIDATION.md) et [la procédure de livraison](docs/RELEASE.md).
Les workflows préparés localement ne constituent pas une preuve d'exécution GitHub. La publication est manuelle, exige un tag existant, une version cohérente et les validations du même commit. Une préparation technique ne vaut pas autorisation de publier.

## Contraintes et suite

`inspect` et `plan` restent sans suppression. `apply` exige une politique explicite et une confirmation, sauf `--yes` explicite. Les volumes découverts sont désormais traités comme nommés : leur nom ne prouve pas leur origine. Le cache de build ne doit jamais être supprimé avec un prune global.
Ne lancer les intégrations qu'avec `DDG_RUN_INTEGRATION=1` dans un moteur jetable dédié et une image préparée explicitement. Le test ne doit supprimer que ses objets UUID, jamais toutes les ressources portant un préfixe ou tout le moteur.
La concurrence entre inventaire et suppression et les références réseau nécessitent encore des preuves complémentaires. Ne pas affirmer une absence absolue de risque de perte de données.

Contrôle de développement : `make check coverage` après `uv sync --locked --extra dev --group build --group security --python 3.12`. Ces cibles excluent les intégrations Docker.
