<?php
// Isolated read-only Nissan test; no configuration, MQTT or charging-control writes.
ini_set('display_errors', '0');
require_once __DIR__ . '/connection_test_lib.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function nissan_test_reply(int $status, array $body): void {
    http_response_code($status);
    echo json_encode($body);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    nissan_test_reply(405, ['success' => false, 'code' => 'invalid_request']);
}
if (!nissan_test_valid_origin($_SERVER) ||
    strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '')[0])) !== 'application/json' ||
    (isset($_SERVER['HTTP_SEC_FETCH_SITE']) && $_SERVER['HTTP_SEC_FETCH_SITE'] !== 'same-origin')) {
    nissan_test_reply(403, ['success' => false, 'code' => 'invalid_request']);
}
$body = file_get_contents('php://input', false, null, 0, 8193);
if ($body === false || strlen($body) > 8192 || !nissan_test_valid_input(json_decode($body, true))) {
    nissan_test_reply(400, ['success' => false, 'code' => 'invalid_input']);
}

// Inherit the settings web server's access policy. Same-origin checks block browser
// cross-site submissions; they are not a replacement for installation access control.
// A private file holds expiry times and keyed account digests, never raw account data.
$previousMask = umask(0077);
$directory = sys_get_temp_dir() . '/openwb-nissanconnect-test';
if ((!is_dir($directory) && !@mkdir($directory, 0700)) || is_link($directory)) {
    umask($previousMask);
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
$path = $directory . '/state';
if (is_link($path)) {
    umask($previousMask);
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
$lock = @fopen($path, 'c+');
umask($previousMask);
if (!$lock) {
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
if (!flock($lock, LOCK_EX | LOCK_NB)) {
    nissan_test_reply(429, ['success' => false, 'code' => 'busy', 'retry_after_seconds' => 0]);
}
$state = nissan_test_load_state($lock, time());
if ($state === null || count($state['accounts']) >= 1024) {
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
$input = json_decode($body, true);
$account = nissan_test_account_key($state, $input['user_id']);
$delays = nissan_test_delays($state, $account, time());
if ($delays['retry_after_seconds'] > 0) {
    header('Retry-After: ' . $delays['retry_after_seconds']);
    nissan_test_reply(429, array_merge(['success' => false,
        'code' => $delays['provider_retry_after_seconds'] > 0 ? 'provider_delay' : 'cooldown'], $delays));
}
// Verify writable state before a query; no local cooldown starts on failure.
if (!nissan_test_store_state($lock, $state)) {
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
ignore_user_abort(true);
set_time_limit(80);
$worker = dirname(__DIR__, 5) . '/packages/modules/vehicles/nissanconnect/connection_test.py';
$result = nissan_test_run_worker(['/usr/bin/python3', '-I', '-B', $worker], $body);
$now = time();
$result = nissan_test_record_result($state, $account, $result, $now);
if (!nissan_test_store_state($lock, $state)) {
    nissan_test_reply(503, ['success' => false, 'code' => 'unavailable']);
}
$result = array_merge($result, nissan_test_delays($state, $account, $now));
flock($lock, LOCK_UN);
fclose($lock);
nissan_test_reply(200, $result);
