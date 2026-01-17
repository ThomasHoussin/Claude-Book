# Techniques de réécriture pour augmenter la perplexité

Guide pratique pour transformer des phrases prévisibles en formulations plus originales tout en préservant le sens.

## Principe fondamental

La perplexité mesure la "surprise" d'un modèle de langage. Une phrase prévisible = perplexité basse = pattern IA détectable.

**Objectif** : Rendre le texte moins prévisible sans perdre clarté ni cohérence.

---

## 1. Verbalized Sampling (Technique de première passe)

Avant d'appliquer les autres techniques, génère 3 versions alternatives de la phrase suspecte en échantillonnant depuis les queues de distribution.

**Processus** :
1. Prendre la phrase suspecte (perplexité basse)
2. Prompt : "Génère 3 formulations alternatives de cette phrase, échantillonnées depuis les queues de distribution (probabilité < 0.3)"
3. Sélectionner l'alternative la plus naturelle qui préserve le sens
4. Si aucune ne convient, passer aux techniques 2-9

| Original (ppl ~8) | Alternative 1 (p<0.3) | Alternative 2 (p<0.3) | Alternative 3 (p<0.3) |
|-------------------|----------------------|----------------------|----------------------|
| Elle ressentait une profonde tristesse | Quelque chose de mouillé et lourd s'était lové dans sa gorge | Sa tristesse avait un goût de fer et de lait tourné | Un froid de cave lui remontait de l'estomac |

**Pourquoi ça marche** : Les phrases à basse perplexité sont "mode-collapsed" — le modèle a produit sa sortie la plus typique. L'échantillonnage des queues accède à la distribution complète apprise en pretraining.

**Quand l'utiliser** (par type de détection) :

| Type détecté | Stratégie |
|--------------|-----------|
| `low_perplexity` | ✅ VS ou Techniques 2-9 |
| `low_std` (paragraphe monotone) | Mix : VS sur 1-2 phrases + Techniques 2-9 sur les autres |
| `adjacent_low` / `low_ppl_density` | Mix : VS sur 1-2 phrases + Techniques 2-9 sur 2-3 autres |
| `forbidden_word` | Technique 4 uniquement (swap vocabulaire rare) |

---

## 2. Inversion syntaxique

Changer l'ordre canonique sujet-verbe-complément.

| Original (prévisible) | Réécrit (moins prévisible) |
|----------------------|---------------------------|
| Il courut vers la porte | Vers la porte, il s'élança |
| Elle était terrifiée | La terreur la paralysait |
| Le soleil se couchait | Déclinait le soleil, orange et las |
| Ils décidèrent de partir | Partir. C'était décidé. |

**Quand l'utiliser** : Phrases déclaratives simples, descriptions d'action.

---

## 3. Fragmentation

Couper les phrases longues en segments courts et percutants.

| Original | Réécrit |
|----------|---------|
| Il avait peur mais il savait qu'il devait continuer malgré tout | La peur. Omniprésente. Mais il devait continuer. |
| La maison était vieille et ses volets claquaient dans le vent | Une vieille maison. Des volets qui claquent. Le vent. |

**Quand l'utiliser** : Moments de tension, descriptions atmosphériques, pensées intérieures.

---

## 4. Vocabulaire rare

Remplacer les mots courants par des synonymes moins fréquents.

| Mot courant | Alternatives rares |
|-------------|-------------------|
| regarder | scruter, darder les yeux, couver du regard |
| marcher | arpenter, déambuler, fouler |
| dire | susurrer, lâcher, articuler, grommeler |
| peur | effroi, épouvante, transe |
| bruit | rumeur, tumulte, vacarme, brouhaha |
| beau | splendide, saisissant, fastueux |
| vieux | vétuste, décrépit, séculaire |

**Attention** : Ne pas surcharger. Un mot rare par phrase maximum.

---

## 5. Rythme cassé

Alterner phrases très courtes et plus longues pour créer un rythme imprévisible.

| Original (rythme uniforme) | Réécrit (rythme cassé) |
|---------------------------|------------------------|
| Elle ouvrit la porte. Elle entra dans la pièce. Elle regarda autour d'elle. | Elle ouvrit la porte. La pièce l'attendait, sombre et silencieuse comme une tombe oubliée. Un regard circulaire. Personne. |

**Pattern efficace** : Court - Long - Très court - Moyen

---

## 6. Sensorialité

Ajouter des détails sensoriels spécifiques (vue, son, toucher, odeur, goût).

| Original (abstrait) | Réécrit (sensoriel) |
|--------------------|---------------------|
| Il faisait froid | L'air lui mordait les joues, acre et métallique |
| La pièce était sale | Une odeur de moisi et de vieux papier, des toiles d'araignée dans les coins |
| Elle avait faim | Son estomac gargouillait, la salive lui montait aux lèvres |

**Quand l'utiliser** : Descriptions de lieux, états physiques des personnages.

---

## 7. Voix du personnage

Intégrer des tics de langage, expressions ou pensées propres au personnage.

**Exemples par archétype :**

| Type de personnage | Formulations caractéristiques |
|-------------------|------------------------------|
| Leader prudent | "Il fallait réfléchir. Pas de précipitation." |
| Impulsif | "Fichtre !", interjections, phrases incomplètes |
| Intellectuel | Métaphores, références, parenthèses explicatives |
| Enfant | Comparaisons naïves, vocabulaire simple mais images fortes |

**Quand l'utiliser** : Dialogues, monologues intérieurs, narration focalisée.

---

## 8. Détournement de cliché

Reprendre une expression figée et la tordre.

| Cliché | Détournement |
|--------|--------------|
| blanc comme neige | blanc comme un os rongé |
| le temps passe vite | le temps s'écoulait, visqueux |
| son cœur battait fort | son cœur cognait contre ses côtes comme un prisonnier |

---

## 9. Ellipse narrative

Supprimer les transitions attendues, laisser le lecteur combler.

| Original (explicite) | Réécrit (ellipse) |
|---------------------|-------------------|
| Il monta l'escalier et arriva devant la porte. Il hésita puis frappa. | L'escalier. La porte. Ses phalanges contre le bois. |

---

## Combinaisons recommandées

Pour une phrase très suspecte (ppl < 10), combiner plusieurs techniques :

1. **Inversion + Vocabulaire rare**
   - Original : "Il regarda la mer avec tristesse"
   - Réécrit : "La mer, il la scrutait. Mélancolique."

2. **Fragmentation + Sensorialité**
   - Original : "La nuit tombait et il faisait de plus en plus froid"
   - Réécrit : "La nuit. Un froid qui s'insinuait sous le col, glaçait les doigts."

3. **Voix du personnage + Rythme cassé**
   - Original : "Claude était en colère et ne voulait pas obéir"
   - Réécrit : "Claude serrait les poings. Obéir ? Jamais. Plutôt mourir."

---

## Pièges à éviter

1. **Sur-correction** : Trop de techniques = texte illisible
2. **Perte de sens** : La clarté prime sur l'originalité
3. **Incohérence de voix** : Garder le registre du narrateur/personnage
4. **Rupture de ton** : Ne pas introduire d'humour dans une scène grave
5. **Incises avec tirets cadratins** : Les incises — comme ceci — sont un marqueur IA fréquent. Une incise avec tirets par paragraphe maximum.

---

## Checklist avant validation

- [ ] Le sens original est préservé
- [ ] Le style reste cohérent avec `bible/style.md`
- [ ] Les dialogues sonnent naturels pour le personnage
- [ ] Le rythme global du passage reste fluide
- [ ] Pas de répétition des mêmes techniques
