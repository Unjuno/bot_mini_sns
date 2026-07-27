<?php

declare(strict_types=1);
require_once __DIR__ . '/../src/common.php';

$posts = [];
while (($line = fgets(STDIN)) !== false) {
    $event = json_decode(trim($line), true, flags: JSON_THROW_ON_ERROR);
    echo json_encode(process_event($event, $posts), JSON_UNESCAPED_UNICODE) . PHP_EOL;
}
