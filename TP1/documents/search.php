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
    <link rel="stylesheet" href="stylesheet3.css">
</head>
<body>
    <div class="shape shape-1"></div>
    <div class="shape shape-2"></div>
    <div class="container">
        <h2>Résultats de la recherche</h2>
        
        <?php
            if ($error) {
                echo "<div class='error-message'>" . $error . "</div>";
            } elseif (empty($results) && isset($_GET['motcle'])) {
                echo "<div class='empty-state'>Aucun document trouvé pour \"<strong>" . htmlspecialchars($_GET['motcle']) . "</strong>\".</div>";
            } elseif (!empty($results)) {
                echo "<div class='result-list'>";
                foreach ($results as $row) {
                    echo "<div class='result-card'>";
                    echo "<div class='result-info'>";
                    echo "<h3>" . htmlspecialchars($row['descr']) . "</h3>";
                    echo "</div>";
                    echo "<a href='" . htmlspecialchars($row['adress']) . "' target='_blank' class='btn-open'>";
                    echo "Ouvrir →";
                    echo "</a>";
                    echo "</div>";
                }
                echo "</div>";
            }
        ?>
        
        <div class="link">
            <a href="search.html">← Nouvelle recherche</a>
        </div>
    </div>
</body>
</html>
