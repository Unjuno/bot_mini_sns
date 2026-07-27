<?php

declare(strict_types=1);

require __DIR__ . '/../src/common.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'POST required'], JSON_THROW_ON_ERROR);
    exit;
}

$event = json_decode(file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
$posts = [];
try {
    $reply = process_event($event, $posts, 5);
    header('Content-Type: application/json');
    echo json_encode($reply, JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    http_response_code(400);
    header('Content-Type: application/json');
    echo json_encode(['error' => $error->getMessage()], JSON_THROW_ON_ERROR);
}
