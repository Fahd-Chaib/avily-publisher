# avily-publisher

Robot de publication d'AVILY. Claude dépose les vidéos montées et leurs textes (SEO compris) dans `queue/`.
Une GitHub Action tourne toutes les 30 minutes et :

| Plateforme | Ce que fait le robot |
|---|---|
| YouTube Shorts | envoie la vidéo dès qu'elle est dans la file, en privé avec date de publication : YouTube la publie lui-même à l'heure prévue |
| Instagram Reels | publie à l'heure prévue (la vidéo est servie par GitHub Pages) |
| TikTok | dépose la vidéo en **brouillon** dans ta boîte de réception TikTok à l'heure prévue (API non auditée) ; tu ajoutes un son et tu publies |

Un post en retard de plus de 6 h n'est pas publié (pour éviter une rafale de posts après une panne).
Quand tout est fait, le post part dans `archive/` et la vidéo est supprimée.
En cas d'erreur, l'exécution échoue et GitHub t'envoie un e-mail.

## Format d'un post (`queue/<date>_<nom>/post.json`)

```json
{
  "slug": "n26_caramel",
  "publish_at": "2026-10-13T20:00:00",
  "timezone": "Africa/Casablanca",
  "platforms": ["youtube", "instagram", "tiktok"],
  "instagram": {"caption": "…"},
  "tiktok": {"caption": "…"},
  "youtube": {"title": "… #Shorts", "description": "…", "tags": ["…"]}
}
```

## Mise en place (une seule fois)

### 0. Le dépôt
- Dépôt **public** (GitHub Pages gratuit) : les vidéos y sont visibles quelques heures avant leur sortie, les clés restent dans les secrets.
- Settings → Pages → Source : *Deploy from a branch* → `main` / `(root)`.
- Settings → Actions → General → Workflow permissions : *Read and write*.

### 1. Instagram (≈ 20 min)
1. Compte Instagram en mode Professionnel (déjà fait).
2. https://developers.facebook.com → *Créer une app* → cas d'usage « Instagram » → *API avec connexion Instagram*.
3. Dans *Rôles de l'app*, ajouter ton compte Instagram comme testeur, puis accepter l'invitation dans Instagram (Paramètres → Apps et sites web).
4. *Générer un jeton d'accès* pour @avily.ma (permissions `instagram_business_basic`, `instagram_business_content_publish`).
5. Secrets du dépôt (Settings → Secrets and variables → Actions) :
   - `IG_ACCESS_TOKEN` : le jeton (longue durée, 60 jours ; le robot le renouvelle seul grâce à `GH_PAT`)
   - `IG_USER_ID` : l'identifiant du compte Instagram affiché à côté du jeton

### 2. YouTube (≈ 20 min)
1. https://console.cloud.google.com → nouveau projet « avily-publisher » → activer **YouTube Data API v3**.
2. *Écran de consentement OAuth* : type Externe, ajouter ton e-mail comme utilisateur test, puis **Publier l'application (En production)**. En mode Test, l'autorisation expire au bout de 7 jours.
3. *Identifiants* → ID client OAuth → type « Application de bureau ».
4. Obtenir le jeton de rafraîchissement : `python tools/youtube_auth.py <client_id> <client_secret>` sur ton ordinateur, connexion avec le compte de la chaîne AVILY.
5. Secrets : `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

### 3. Renouvellement automatique des jetons
- Créer un *fine-grained token* GitHub limité à ce dépôt, permission **Secrets : Read and write**.
- Secret : `GH_PAT`.

### 4. TikTok (brouillons, optionnel)
1. https://developers.tiktok.com → créer une app → produits *Login Kit* + *Content Posting API* (scope `video.upload`).
2. Autoriser l'app avec @avily.ma pour obtenir un *refresh token*.
3. Secrets : `TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN`.

Sans ces secrets, TikTok est simplement ignoré (le reste fonctionne).

## Tester sans rien publier
Actions → *Publier AVILY* → *Run workflow* → cocher « Test sans rien publier ».
