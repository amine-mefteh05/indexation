<?php
$conn = new mysqli("localhost", "root", "", "test");

$error = null;
$results = [];

if ($conn->connect_error) {
    $error = "Erreur connexion : " . $conn->connect_error;
} else if (isset($_GET['motcle'])) {
    $motcle = $_GET['motcle'];
    $stmt = $conn->prepare("SELECT descr, adress FROM documents WHERE mc LIKE ? OR descr LIKE ?");
    $search = "%" . $motcle . "%";
    $stmt->bind_param("ss", $search, $search);
    $stmt->execute();
    
    $res = $stmt->get_result();
    while ($row = $res->fetch_assoc()) {
        $results[] = $row;
    }
    $stmt->close();
}
$conn->close();
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Résultats de Recherche | Portail</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #10b981;
            --primary-hover: #059669;
            --bg-gradient-1: #0f172a;
            --bg-gradient-2: #064e3b;
            --bg-shape-1: #059669;
            --bg-shape-2: #34d399;
            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-1), var(--bg-gradient-2));
            color: var(--text-main);
            min-height: 100vh; display: flex; justify-content: center; align-items: center;
            overflow: hidden; position: relative; padding: 20px;
        }
        .shape { position: absolute; filter: blur(80px); z-index: 0; opacity: 0.4; animation: float 20s infinite ease-in-out alternate; }
        .shape-1 { width: 500px; height: 500px; background: var(--bg-shape-1); top: -150px; right: -100px; border-radius: 50%; }
        .shape-2 { width: 400px; height: 400px; background: var(--bg-shape-2); bottom: -100px; left: -50px; border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; animation-delay: -7s; }
        @keyframes float {
            0% { transform: translate(0, 0) rotate(0deg) scale(1); }
            50% { transform: translate(-50px, 40px) rotate(-10deg) scale(1.1); }
            100% { transform: translate(30px, -50px) rotate(10deg) scale(0.9); }
        }
        .container {
            position: relative; z-index: 1; background: var(--glass-bg); backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px); padding: 40px; border-radius: 24px;
            border: 1px solid var(--glass-border); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            width: 100%; max-width: 600px;
            transform: translateY(20px); opacity: 0; animation: slideUp 0.8s ease forwards;
            max-height: 90vh; overflow-y: auto;
        }
        .container::-webkit-scrollbar { width: 8px; }
        .container::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); border-radius: 10px; }
        .container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
        
        @keyframes slideUp { to { transform: translateY(0); opacity: 1; } }
        
        h2 {
            text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 30px;
            background: linear-gradient(to right, #fff, #6ee7b7); -webkit-background-clip: text;
            background-clip: text; -webkit-text-fill-color: transparent;
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5);
            color: #fca5a5; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center;
        }
        
        .empty-state {
            text-align: center; color: var(--text-muted); padding: 30px 0; font-size: 1.1rem;
        }
        
        .result-list {
            display: flex; flex-direction: column; gap: 15px; margin-bottom: 30px;
        }
        
        .result-card {
            background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px; padding: 20px; display: flex; justify-content: space-between;
            align-items: center; transition: all 0.3s ease;
        }
        
        .result-card:hover {
            background: rgba(15, 23, 42, 0.8); transform: translateY(-2px);
            border-color: rgba(16, 185, 129, 0.3); box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        
        .result-info h3 { font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 5px; }
        
        .btn-open {
            background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 10px 20px;
            border-radius: 10px; text-decoration: none; font-weight: 600; transition: all 0.3s ease;
            display: inline-flex; align-items: center; gap: 6px; border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .btn-open:hover { background: var(--primary-color); color: white; }
        
        .link { text-align: center; margin-top: 20px; }
        .link a {
            color: var(--text-muted); text-decoration: none; font-weight: 600;
            transition: all 0.3s ease; display: inline-flex; align-items: center; gap: 8px;
            padding: 8px 16px; border-radius: 20px; background: rgba(255,255,255,0.05);
        }
        .link a:hover { color: white; background: rgba(255,255,255,0.1); transform: translateY(-1px); }
    </style>
</head>
<body>
    <div class="shape shape-1"></div>
    <div class="shape shape-2"></div>
    <div class="container">
        <h2>Résultats de la recherche</h2>
        
        <?php if ($error): ?>
            <div class="error-message"><?php echo $error; ?></div>
        <?php elseif (empty($results) && isset($_GET['motcle'])): ?>
            <div class="empty-state">Aucun document trouvé pour "<strong><?php echo htmlspecialchars($_GET['motcle']); ?></strong>".</div>
        <?php elseif (!empty($results)): ?>
            <div class="result-list">
                <?php foreach ($results as $row): ?>
                    <div class="result-card">
                        <div class="result-info">
                            <h3><?php echo htmlspecialchars($row['descr']); ?></h3>
                        </div>
                        <a href="<?php echo htmlspecialchars($row['adress']); ?>" target="_blank" class="btn-open">
                            Ouvrir →
                        </a>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
        
        <div class="link">
            <a href="search.html">← Nouvelle recherche</a>
        </div>
    </div>
</body>
</html>
