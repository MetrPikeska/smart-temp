<?php
// API pro čtení dat z lokálního serveru
// Umístit: petrmikeska.cz/api.php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$local_server = 'http://192.168.34.4:5000';

$action = $_GET['action'] ?? 'latest';

try {
    switch ($action) {
        case 'latest':
            $response = file_get_contents($local_server . '/api/latest');
            echo $response;
            break;
        
        case 'history':
            $hours = $_GET['hours'] ?? 24;
            $response = file_get_contents($local_server . '/api/history?hours=' . intval($hours));
            echo $response;
            break;
        
        case 'stats':
            $hours = $_GET['hours'] ?? 24;
            $response = file_get_contents($local_server . '/api/stats?hours=' . intval($hours));
            echo $response;
            break;
        
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Unknown action']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
