<?php

declare(strict_types=1);

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
http_response_code(200);
header('Content-Type: application/json');
if (str_contains($path, 'chat.postMessage')) {
    echo json_encode(['ok' => true]);
} elseif (str_contains($path, 'helix/chat/messages')) {
    echo json_encode(['data' => [['is_sent' => true]]]);
} else {
    echo json_encode(['ok' => true, 'data' => []]);
}
