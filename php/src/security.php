<?php

declare(strict_types=1);

function verify_hmac_sha256(string $body, string $secret, string $provided, string $prefix = ''): bool
{
    $actual = str_starts_with($provided, $prefix) ? substr($provided, strlen($prefix)) : $provided;
    return hash_equals(base64_encode(hash_hmac('sha256', $body, $secret, true)), $actual);
}

function verify_hmac_sha256_hex(string $body, string $secret, string $provided, string $prefix = ''): bool
{
    $actual = str_starts_with($provided, $prefix) ? substr($provided, strlen($prefix)) : $provided;
    return hash_equals(hash_hmac('sha256', $body, $secret), $actual);
}

function verify_slack_signature(string $body, string $secret, string $timestamp, string $provided): bool
{
    return verify_hmac_sha256_hex('v0:'.$timestamp.':'.$body, $secret, $provided, 'v0=');
}
