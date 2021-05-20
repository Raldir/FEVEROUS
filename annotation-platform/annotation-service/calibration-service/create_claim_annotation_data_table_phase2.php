<?php
$db_params = parse_ini_file( dirname(__FILE__).'/../db_params.ini', false);

$servername = "localhost";
$dbname = $db_params['database'];

// Create connection
$conn = new mysqli($servername, $db_params['user'], $db_params['password'], $dbname);
// Check connection
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

// sql to create table
$sql = "CREATE TABLE CalibrationClaimAnnotationDataP2(
id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
page TEXT(1000) NOT NULL,
page_id INT(6) NOT NULL,
is_table BOOLEAN NOT NULL,
selected_id TEXT(1000) NOT NULL,
manipulation TEXT(100) NOT NULL,
multiple_pages BOOLEAN NOT NULL,
quick_hyperlinks TEXT(1000),
taken_flag BOOLEAN NOT NULL,
annotators_num INT(6),
in_tabfacts1 BOOLEAN,
in_tabfacts2 BOOLEAN,
in_ott BOOLEAN,
skipped INT(6),
skipped_by INT(6),
veracity INT(6) NOT NULL
)";

if ($conn->query($sql) === TRUE) {
  echo "Table Claims created successfully";
} else {
  echo "Error creating table: " . $conn->error;
}

$conn->close();
?>
