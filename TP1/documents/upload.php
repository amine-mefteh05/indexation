<?php
$conn = new mysqli("localhost", "root", "", "test");

if ($conn->connect_error) {
    $status = "error";
    $message = "Erreur connexion : " . $conn->connect_error;
} else {
    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $descr = $_POST['description'];
        $mc = $_POST['keywords'];

        if (isset($_FILES["document"]) && $_FILES["document"]["error"] == 0) {
            $fileName = $_FILES["document"]["name"];
            $fileTmp = $_FILES["document"]["tmp_name"];
            $uploadDir = "uploads/";
            $filePath = $uploadDir . basename($fileName);
            
            if(!is_dir($uploadDir)){
                mkdir($uploadDir, 0777, true);
            }

            if (move_uploaded_file($fileTmp, $filePath)) {
                $stmt = $conn->prepare("INSERT INTO documents (descr, adress, mc) VALUES (?, ?, ?)");
                $stmt->bind_param("sss", $descr, $filePath, $mc);
                $stmt->execute();
                $stmt->close();

                $status = "success";
                $message = "Document ajouté avec succès !";
            } else {
                $status = "error";
                $message = "Erreur lors de l'upload du fichier.";
            }
        } else {
            $status = "error";
            $message = "Veuillez sélectionner un fichier valide.";
        }
    } else {
        $status = "error";
        $message = "Requête invalide.";
    }
    $conn->close();
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Résultat de l'Upload | Portail</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
            --bg-gradient-1: #0f172a;
            --bg-gradient-2: #1e1b4b;
            --bg-shape-1: #4338ca;
            --bg-shape-2: #818cf8;
            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --success-color: #10b981;
            --error-color: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-1), var(--bg-gradient-2));
            color: var(--text-main);
            min-height: 100vh;
            display: flex; justify-content: center; align-items: center;
            overflow: hidden; position: relative;
        }
        .shape { position: absolute; filter: blur(80px); z-index: 0; opacity: 0.5; animation: float 20s infinite ease-in-out alternate; }
        .shape-1 { width: 400px; height: 400px; background: var(--bg-shape-1); top: -100px; left: -100px; border-radius: 50%; }
        .shape-2 { width: 300px; height: 300px; background: var(--bg-shape-2); bottom: -50px; right: -50px; border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; animation-delay: -5s; }
        @keyframes float {
            0% { transform: translate(0, 0) rotate(0deg) scale(1); }
            50% { transform: translate(50px, 30px) rotate(10deg) scale(1.1); }
            100% { transform: translate(-30px, 50px) rotate(-10deg) scale(0.9); }
        }
        .container {
            position: relative; z-index: 1; background: var(--glass-bg); backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px); padding: 50px; border-radius: 24px;
            border: 1px solid var(--glass-border); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            width: 100%; max-width: 450px; text-align: center;
            transform: translateY(20px); opacity: 0; animation: slideUp 0.8s ease forwards;
        }
        @keyframes slideUp { to { transform: translateY(0); opacity: 1; } }
        
        .icon { font-size: 4rem; margin-bottom: 20px; }
        .status-success { color: var(--success-color); }
        .status-error { color: var(--error-color); }
        
        h2 { font-size: 1.8rem; font-weight: 700; margin-bottom: 15px; }
        p { color: var(--text-muted); font-size: 1.1rem; margin-bottom: 30px; }
        .link a {
            display: inline-block; padding: 12px 24px; background: rgba(255,255,255,0.1);
            color: white; text-decoration: none; border-radius: 12px; font-weight: 600;
            transition: all 0.3s ease;
        }
        .link a:hover { background: rgba(255,255,255,0.2); transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="shape shape-1"></div>
    <div class="shape shape-2"></div>
    <div class="container">
        <?php if($status == "success"): ?>
            <div class="icon status-success">✓</div>
            <h2>Succès</h2>
        <?php else: ?>
            <div class="icon status-error">✕</div>
            <h2>Erreur</h2>
        <?php endif; ?>
        
        <p><?php echo htmlspecialchars($message); ?></p>
        
        <div class="link">
            <a href="index.html">← Retour à l'insertion</a>
        </div>
    </div>
</body>
</html>
