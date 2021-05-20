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
$sql = "CREATE TABLE Adjudication(
id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
annotator INT(10) NOT NULL,
mode TEXT(10) NOT NULL,
annotation1 INT(10) NOT NULL,
annotation2 INT(10) NOT NULL,
adjudication TEXT(10),
comment TEXT(1000)
)";

if ($conn->query($sql) === TRUE) {
  echo "Table Adjudication created successfully";
} else {
  echo "Error creating table: " . $conn->error;
}

$conn->close();
?>
