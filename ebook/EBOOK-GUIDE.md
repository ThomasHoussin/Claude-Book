# Guide de Generation d'Ebook

Ce guide explique comment generer des ebooks (EPUB, PDF, MOBI) a partir du projet
"Le Club des Cinq et le Phare Abandonne".

## Prerequis

### Logiciels requis

1. **Pandoc** (obligatoire)
   - Telecharger: https://pandoc.org/installing.html
   - Version recommandee: 3.0 ou superieur
   - Verifier l'installation: `pandoc --version`

2. **PowerShell** (inclus avec Windows)
   - Version 5.1 ou superieur
   - Verifier: `$PSVersionTable.PSVersion`

3. **Module powershell-yaml** (recommande)
   ```powershell
   Install-Module powershell-yaml -Scope CurrentUser
   ```

4. **Pour PDF** (optionnel)
   - XeLaTeX: https://miktex.org/ (Windows) ou TeX Live
   - Permet de generer des PDF avec typographie francaise correcte

5. **Pour MOBI** (optionnel)
   - Calibre: https://calibre-ebook.com/
   - Fournit `ebook-convert` pour la conversion EPUB -> MOBI

---

## Structure des fichiers

```
ebook/
├── config/
│   └── book.yaml          <- Configuration principale
├── assets/
│   ├── images/
│   │   ├── cover.jpg      <- Image de couverture
│   │   └── headers/       <- Images d'en-tete de chapitre
│   └── fonts/             <- Polices personnalisees (optionnel)
├── templates/
│   └── epub.css           <- Styles EPUB
├── build/                 <- Fichiers generes (gitignore)
└── build-ebook.ps1        <- Script de generation
```

---

## Utilisation rapide

### Generer un EPUB

```powershell
cd "d:\code-workspace\Claude Book\ebook"
.\build-ebook.ps1
```

### Generer un PDF

```powershell
.\build-ebook.ps1 -Format pdf
```

### Generer tous les formats actives

```powershell
.\build-ebook.ps1 -Format all
```

### Mode verbeux (pour debogage)

```powershell
.\build-ebook.ps1 -Verbose
```

### Nettoyer et reconstruire

```powershell
.\build-ebook.ps1 -Clean
```

### Mode simulation (sans generer)

```powershell
.\build-ebook.ps1 -DryRun
```

---

## Configuration de l'image de couverture

### Specifications recommandees

| Propriete | Valeur recommandee |
|-----------|-------------------|
| Dimensions | 1600 x 2400 pixels |
| Ratio | 2:3 (portrait) |
| Format | JPEG ou PNG |
| Taille max | 5 MB |
| Resolution | 300 DPI (pour impression) |

### Etapes

1. Creer ou obtenir une image de couverture
2. Redimensionner aux dimensions recommandees
3. Sauvegarder dans `ebook/assets/images/cover.jpg`
4. Verifier que `book.yaml` contient:
   ```yaml
   cover:
     enabled: true
     image: "assets/images/cover.jpg"
   ```

### Outils recommandes

- **GIMP** (gratuit): https://www.gimp.org/
- **Canva** (en ligne): https://www.canva.com/
- **Photoshop** (payant)

### Conseils de design

- Texte lisible en miniature (titre visible a 100px de large)
- Contraste eleve entre le texte et l'arriere-plan
- Eviter les details fins qui disparaissent en petit format
- Tester sur differents appareils (Kindle, telephone, tablette)

---

## Images d'en-tete de chapitre

### Activation

Dans `book.yaml`:

```yaml
chapters:
  header_images:
    enabled: true
    default: ""  # Image par defaut pour tous les chapitres
    mapping:
      chapitre-01: "assets/images/headers/chapitre-01.jpg"
      chapitre-12: "assets/images/headers/climax.jpg"
```

### Specifications

| Propriete | Valeur recommandee |
|-----------|-------------------|
| Dimensions | 800 x 300 pixels |
| Ratio | Large (paysage) |
| Format | JPEG |
| Taille | < 500 KB par image |

### Structure des fichiers

```
ebook/assets/images/headers/
├── chapitre-01.jpg
├── chapitre-02.jpg
├── ...
└── chapitre-18.jpg
```

### Conseils

- Utiliser des images evocatrices du contenu du chapitre
- Maintenir une coherence visuelle (meme style, palette)
- Images decoratives, pas informatives (accessibilite)
- Tester sur liseuse e-ink (contraste important)

---

## Personnalisation des styles CSS

### Fichier de styles

Le fichier `templates/epub.css` controle l'apparence du livre.

### Modifications courantes

#### Changer la police principale

```css
body {
    font-family: "Palatino Linotype", Palatino, Georgia, serif;
}
```

#### Ajuster l'interligne

```css
body {
    line-height: 1.8;  /* Plus d'espace */
}
```

#### Style des titres de chapitre

```css
h1 {
    font-size: 2em;
    font-style: italic;
    border-bottom: 1px solid #333;
    padding-bottom: 0.5em;
}
```

#### Personnaliser les separateurs de scene

```css
hr::before {
    content: "~ ~ ~";  /* Au lieu de * * * */
}
```

### Test des styles

1. Generer l'EPUB
2. Ouvrir dans Calibre (F7 pour voir le HTML)
3. Ajuster le CSS
4. Regenerer et retester

---

## Generation PDF

### Prerequis

- XeLaTeX installe (MiKTeX ou TeX Live)
- Polices Unicode installees

### Activation

Dans `book.yaml`:

```yaml
output:
  formats:
    pdf:
      enabled: true
      engine: "xelatex"
      paper_size: "a5"
```

### Options de mise en page

```yaml
pdf:
  paper_size: "a5"     # a4, a5, letter, 6x9in
  margin:
    top: "2.5cm"
    bottom: "2.5cm"
    left: "2cm"
    right: "2cm"
  font:
    main: "Linux Libertine O"
    size: "11pt"
  line_spacing: 1.4
```

### Polices recommandees pour le francais

- Linux Libertine O (gratuit, excellent support Unicode)
- EB Garamond (gratuit, style classique)
- Palatino Linotype (inclus Windows)

---

## Generation MOBI (Kindle)

### Prerequis

- Calibre installe
- EPUB genere au prealable

### Processus

1. Le script genere d'abord l'EPUB
2. Puis convertit en MOBI via `ebook-convert`

### Activation

```yaml
output:
  formats:
    mobi:
      enabled: true
```

### Limitations

- MOBI est un format obsolete (Amazon recommande maintenant KF8/AZW3)
- Certains styles CSS ne sont pas supportes
- Les images de grande taille peuvent etre compressees

---

## Configuration avancee

### Modifier les metadonnees

Dans `book.yaml`, section `metadata`:

```yaml
metadata:
  title: "Le Club des Cinq et le Phare Abandonne"
  subtitle: "Une aventure en Bretagne"
  author: "Votre Nom"
  language: "fr-FR"
  publisher: "Ma Maison d'Edition"
  date: "2024"
  rights: "Tous droits reserves"
  isbn: "978-X-XXXX-XXXX-X"
  description: |
    Une description de votre livre pour les catalogues
    et les liseuses.
```

### Changer le nom du fichier de sortie

```yaml
output:
  filename: "mon-livre"  # Produira mon-livre.epub
```

### Ajouter une dedicace

```yaml
front_matter:
  include:
    dedication: true
  dedication_text: "A tous les amateurs d'aventure"
```

### Ajouter une epigraphe

```yaml
front_matter:
  include:
    epigraph: true
  epigraph:
    text: "L'aventure est au coin de la rue."
    attribution: "Auteur Inconnu"
```

---

## Depannage

### Erreur: "Pandoc n'est pas installe"

```
Solution: Installer Pandoc et redemarrer PowerShell
Lien: https://pandoc.org/installing.html
```

### Erreur: "powershell-yaml module not found"

```powershell
Install-Module powershell-yaml -Scope CurrentUser
```

Le script fonctionnera quand meme avec une configuration par defaut.

### Erreur: "Aucun fichier de chapitre trouve"

```
Verifier:
1. Le chemin dans book.yaml (chapters.source_dir)
2. Le pattern de fichiers (chapters.pattern)
3. Que les fichiers existent dans story/chapters/
```

### Erreur: "Image de couverture introuvable"

```
Verifier:
1. Le fichier existe dans ebook/assets/images/
2. Le chemin dans book.yaml est correct
3. L'extension est correcte (.jpg vs .jpeg)
```

L'EPUB sera genere sans couverture si l'image est absente.

### L'EPUB ne s'affiche pas correctement

```
1. Valider l'EPUB: https://validator.idpf.org/
2. Tester dans Calibre (plus tolerant)
3. Verifier le CSS pour les erreurs de syntaxe
```

### Le PDF a des caracteres manquants

```
Solution: Utiliser XeLaTeX avec une police Unicode
Verifier que la police est installee sur le systeme
```

### Script bloque par politique d'execution

```powershell
# Executer en tant qu'administrateur:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Ou lancer le script avec:
powershell -ExecutionPolicy Bypass -File build-ebook.ps1
```

---

## Validation de l'EPUB

### Validateur en ligne

https://validator.idpf.org/

### Calibre (local)

1. Ouvrir l'EPUB dans Calibre
2. Clic droit -> Modifier le livre
3. Outils -> Verifier le livre

### epubcheck (ligne de commande)

```bash
java -jar epubcheck.jar build/le-club-des-cinq-phare.epub
```

---

## Bonnes pratiques

### Avant la generation finale

- [ ] Relire tous les chapitres pour les erreurs typographiques
- [ ] Verifier la coherence des titres de chapitres
- [ ] Tester sur plusieurs appareils/applications
- [ ] Valider l'EPUB avec un validateur officiel

### Metadonnees importantes

- [ ] Titre exact et orthographe correcte
- [ ] Nom d'auteur correct
- [ ] Langue definie (fr-FR)
- [ ] Description pour les catalogues

### Images

- [ ] Couverture de haute qualite
- [ ] Toutes les images optimisees (taille < 500 KB)
- [ ] Texte alternatif pour l'accessibilite

---

## Ressources supplementaires

- **Documentation Pandoc**: https://pandoc.org/MANUAL.html
- **EPUB 3 Specification**: https://www.w3.org/publishing/epub3/
- **Kindle Publishing Guidelines**: https://kdp.amazon.com/en_US/help/topic/G200645400
- **IDPF EPUB Validator**: https://validator.idpf.org/
- **Calibre**: https://calibre-ebook.com/
