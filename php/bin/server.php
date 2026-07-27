<?php

declare(strict_types=1);

require __DIR__ . '/../src/common.php';

$storePath = getenv('PHP_POSTS_FILE') ?: (__DIR__ . '/posts.json');
$posts = [];
if (is_file($storePath)) {
    $stored = json_decode((string) file_get_contents($storePath), true);
    if (is_array($stored)) {
        $posts = $stored;
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'POST required'], JSON_THROW_ON_ERROR);
    exit;
}

$event = json_decode(file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
try {
    $reply = process_event($event, $posts, 5);
    $directory = dirname($storePath);
    if (!is_dir($directory)) {
        mkdir($directory, 0775, true);
    }
    file_put_contents($storePath, json_encode($posts, JSON_THROW_ON_ERROR), LOCK_EX);
    header('Content-Type: application/json');
    echo json_encode($reply, JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    http_response_code(400);
    header('Content-Type: application/json');
    echo json_encode(['error' => $error->getMessage()], JSON_THROW_ON_ERROR);
}
