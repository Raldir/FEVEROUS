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
$sql = "CREATE TABLE CalibrationEvidence (
id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
annotator INT(100) NOT NULL,
claim INT(100) NOT NULL,
verdict TEXT(100) NOT NULL,
evidence1 TEXT(500) NOT NULL,
details1 TEXT(2000) NOT NULL,
evidence2 TEXT(500),
details2 TEXT(2000),
evidence3 TEXT(500),
details3 TEXT(2000),
search TEXT(1000),
hyperlinks TEXT(1000),
page_search TEXT(1000),
search_order TEXT(1000),
total_annotation_time TEXT(1000),
annotation_time_events TEXT(1000),
challenges VARCHAR(255),
questions TEXT(2000),
answers TEXT(500),
date_made DATETIME,
date_modified DATETIME
)";

if ($conn->query($sql) === TRUE) {
  echo "Table Evidence created successfully";
} else {
  echo "Error creating table: " . $conn->error;
}

$conn->close();
?>
