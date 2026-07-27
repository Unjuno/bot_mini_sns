<?php

declare(strict_types=1);

/** Redirect adapter HTTP calls to a local mock server when explicitly enabled. */
function adapter_curl_init(string $url): CurlHandle
{
    $mockBase = getenv('ADAPTER_HTTP_BASE_URL');
    if (is_string($mockBase) && $mockBase !== '') {
        $parts = parse_url($url);
        $path = ($parts['path'] ?? '/').(isset($parts['query']) ? '?'.$parts['query'] : '');
        $url = rtrim($mockBase, '/').$path;
    }
    $handle = curl_init($url);
    if ($handle === false) throw new RuntimeException('Unable to initialize HTTP client');
    return $handle;
}
