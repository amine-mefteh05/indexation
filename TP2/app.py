import os
import time
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import moteur_recherche_images as mri

app = Flask(__name__, static_folder=".")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")

images_base = []
descripteurs_base = []
noms_base = []

def load_db():
    global images_base, descripteurs_base, noms_base
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    print(f"Chargement de la base d'images depuis le dossier: {IMAGE_DIR}")
    images_base, descripteurs_base, noms_base = mri.charger_base(IMAGE_DIR)

# Load the DB when the server starts
load_db()

def get_desc_sims(a, b):
    # Retrieve the sizes of the descriptors
    n_couleur = 96
    n_lbp     = 10
    n_glcm    = 4
    
    bloc_c = slice(0, n_couleur)
    bloc_l = slice(n_couleur, n_couleur + n_lbp)
    bloc_g = slice(n_couleur + n_lbp, n_couleur + n_lbp + n_glcm)
    bloc_h = slice(n_couleur + n_lbp + n_glcm, None)

    d_couleur = mri.distance_chi2(a[bloc_c], b[bloc_c])
    d_lbp     = mri.distance_euclidienne(a[bloc_l], b[bloc_l])
    d_glcm    = mri.distance_euclidienne(a[bloc_g], b[bloc_g])
    d_hog     = mri.distance_cosinus(a[bloc_h], b[bloc_h])
    
    # Simple heuristic to map distance to a similarity [0, 1] for the UI
    sim_couleur = max(0.0, min(1.0, 1.0 - d_couleur / 2.0))
    sim_lbp     = max(0.0, min(1.0, 1.0 - d_lbp / 1.5))
    sim_glcm    = max(0.0, min(1.0, 1.0 - d_glcm / 1.5))
    sim_hog     = max(0.0, min(1.0, 1.0 - d_hog / 2.0))
    
    return {
        "Color": float(sim_couleur),
        "LBP":   float(sim_lbp),
        "GLCM":  float(sim_glcm),
        "HOG":   float(sim_hog)
    }

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "image_search_engine.html")

@app.route("/api/stats", methods=["GET"])
def get_stats():
    dims = len(descripteurs_base[0]) if descripteurs_base else 0
    return jsonify({
        "db_size": len(images_base),
        "dims": dims
    })

@app.route("/api/descriptors", methods=["GET"])
def get_descriptors():
    return jsonify(["HSV", "LBP", "GLCM", "HOG"])

@app.route("/api/index", methods=["POST"])
def reindex():
    load_db()
    return jsonify({"indexed": len(images_base)})

@app.route("/api/search", methods=["POST"])
def search():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
        
    start_time = time.time()
    
    file = request.files["image"]
    method = request.form.get("method", "combinee")
    k = int(request.form.get("k", 5))
    
    # Read the image from bytes
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img_req = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img_req is None:
        return jsonify({"error": "Invalid image"}), 400
        
    # Extract features for the query image
    try:
        desc_req = mri.extraire_descripteurs(img_req)
    except Exception as e:
        return jsonify({"error": f"Error extracting descriptors: {str(e)}"}), 500
    
    # Read weights (only used if methode == 'combinee')
    w_color = float(request.form.get("w_color", 0.4))
    w_lbp   = float(request.form.get("w_lbp", 0.2))
    w_glcm  = float(request.form.get("w_glcm", 0.1))
    w_hog   = float(request.form.get("w_hog", 0.3))
    
    all_distances = []
    
    for i, d in enumerate(descripteurs_base):
        if method == "euclidienne":
            dist = mri.distance_euclidienne(desc_req, d)
        elif method == "cosinus":
            dist = mri.distance_cosinus(desc_req, d)
        elif method == "chi2":
            dist = mri.distance_chi2(desc_req, d)
        else: # combinee
            dist = mri.distance_combinee(desc_req, d, w_color, w_lbp, w_glcm, w_hog)
            
        all_distances.append(dist)
        
    # Get top-k indices
    indices = np.argsort(all_distances)[:k]
    
    results = []
    for rank, idx in enumerate(indices):
        d_base = descripteurs_base[idx]
        sims = get_desc_sims(desc_req, d_base)
        
        # Encoding thumbnail to base64
        thumb_img = images_base[idx]
        # Resize thumbnail down to speed up the network transfer
        h, w = thumb_img.shape[:2]
        if h > 150 or w > 150:
            scale = 150 / max(h, w)
            thumb_img = cv2.resize(thumb_img, (int(w * scale), int(h * scale)))
            
        _, buffer = cv2.imencode(".jpg", thumb_img)
        thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")
        
        results.append({
            "rank": rank + 1,
            "name": noms_base[idx],
            "distance": float(all_distances[idx]),
            "thumbnail": thumb_b64,
            "category": "Image",
            "desc_sims": sims
        })
        
    elapsed = time.time() - start_time
    best_score = float(all_distances[indices[0]]) if len(indices) > 0 else 0.0
    
    return jsonify({
        "results": results,
        "db_size": len(images_base),
        "dims": len(desc_req),
        "elapsed": round(elapsed, 2),
        "best_score": round(best_score, 4)
    })

if __name__ == "__main__":
    # Ensure images folder exists
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        
    print("[INFO] Demarrage du serveur API de recherche d'images...")
    print("[INFO] Interface web disponible sur: http://127.0.0.1:5000/")
    app.run(host="127.0.0.1", port=5000, debug=True)
