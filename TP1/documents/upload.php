<?php
$conn = new mysqli("localhost", "root", "", "test");

if ($conn->connect_error) {
    $status = "error";
    $message = "Erreur connexion : " . $conn->connect_error;
    die();
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
    <link rel="stylesheet" href="stylesheet4.css">
</head>
<body>
    <div class="shape shape-1"></div>
    <div class="shape shape-2"></div>
    <div class="container">
        <?php
            if ($status == "success") {
                echo "<div class='icon status-success'>✓</div>";
                echo "<h2>Succès</h2>";
            } else {
                echo "<div class='icon status-error'>✕</div>";
                echo "<h2>Erreur</h2>";
            }
            echo "<p>" . htmlspecialchars($message) . "</p>";
        ?>
        
        <div class="link">
            <a href="index.html">← Retour à l'insertion</a>
        </div>
    </div>
</body>
</html>
