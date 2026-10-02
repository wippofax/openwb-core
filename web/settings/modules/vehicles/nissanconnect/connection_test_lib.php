<?php
// Module-owned settings test helpers. PHP 7.4+, Linux deployment.

function nissan_test_valid_origin(array $server): bool {
    $origin = parse_url($server['HTTP_ORIGIN'] ?? '');
    $host = parse_url('http://' . ($server['HTTP_HOST'] ?? ''));
    $scheme = (!empty($server['HTTPS']) && $server['HTTPS'] !== 'off') ? 'https' : 'http';
    if (!is_array($origin) || !is_array($host) || !isset($origin['host'], $host['host']) ||
        isset($origin['user']) || isset($origin['pass']) || isset($origin['query']) ||
        isset($origin['fragment']) || isset($origin['path']) || ($origin['scheme'] ?? '') !== $scheme) {
        return false;
    }
    return strtolower($origin['host']) === strtolower($host['host']) &&
        ($origin['port'] ?? ($scheme === 'https' ? 443 : 80)) ===
        ($host['port'] ?? ($scheme === 'https' ? 443 : 80));
}

function nissan_test_valid_input($input): bool {
    if (!is_array($input) || array_diff(array_keys($input), ['user_id', 'password', 'vin'])) {
        return false;
    }
    $user = $input['user_id'] ?? null;
    $password = $input['password'] ?? null;
    $vin = $input['vin'] ?? null;
    return is_string($user) && trim($user) !== '' && strlen($user) <= 320 &&
        is_string($password) && $password !== '' && strlen($password) <= 4096 &&
        ($vin === null || $vin === '' || (is_string($vin) &&
            preg_match('/^[A-HJ-NPR-Z0-9]{17}$/', strtoupper(trim($vin))) === 1));
}

function nissan_test_run_worker(array $command, string $body, float $timeout = 70.0): array {
    $process = @proc_open($command, [0 => ['pipe', 'r'], 1 => ['pipe', 'w'],
        2 => ['file', PHP_OS_FAMILY === 'Windows' ? 'NUL' : '/dev/null', 'w']], $pipes,
        null, null, ['bypass_shell' => true]);
    if (!is_resource($process)) {
        return ['success' => false, 'code' => 'unavailable'];
    }
    // The command and all argv values are fixed; user input travels only through stdin.
    $offset = 0;
    while ($offset < strlen($body)) {
        $written = @fwrite($pipes[0], substr($body, $offset));
        if (!$written) { break; }
        $offset += $written;
    }
    fclose($pipes[0]);
    stream_set_blocking($pipes[1], false);
    $output = '';
    $deadline = microtime(true) + $timeout;
    $failed = false;
    do {
        $output .= stream_get_contents($pipes[1], 8193 - min(strlen($output), 8193));
        $status = proc_get_status($process);
        if (strlen($output) > 8192 || microtime(true) >= $deadline) {
            $failed = true;
            proc_terminate($process, 9);
            break;
        }
        if ($status['running']) { usleep(20000); }
    } while ($status['running']);
    if (!$failed) { $output .= stream_get_contents($pipes[1], 8193); }
    fclose($pipes[1]);
    proc_close($process);
    if ($failed || strlen($output) > 8192 || $offset !== strlen($body)) {
        return ['success' => false, 'code' => 'timeout'];
    }
    $result = json_decode($output, true);
    if (!is_array($result) || !isset($result['success'], $result['code']) || !is_bool($result['success'])) {
        return ['success' => false, 'code' => 'unavailable'];
    }
    return $result;
}

function nissan_test_effective_uid(): ?int {
    // Linux deployment; do not mistake a Windows stat UID for an ACL check.
    if (PHP_OS_FAMILY !== 'Linux') { return null; }
    if (function_exists('posix_geteuid')) { return posix_geteuid(); }
    // POSIX is optional in PHP. Read only this process's bounded UID record.
    $status = @file_get_contents('/proc/self/status', false, null, 0, 16384);
    if (!is_string($status) ||
        preg_match('/^Uid:[ \t]+[0-9]+[ \t]+([0-9]+)[ \t]+[0-9]+[ \t]+([0-9]+)[ \t]*$/m',
            $status, $match) !== 1 || $match[1] !== $match[2]) {
        return null;
    }
    return (int)$match[1];
}

function nissan_test_private_stat($stat, int $uid, bool $directory): bool {
    return is_array($stat) && ($stat['uid'] ?? null) === $uid &&
        (($stat['mode'] ?? 0) & 0170000) === ($directory ? 0040000 : 0100000) &&
        (($stat['mode'] ?? 0) & 07777) === ($directory ? 0700 : 0600) &&
        ($directory || ($stat['nlink'] ?? 0) === 1);
}

function nissan_test_same_file($left, $right): bool {
    return is_array($left) && is_array($right) &&
        isset($left['dev'], $left['ino'], $right['dev'], $right['ino']) &&
        $left['dev'] === $right['dev'] && $left['ino'] === $right['ino'];
}

function nissan_test_open_state(string $directory) {
    $uid = nissan_test_effective_uid();
    if ($uid === null) { return false; }
    $parent = dirname($directory);
    clearstatcache(true, $parent);
    $parentStat = @lstat($parent);
    // A writable shared parent needs sticky-directory protection. Do not trust
    // a parent owned by another unprivileged user, even when its mode looks safe.
    if (!is_array($parentStat) || (($parentStat['mode'] ?? 0) & 0170000) !== 0040000 ||
        !in_array($parentStat['uid'] ?? null, [0, $uid], true) ||
        (($parentStat['mode'] & 0022) !== 0 && ($parentStat['mode'] & 01000) === 0)) {
        return false;
    }
    $previousMask = umask(0077);
    try {
        clearstatcache(true, $directory);
        $beforeDirectory = @lstat($directory);
        if ($beforeDirectory === false) {
            // Another legitimate request may win creation; validate its result.
            @mkdir($directory, 0700);
            clearstatcache(true, $directory);
            $beforeDirectory = @lstat($directory);
        }
        if (!nissan_test_private_stat($beforeDirectory, $uid, true)) { return false; }
        $path = $directory . '/state';
        clearstatcache(true, $path);
        $beforeFile = @lstat($path);
        if ($beforeFile !== false && !nissan_test_private_stat($beforeFile, $uid, false)) {
            return false;
        }
        // Exclusive creation does not follow an existing link. Reopening never
        // truncates: inspect the opened descriptor before reading or writing.
        $file = @fopen($path, $beforeFile === false ? 'x+b' : 'r+b');
        if ($file === false) { return false; }
        $opened = fstat($file);
        clearstatcache(true, $path);
        $afterFile = @lstat($path);
        clearstatcache(true, $directory);
        $afterDirectory = @lstat($directory);
        if (!nissan_test_private_stat($opened, $uid, false) ||
            !nissan_test_private_stat($afterFile, $uid, false) ||
            !nissan_test_private_stat($afterDirectory, $uid, true) ||
            !nissan_test_same_file($beforeDirectory, $afterDirectory) ||
            !nissan_test_same_file($opened, $afterFile) ||
            ($beforeFile !== false && !nissan_test_same_file($beforeFile, $opened))) {
            fclose($file);
            return false;
        }
        return $file;
    } finally {
        umask($previousMask);
    }
}

function nissan_test_load_state($lock, int $now): ?array {
    rewind($lock);
    $raw = stream_get_contents($lock, 131073);
    if ($raw === '') {
        return ['key' => bin2hex(random_bytes(32)), 'accounts' => [], 'provider_until' => 0];
    }
    $state = json_decode($raw, true);
    if (strlen($raw) > 131072 || !is_array($state) ||
        !is_string($state['key'] ?? null) || !preg_match('/^[a-f0-9]{64}$/', $state['key']) ||
        !is_array($state['accounts'] ?? null) || !is_int($state['provider_until'] ?? null)) {
        return null;
    }
    foreach ($state['accounts'] as $key => $until) {
        if (!preg_match('/^[a-f0-9]{64}$/', (string)$key) || !is_int($until)) { return null; }
        if ($until <= $now) { unset($state['accounts'][$key]); }
    }
    return $state;
}

function nissan_test_store_state($lock, array $state): bool {
    $value = json_encode($state);
    return is_string($value) && strlen($value) <= 131072 && rewind($lock) && ftruncate($lock, 0) &&
        fwrite($lock, $value) === strlen($value) && fflush($lock);
}

function nissan_test_account_key(array $state, string $user): string {
    return hash_hmac('sha256', strtolower(trim($user)), $state['key']);
}

function nissan_test_delays(array $state, string $account, int $now): array {
    $accountDelay = max(0, min(300, ($state['accounts'][$account] ?? 0) - $now));
    $providerDelay = max(0, min(86400, $state['provider_until'] - $now));
    return ['account_retry_after_seconds' => $accountDelay,
        'provider_retry_after_seconds' => $providerDelay,
        'retry_after_seconds' => max($accountDelay, $providerDelay)];
}

function nissan_test_record_result(array &$state, string $account, array $result, int $now): array {
    $query = $result['query'] ?? [];
    if (($result['success'] ?? false) === true) {
        $soc = $query['soc'] ?? null;
        $range = $query['range_km'] ?? null;
        $odometer = $query['odometer_km'] ?? null;
        $complete = ($query['outcome'] ?? '') === 'success' &&
            (is_int($soc) || is_float($soc)) && is_finite((float)$soc) && $soc >= 0 && $soc <= 100 &&
            ($range === null || ((is_int($range) || is_float($range)) && is_finite((float)$range) && $range >= 0));
        $complete = $complete && ($odometer === null ||
            ((is_int($odometer) || is_float($odometer)) && is_finite((float)$odometer) && $odometer >= 0));
        foreach (['request_started_at', 'completed_at', 'measurement_at'] as $field) {
            $complete = $complete && is_string($query[$field] ?? null) && strtotime($query[$field]) !== false;
        }
        if (!$complete) { return ['success' => false, 'code' => 'unavailable']; }
        $state['accounts'][$account] = $now + 300;
    }
    // Nissan does not expose a reliable account-only scope here. Treat its advice
    // conservatively as provider-wide so changing accounts cannot bypass it.
    $delay = max(0, min(86400, (int)($query['provider_retry_after_seconds'] ?? 0)));
    $state['provider_until'] = max($state['provider_until'], $now + $delay);
    return $result;
}
