<?php
ini_set('session.gc_maxlifetime', 86400);
session_set_cookie_params(86400);
session_start();

$_SESSION = array();
function update_table($conn, $sql_command, string $types , ...$vars ) {
$sql2 = $sql_command; // Add flag that current claim is taken. Need to be freed when evidence is submitted,
$stmt= $conn->prepare($sql2);
$stmt->bind_param($types, ...$vars);
$stmt->execute();
}

$id = $_GET["id"];
$pw_md5 = $_GET["pw"];

$db_params = parse_ini_file( dirname(__FILE__).'/db_params.ini', false);
$date = date("Y-m-d H:i:s");


$servername = "localhost";
$username = $db_params['user'];
$password = $db_params['password'];
$dbname = $db_params['database'];

$conn = new mysqli($servername, $username, $password, $dbname);


if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

$sql = "SELECT id,annotation_mode, finished_calibration, calibration_score, active FROM Annotators WHERE password_md5 = ? AND id = ? AND active !=-1";
$stmt= $conn->prepare($sql);
$stmt->bind_param("si", $pw_md5, $id);
$stmt->execute();

$result = $stmt->get_result();
$credentials_match = $result->num_rows > 0;
if ($credentials_match) {
  $row = $result->fetch_assoc();
  $_SESSION["user"] = $id;
  $_SESSION["annotation_mode"] = $row['annotation_mode'];
  if($row['annotation_mode'] =='claim'){
    $file = '../logs/claim_annotation.log';
  }else if($row['annotation_mode'] =='evidence'){
    $file = '../logs/evidence_annotation.log';
  }
  $_SESSION["finished_calibration"] = $row['finished_calibration'];
  $_SESSION["calibration_score"] = $row['calibration_score'];
  $_SESSION["active"] = $row['active'];

  file_put_contents($file, "Annotator " . $id . " logged into the tool. " . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  $output =  array($credentials_match, $row['annotation_mode'], $row['finished_calibration']);
  update_table($conn, "UPDATE Annotators SET number_logins=number_logins+1 WHERE id=?", 'i', $id);
  echo(json_encode($output));
}else{
  echo 0;
}

$conn->close();
?>
