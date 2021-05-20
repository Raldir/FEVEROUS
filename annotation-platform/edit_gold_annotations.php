<?php
session_start();

if (!isset($_SESSION["user"])){
  echo file_get_contents('login.html');
  echo "<!--";
}
else if($_SESSION['user'] > 22){
  echo 'You are not authorized to use this tool.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}else if ($_SESSION['annotation_mode'] != 'evidence'){
  echo 'Wrong annotator type. You are not authorized to use this tool.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}


$db_params = parse_ini_file( dirname(__FILE__).'/annotation-service/db_params.ini', false);

$servername = "localhost";
$username = $db_params['user'];
$password = $db_params['password'];
$dbname = $db_params['database'];

$conn = new mysqli($servername, $username, $password, $dbname);

if ($_SERVER['REQUEST_METHOD'] == "POST"){
  if(isset($_POST['submitButton'])){
    if($_POST['claim'] == ''){
      echo "EMPTY CLAIM";
      return;
    }
    if($_POST['set'] == 1){
    $sql = "UPDATE CalibrationGoldEvidence SET evidence1=?, details1=? WHERE claim=?";
  }else if ($_POST['set'] == 2){
      $sql = "UPDATE CalibrationGoldEvidence SET evidence2=?, details2=? WHERE claim=?";
  }else if ($_POST['set'] == 3){
      $sql = "UPDATE CalibrationGoldEvidence SET evidence3=?, details3=? WHERE claim=?";
  }
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("ssi",$_POST['annotations'], $_POST['details'], $_POST['claim']);
    $stmt->execute();
  }
}

?>
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.13.1/css/bootstrap-select.css" />

  <script src="js/extensions/jquery.js"></script>
  <script src="js/extensions/jquery.md5.js"></script>
  <script src="js/extensions/jquery_ui.js"></script>
  <script src="https://unpkg.com/@popperjs/core@2"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.13.1/js/bootstrap-select.min.js"></script>
</head>
<body>
  <form action="" method="post">
  <div class="form-group">
    <label for="exampleInputEmail1">Evidence</label>
    <input class="form-control" name="annotations">
  </div>
  <div class="form-group">
    <label for="exampleInputPassword1">Details</label>
    <input  class="form-control" name="details">
  </div>
  <div class="form-group">
    <label for="exampleInputPassword1">Claim</label>
    <input  class="form-control" name="claim">
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="set" id="exampleRadios1" value="1" checked>
    <label class="form-check-label" for="exampleRadios1">
      Set 1
    </label>
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="set" id="exampleRadios2" value="2">
    <label class="form-check-label" for="exampleRadios2">
      Set 2
    </label>
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="set" id="exampleRadios3" value="3">
    <label class="form-check-label" for="exampleRadios3">
      Set 3
    </label>
  </div>
<button type="submit" name="submitButton" class="btn btn-primary">Submit</button>
</form>
</body>
</html>
