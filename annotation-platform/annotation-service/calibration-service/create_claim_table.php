<?php
$db_params = parse_ini_file( dirname(__FILE__).'/db_params.ini', false);

$servername = "localhost";
$dbname = $db_params['database'];

// Create connection
$conn = new mysqli($servername, $db_params['user'], $db_params['password'], $dbname);
// Check connection
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

// sql to create table
$sql = "CREATE TABLE CalibrationClaims (
id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
claim TEXT(500) NOT NULL,
data_source INT(6) NOT NULL,
annotator INT(30) NOT NULL,
page VARCHAR(500) NOT NULL,
claim_type INT(6),
evidence_annotators_num INT(10),
search TEXT(500),
hyperlinks TEXT(500),
search_order TEXT(500),
total_annotation_time TEXT(500),
annotation_time_events TEXT(500),
taken_flag BOOLEAN,
challenges VARCHAR(500),
ref_claim TEXT(500),
skipped TEXT(500),
skipped_by INT(6),
date_made DATETIME,
date_modified DATETIME
-- totto_flag BOOLEAN,
-- tabfacts_flag BOOLEAN
-- claim_type 0 normal, 1 extedned 2 manipulation
)";

if ($conn->query($sql) === TRUE) {
  echo "Table Claims created successfully";
} else {
  echo "Error creating table: " . $conn->error;
}

$conn->close();
?>
