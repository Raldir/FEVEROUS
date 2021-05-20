<?php

function secondsToTime($seconds) {
    $dtF = new \DateTime('@0');
    $dtT = new \DateTime("@$seconds");
    $diff = $dtF->diff($dtT);
    $hours = $diff->h;
    $hours = $hours + ($diff->days*24);
    return $hours . ' hours ' . $diff->i . ' minutes, and ' . $diff->s . 'seconds';
    // return $dtF->diff($dtT)->format('%d days, %h hours, %i minutes and %s seconds');
}


// Start the session
session_start();


// ini_set('display_errors', 1);
// ini_set('display_startup_errors', 1);
//   error_reporting(E_ALL);
// Check user login or not
if (!isset($_SESSION["user"])){
    include 'index.php';
    echo "<!--";
}else{
  $user_id = $_SESSION["user"];
  // phpinfo();
  $db_params = parse_ini_file( dirname(__FILE__).'/annotation-service/db_params.ini', false);


  // phpinfo();
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = "FeverAnnotationsDB";

  $conn = new mysqli($servername, $username, $password, $dbname);

  $sql = "SELECT id, annotation_mode, current_task, finished_claim_annotations, finished_evidence_annotations, annotation_time, number_logins FROM Annotators WHERE id = ?";

  $stmt= $conn->prepare($sql);
  $stmt->bind_param("s", $user_id);
  $stmt->execute();
  $result = $stmt->get_result();

  $row = $result->fetch_assoc();

  $current_task = $row['current_task'];
  $finished_claim_annotations = $row['finished_claim_annotations'];
  $finished_evidence_annotations = $row['finished_evidence_annotations'];

  $annotation_time = secondsToTime($row['annotation_time']);
  $number_logins = $row['number_logins'];
}

//$user_id = 'hi';
?>

<html>
<head>
  <link rel="stylesheet" href="css/style.css">
</head>

<body>

  <script>
  function goBack() {
    window.history.back();
  }
  </script>


<div class="topnav" id="myTopnav">
  <button onclick="goBack()">Go Back</button>
</div>


<div class="menu-frame" id="my-menu-frame">
<div class="user-info-frame fixed" id="user-info-frame">

<div class="user-info-div center">
<p  id='user-id-info'>ID:  <?php echo $user_id;?>  </p>
<p  id='annotated-claims-info'>Completed Claim Annotation sets:  <?php echo $finished_claim_annotations;?>  </p>
<p  id='annotated-claims-info'>Completed Claim Annotations:  <?php echo $finished_claim_annotations*3;?>  </p>
<p  id='annotated-evidence-info'>Completed Evidence Annotation:  <?php echo $finished_evidence_annotations;?>  </p>
<br>
<p  id='annotated-evidence-info'>Total number of logins:  <?php echo $number_logins;?>  </p>
<p  id='annotated-evidence-info'>Total time spent:  <?php echo $annotation_time;?> </p>
</div>
</div>
</div>
</body>
</html>
