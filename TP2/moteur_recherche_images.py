"""
TP 2 : Moteur de recherche d'images
Enseignant: Mahmoud Mejdoub

Système de recherche d'images similaires basé sur :
  - Histogramme de couleur (HSV)
  - Descripteur LBP (texture locale)
  - Matrice GLCM (texture statistique)
  - Descripteur HOG (forme / contours)
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern, hog
from skimage.feature import graycomatrix, graycoprops   # skimage >= 0.19
import os
import matplotlib.pyplot as plt
from pathlib import Path


# ─────────────────────────────────────────────
#  1. EXTRACTION DES CARACTÉRISTIQUES
# ─────────────────────────────────────────────

def extraire_histogramme_couleur(img, bins=32):
    """
    Calcule un histogramme de couleur dans l'espace HSV.
    Chaque canal (H, S, V) est normalisé séparément puis concaténé.
    bins=32 offre un bon compromis précision / dimensionnalité.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = []
    for i in range(3):
        h = cv2.calcHist([hsv], [i], None, [bins], [0, 256])
        h = cv2.normalize(h, h).flatten()
        hist.extend(h)
    return np.array(hist)   # taille : 3 * bins = 96


def extraire_lbp(img, P=8, R=1):
    """
    Local Binary Pattern (LBP) : capture la texture locale.
    P = nombre de voisins, R = rayon.
    Méthode 'uniform' → histogramme compact (P+2 bins).
    """
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gris, P, R, method='uniform')
    hist, _ = np.histogram(lbp.ravel(),
                           bins=np.arange(0, P + 3),
                           range=(0, P + 2))
    hist = hist.astype(float)
    hist /= hist.sum() + 1e-7   # normalisation L1
    return hist   # taille : P+2 = 10


def extraire_glcm(img):
    """
    Matrice de cooccurrence (GLCM) : texture statistique.
    Retourne 4 propriétés : contraste, homogénéité, énergie, entropie.
    L'image est réduite à 64 niveaux pour accélérer le calcul.
    """
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gris_64 = (gris // 4).astype(np.uint8)   # 256 → 64 niveaux

    glcm = graycomatrix(gris_64, distances=[1], angles=[0, np.pi/4,
                        np.pi/2, 3*np.pi/4],
                        levels=64, symmetric=True, normed=True)

    contraste  = graycoprops(glcm, 'contrast').mean()
    homogen    = graycoprops(glcm, 'homogeneity').mean()
    energie    = graycoprops(glcm, 'energy').mean()
    entropie   = -np.sum(glcm * np.log2(glcm + 1e-10))

    # Normalisation manuelle pour ramener les valeurs dans [0, 1]
    feats = np.array([contraste, homogen, energie, entropie])
    feats = feats / (np.linalg.norm(feats) + 1e-7)
    return feats   # taille : 4


def extraire_hog(img, taille=(128, 128)):
    """
    Histogram of Oriented Gradients (HOG) : forme et contours.
    L'image est redimensionnée pour obtenir un vecteur de taille fixe.
    """
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gris = cv2.resize(gris, taille)
    fd = hog(gris,
             pixels_per_cell=(16, 16),
             cells_per_block=(2, 2),
             orientations=9,
             block_norm='L2-Hys')
    return fd   # taille fixe selon taille cible


def extraire_descripteurs(img):
    """
    Concatène tous les descripteurs en un seul vecteur caractéristique.
    """
    couleur  = extraire_histogramme_couleur(img)   # 96 dims
    lbp      = extraire_lbp(img)                   # 10 dims
    glcm     = extraire_glcm(img)                  #  4 dims
    hog_feat = extraire_hog(img)                   # variable (fixe par image)
    return np.concatenate([couleur, lbp, glcm, hog_feat])


# ─────────────────────────────────────────────
#  2. CALCUL DES DISTANCES
# ─────────────────────────────────────────────

def distance_euclidienne(a, b):
    """Distance L2 classique."""
    return np.linalg.norm(a - b)


def distance_cosinus(a, b):
    """1 − similarité cosinus (0 = identique, 2 = opposé)."""
    num = np.dot(a, b)
    den = np.linalg.norm(a) * np.linalg.norm(b) + 1e-7
    return 1.0 - num / den


def distance_chi2(a, b):
    """
    Distance Chi-2 : adaptée aux histogrammes normalisés.
    Formule : Σ (a_i − b_i)² / (a_i + b_i + ε)
    """
    return np.sum((a - b) ** 2 / (a + b + 1e-7))


def distance_combinee(a, b,
                      poids_couleur=0.4,
                      poids_lbp=0.2,
                      poids_glcm=0.1,
                      poids_hog=0.3):
    """
    Distance pondérée par blocs de descripteurs.
    Les poids permettent de régler l'importance de chaque type de feature.
    
    Poids par défaut :
      - Couleur  40 % (très discriminante pour des scènes naturelles)
      - HOG      30 % (forme importante pour objets)
      - LBP      20 % (texture locale)
      - GLCM     10 % (texture globale)
    """
    # Tailles des blocs
    n_couleur = 96
    n_lbp     = 10
    n_glcm    = 4

    bloc_c = slice(0, n_couleur)
    bloc_l = slice(n_couleur, n_couleur + n_lbp)
    bloc_g = slice(n_couleur + n_lbp, n_couleur + n_lbp + n_glcm)
    bloc_h = slice(n_couleur + n_lbp + n_glcm, None)

    d_couleur = distance_chi2(a[bloc_c], b[bloc_c])
    d_lbp     = distance_euclidienne(a[bloc_l], b[bloc_l])
    d_glcm    = distance_euclidienne(a[bloc_g], b[bloc_g])
    d_hog     = distance_cosinus(a[bloc_h], b[bloc_h])

    return (poids_couleur * d_couleur +
            poids_lbp    * d_lbp     +
            poids_glcm   * d_glcm    +
            poids_hog    * d_hog)


# ─────────────────────────────────────────────
#  3. CHARGEMENT DE LA BASE D'IMAGES
# ─────────────────────────────────────────────

def charger_base(dossier, extensions=('.jpg', '.jpeg', '.png', '.bmp')):
    """
    Charge toutes les images d'un dossier et calcule leurs descripteurs.
    Retourne : (liste_images, liste_descripteurs, liste_noms_fichiers)
    """
    images, descripteurs, noms = [], [], []

    for fichier in sorted(os.listdir(dossier)):
        if Path(fichier).suffix.lower() not in extensions:
            continue
        chemin = os.path.join(dossier, fichier)
        img = cv2.imread(chemin)
        if img is None:
            print(f"[AVERTISSEMENT] Impossible de lire : {fichier}")
            continue
        images.append(img)
        descripteurs.append(extraire_descripteurs(img))
        noms.append(fichier)
        print(f"  [OK] {fichier} chargée")

    print(f"\n{len(images)} image(s) chargée(s) dans la base.\n")
    return images, descripteurs, noms


# ─────────────────────────────────────────────
#  4. RECHERCHE D'IMAGES SIMILAIRES
# ─────────────────────────────────────────────

def recherche_similaire(img_requete, images_base, descripteurs_base, noms_base,
                        k=5, methode='combinee'):
    """
    Recherche les k images les plus similaires à img_requete.
    
    Paramètres
    ----------
    img_requete        : image OpenCV (BGR)
    images_base        : liste des images de la base
    descripteurs_base  : liste des vecteurs de descripteurs
    noms_base          : liste des noms de fichiers
    k                  : nombre de résultats à retourner
    methode            : 'euclidienne' | 'cosinus' | 'chi2' | 'combinee'
    """
    desc_requete = extraire_descripteurs(img_requete)

    # Sélection de la fonction de distance
    fonctions = {
        'euclidienne': distance_euclidienne,
        'cosinus':     distance_cosinus,
        'chi2':        distance_chi2,
        'combinee':    distance_combinee,
    }
    dist_fn = fonctions.get(methode, distance_combinee)

    # Calcul de toutes les distances
    distances = [dist_fn(desc_requete, d) for d in descripteurs_base]

    # Tri par distance croissante
    indices = np.argsort(distances)[:k]

    # ── Affichage des résultats ──
    cols = k + 1
    fig, axes = plt.subplots(1, cols, figsize=(4 * cols, 4))
    fig.suptitle(f"Méthode : {methode}  |  Top-{k} images similaires",
                 fontsize=14, fontweight='bold')

    # Image requête
    axes[0].imshow(cv2.cvtColor(img_requete, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Requête", fontweight='bold', color='red')
    axes[0].axis('off')

    # Images similaires
    for rang, idx in enumerate(indices):
        axes[rang + 1].imshow(cv2.cvtColor(images_base[idx], cv2.COLOR_BGR2RGB))
        axes[rang + 1].set_title(
            f"#{rang+1}  d={distances[idx]:.3f}\n{noms_base[idx]}",
            fontsize=8
        )
        axes[rang + 1].axis('off')

    plt.tight_layout()
    plt.savefig("resultats_recherche.png", dpi=150, bbox_inches='tight')
    plt.show()
    print("Résultats sauvegardés dans 'resultats_recherche.png'")

    return indices, distances


# ─────────────────────────────────────────────
#  5. ANALYSE COMPARATIVE DES MÉTHODES
# ─────────────────────────────────────────────

def comparer_methodes(img_requete, images_base, descripteurs_base, noms_base, k=3):
    """
    Affiche les résultats des 4 méthodes de distance côte à côte
    pour faciliter l'analyse comparative.
    """
    methodes = ['euclidienne', 'cosinus', 'chi2', 'combinee']
    fonctions = {
        'euclidienne': distance_euclidienne,
        'cosinus':     distance_cosinus,
        'chi2':        distance_chi2,
        'combinee':    distance_combinee,
    }

    desc_req = extraire_descripteurs(img_requete)

    fig, axes = plt.subplots(len(methodes), k + 1,
                             figsize=(4 * (k + 1), 4 * len(methodes)))
    fig.suptitle("Comparaison des méthodes de distance", fontsize=16, fontweight='bold')

    for ligne, methode in enumerate(methodes):
        dist_fn = fonctions[methode]
        distances = [dist_fn(desc_req, d) for d in descripteurs_base]
        indices = np.argsort(distances)[:k]

        # Colonne 0 : image requête
        axes[ligne, 0].imshow(cv2.cvtColor(img_requete, cv2.COLOR_BGR2RGB))
        axes[ligne, 0].set_title(f"[{methode}]\nRequête",
                                 fontweight='bold', color='darkblue', fontsize=9)
        axes[ligne, 0].axis('off')

        for col, idx in enumerate(indices):
            axes[ligne, col + 1].imshow(
                cv2.cvtColor(images_base[idx], cv2.COLOR_BGR2RGB))
            axes[ligne, col + 1].set_title(
                f"#{col+1}  d={distances[idx]:.3f}\n{noms_base[idx]}", fontsize=7)
            axes[ligne, col + 1].axis('off')

    plt.tight_layout()
    plt.savefig("comparaison_methodes.png", dpi=150, bbox_inches='tight')
    plt.show()
    print("Comparaison sauvegardée dans 'comparaison_methodes.png'")


# ─────────────────────────────────────────────
#  6. SCRIPT DE TEST PRINCIPAL
# ─────────────────────────────────────────────

if __name__ == "__main__":

    # ── Paramètres à modifier selon votre configuration ──
    BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
    DOSSIER_BASE  = os.path.join(BASE_DIR, "images")
    IMAGE_REQUETE = os.path.join(BASE_DIR, "requete.jpg")
    K             = 5                  # nombre de résultats à afficher
    METHODE       = "combinee"         # 'euclidienne' | 'cosinus' | 'chi2' | 'combinee'

    # ── Chargement de la base ──
    print("=" * 50)
    print("  Chargement de la base d'images...")
    print("=" * 50)
    images_base, descripteurs_base, noms_base = charger_base(DOSSIER_BASE)

    if len(images_base) == 0:
        print("[ERREUR] Aucune image trouvée dans le dossier :", DOSSIER_BASE)
        exit(1)

    # ── Chargement de l'image requête ──
    img_req = cv2.imread(IMAGE_REQUETE)
    if img_req is None:
        print(f"[ERREUR] Impossible de lire l'image requête : {IMAGE_REQUETE}")
        exit(1)

    print(f"Image requête : {IMAGE_REQUETE}")
    print(f"Taille vecteur descripteur : {extraire_descripteurs(img_req).shape[0]} dims")
    print()

    # ── Recherche ──
    print("=" * 50)
    print(f"  Recherche (méthode={METHODE}, k={K})...")
    print("=" * 50)
    indices, distances = recherche_similaire(
        img_req, images_base, descripteurs_base, noms_base,
        k=K, methode=METHODE
    )

    print("\nRésultats :")
    for rang, idx in enumerate(indices):
        print(f"  #{rang+1}  {noms_base[idx]}  →  distance = {distances[idx]:.4f}")

    # ── Comparaison optionnelle des méthodes ──
    print("\n" + "=" * 50)
    print("  Comparaison des 4 méthodes de distance...")
    print("=" * 50)
    comparer_methodes(img_req, images_base, descripteurs_base, noms_base, k=3)
