<?php
ini_set('session.gc_maxlifetime', 86400);
session_set_cookie_params(86400);
session_start();

function update_table($conn, $sql_command, string $types , ...$vars ) {

  $date = date("Y-m-d H:i:s");
  $file = '../logs/claim_annotation.log';
  $sql2 = $sql_command; // Add flag that current claim is taken. Need to be freed when evidence is submitted,
  $stmt= $conn->prepare($sql2);
  $stmt->bind_param($types, ...$vars);
  $stmt->execute();
  $err = "Error description update contents: " . $sql_command . ' ' . $stmt -> error . $stmt->affected_rows;
  file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
}
// $req = $argv[1];
// $user_id = $argv[2];

$date = date("Y-m-d H:i:s");
$file = '../logs/claim_annotation.log';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $req = $_POST["request"];
  // $user_id = $_POST["user_id"];
}else if ($_SERVER['REQUEST_METHOD'] === 'GET'){
  $req = $_GET["request"];
  // $user_id = $_GET["user_id"];
}else{
  $req = $argv[1];
  // $user_id = $argv[2];
}
$user_id = $_SESSION['user'];
$finished_calibration = $_SESSION['finished_calibration'];

if ($finished_calibration == 2){
  $claim_data_table = "ClaimAnnotationData";
  $claim_table = "Claims";
}
else if ($finished_calibration == 0){
  $claim_data_table = "CalibrationClaimAnnotationDataP1";
  $claim_table = "CalibrationClaims";
  }
else if ($finished_calibration == 1){
  $claim_data_table = "CalibrationClaimAnnotationDataP2";
  $claim_table = "CalibrationClaims";
}

if ($_SESSION['annotation_mode'] != 'claim') { #Checks for existing session
  file_put_contents($file, "Annotator " . $user_id ." is assigned to different task" . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  echo -2;
  return;
}

$db_params = parse_ini_file( dirname(__FILE__).'/db_params.ini', false);
$annotations_params = parse_ini_file( dirname(__FILE__).'/annotation_params.ini', false);

if ($req == "skip-annotation" && $finished_calibration == 2){

  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];
  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }
  $sql = "SELECT id, annotation_mode, current_task FROM Annotators WHERE id = ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $result = $stmt->get_result();

  $row = $result->fetch_assoc();

  file_put_contents($file, "Skip claim request from user " . $user_id . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  //echo $row[1];
  if($result->num_rows > 0){
    if ($row['current_task'] != 0) {
      $sql = "SELECT id, page, is_table, selected_id FROM ClaimAnnotationData WHERE id = ?";
      $stmt= $conn->prepare($sql);
      $stmt->bind_param("i", $row['current_task']);
      $stmt->execute();
      $result = $stmt->get_result();
      $row = $result->fetch_assoc(); //get first result

      $conn->begin_transaction();
      try {
        update_table($conn, "UPDATE ClaimAnnotationData SET taken_flag=0, skipped=skipped+1, skipped_by=? WHERE id=?", 'ii', $user_id, $row['id']);
        update_table($conn, "UPDATE Annotators SET current_task=0, skipped_data=skipped_data+1 WHERE id=?", 'i', $user_id);
        $conn->commit();
      }catch (mysqli_sql_exception $exception) {
        $conn->rollback();
        file_put_contents($file, 'Error when trying to update tables for skipping! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        throw $exception;
      }
    }
  }
  $conn->close();
}else if ($req == "next-data"){
  // phpinfo();
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $conn = new mysqli($servername, $username, $password, $dbname);


  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  $sql = "SELECT id, annotation_mode, current_task FROM Annotators WHERE id = ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $result = $stmt->get_result();

  $row = $result->fetch_assoc();

  //echo $row[1];
  file_put_contents($file, "Select data for annotator " . $user_id. ' ' . $date.PHP_EOL, FILE_APPEND | LOCK_EX);

  if($result->num_rows > 0){
    if ($row['current_task'] != 0) {

      $sql = "SELECT id, page, is_table, selected_id, manipulation, quick_hyperlinks, multiple_pages, veracity FROM $claim_data_table WHERE id = ?";

      $stmt= $conn->prepare($sql);
      $stmt->bind_param("i", $row['current_task']);
      $stmt->execute();
      $result = $stmt->get_result();
      $row = $result->fetch_assoc(); //get first result
      $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
      echo json_encode($output);
    } else {
      $choice = mt_rand() / mt_getrandmax();
      $prob_new = $annotations_params['RATIO_NEW_CLAIMS_DATA'];
      $max_annotators_per_claim_data = $annotations_params['MAX_ANNOTATORS_PER_CLAIM_DATA'];

      // if($user_id == 2){
        if($choice < $prob_new || $finished_calibration!=2){
          $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num = (SELECT MIN(annotators_num) FROM $claim_data_table) AND taken_flag=0 AND skipped=0 AND (annotators_num<=$max_annotators_per_claim_data OR $finished_calibration!=2) AND NOT EXISTS (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1";
          $result = $conn->query($sql);
          $err = "Error description select data 1: " . $conn -> error;
          file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
          $row = $result->fetch_assoc(); // get first result
          $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
          if(empty($row['id'])){
            $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num > 0 AND taken_flag=0 AND skipped=0 AND (annotators_num<=$max_annotators_per_claim_data OR $finished_calibration!=2) AND NOT EXISTS (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
            $result = $conn->query($sql);
            $err = "Error description select data 2: " . $conn -> error;
            file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
            $row = $result->fetch_assoc(); // get first result
            $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
          }
        }
        else{
          $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num > 0 AND taken_flag=0 AND skipped=0 AND annotators_num <=$max_annotators_per_claim_data AND NOT EXISTS (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
          $result = $conn->query($sql);
          $err = "Error description select data 3: " . $conn -> error;
          file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
          $row = $result->fetch_assoc(); // get first result
          $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
          if(empty($row['id'])){
            $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num = (SELECT MIN(annotators_num) FROM $claim_data_table) AND taken_flag=0 AND skipped=0 AND annotators_num<=$max_annotators_per_claim_data AND NOT EXISTS (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
            $result = $conn->query($sql);
            $err = "Error description select data 4: " . $conn -> error;
            file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
            $row = $result->fetch_assoc(); // get first result
            $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
          }
        }
      // }
    //   else{
    //   if($choice < $prob_new || $finished_calibration!=2){
    //     $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num = (SELECT MIN(annotators_num) FROM $claim_data_table) AND taken_flag=0 AND skipped=0 AND (annotators_num<=$max_annotators_per_claim_data OR $finished_calibration!=2) AND ca.id NOT IN (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1";
    //     $result = $conn->query($sql);
    //     $err = "Error description select data 1: " . $conn -> error;
    //     file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
    //     $row = $result->fetch_assoc(); // get first result
    //     $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
    //     if(empty($row['id'])){
    //       $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num > 0 AND taken_flag=0 AND skipped=0 AND (annotators_num<=$max_annotators_per_claim_data OR $finished_calibration!=2) AND ca.id NOT IN (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
    //       $result = $conn->query($sql);
    //       $err = "Error description select data 2: " . $conn -> error;
    //       file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
    //       $row = $result->fetch_assoc(); // get first result
    //       $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
    //     }
    //   }
    //   else{
    //     $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num > 0 AND taken_flag=0 AND skipped=0 AND annotators_num <=$max_annotators_per_claim_data AND ca.id NOT IN (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
    //     $result = $conn->query($sql);
    //     $err = "Error description select data 3: " . $conn -> error;
    //     file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
    //     $row = $result->fetch_assoc(); // get first result
    //     $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
    //     if(empty($row['id'])){
    //       $sql = "SELECT ca.id, page, is_table, selected_id, manipulation, quick_hyperlinks,skipped, multiple_pages, veracity FROM $claim_data_table ca WHERE (annotators_num = (SELECT MIN(annotators_num) FROM $claim_data_table) AND taken_flag=0 AND skipped=0 AND annotators_num<=$max_annotators_per_claim_data AND ca.id NOT IN (SELECT data_source FROM $claim_table cl WHERE (annotator = $user_id AND ca.id = data_source))) ORDER BY RAND() LIMIT 1 ";
    //       $result = $conn->query($sql);
    //       $err = "Error description select data 4: " . $conn -> error;
    //       file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
    //       $row = $result->fetch_assoc(); // get first result
    //       $output =  array($row['id'], $row['page'], $row['is_table'], $row['selected_id'], $row['manipulation'], $row['quick_hyperlinks'], $row['multiple_pages'], $row['veracity']);
    //     }
    //   }
    // }

      if(empty($row['id']) && $finished_calibration != 2){
        $conn->begin_transaction();
        update_table($conn, "UPDATE Annotators SET finished_calibration=finished_calibration+1,current_task=0 WHERE id=?", 'i', $user_id);
        $conn->commit();
        if($finished_calibration+1 ==2){
          echo json_encode(array('finished-calibration'));
          $_SESSION["finished_calibration"] = 2;
        }else if ($finished_calibration+1 ==1){
          $_SESSION["finished_calibration"] = 1;
          echo json_encode(array('phase2'));
        }
        return;
      }else{
        echo json_encode($output);
      }

      // echo json_encode($output);

      $conn->begin_transaction();
      try {
        if(!is_null($row['id'])){
          if ($finished_calibration == 2){
            update_table($conn, "UPDATE ClaimAnnotationData SET taken_flag=1 WHERE id=?", 'i', $row['id']);
          }
          update_table($conn, "UPDATE Annotators SET current_task=? WHERE id=?", 'ii', $row['id'], $user_id);
        }
        $conn->commit();
      }catch (mysqli_sql_exception $exception) {
        $conn->rollback();
        file_put_contents($file, 'Error when trying to update tables when next data! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        throw $exception;
      }
    }
  }
  file_put_contents($file, "Selected data " . $row['id'] . ' for user ' . $user_id . ' ' . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  $conn->close();
} else if ($req == "claim-submission"){

  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  file_put_contents($file, "Submit request from annotator " . $user_id. ' ' . $date.PHP_EOL, FILE_APPEND | LOCK_EX);

  $data_id = $_POST["data_id"];
  $generated_claim =  $_POST['claim'];
  $generated_claim_extended = $_POST['claim_extended'];
  $generated_claim_manipulation = $_POST['claim_manipulation'];
  $challenge = $_POST['challenge'];
  $challenge_extended = $_POST['challenge_extended'];
  $challenge_manipulation = $_POST['challenge_manipulation'];

  $search = $_POST['search'];
  $hyperlinks = $_POST['hyperlinks'];
  $order = $_POST['order'];
  $times = $_POST['times'];
  $total_time = $_POST['total_time'];

  file_put_contents($file, $user_id.PHP_EOL. $data_id.PHP_EOL . $generated_claim.PHP_EOL . $generated_claim_extended.PHP_EOL . $generated_claim_manipulation.PHP_EOL . $challenge.PHP_EOL . $challenge_extended.PHP_EOL . $challenge_manipulation.PHP_EOL . $search.PHP_EOL . $hyperlinks.PHP_EOL . $order.PHP_EOL . $times.PHP_EOL . $total_time.PHP_EOL . $date.PHP_EOL, FILE_APPEND | LOCK_EX);

  if ($search != 'null'){
    $search = implode(" [SEP] ", json_decode($search));
  }else{
    $search = NULL;
  }
  if ($hyperlinks != 'null'){
    $hyperlinks = implode(" [SEP] ", json_decode($hyperlinks));
  }else{
    $hyperlinks = NULL;
  }
  if ($order != 'null'){
    $order = implode(" [SEP] ", json_decode($order));
  }else{
    $order = NULL;
  }
  if ($times != 'null'){
    $times = implode(" [SEP] ", json_decode($times));
  }else{
    $times = NULL;
  }

  // $challenge = implode(" [SEP] ", json_decode($challenge));
  // $challenge_extended = implode(" [SEP] ", json_decode($challenge_extended));
  // $challenge_manipulation = implode(" [SEP] ", json_decode($challenge_manipulation));

  // $sql = "SELECT id, page, selected_id FROM ClaimAnnotationData WHERE (taken_flag = 1 AND id = (SELECT current_task FROM Annotators WHERE id=?))";
  $sql = "SELECT id, page, selected_id FROM $claim_data_table WHERE (id = (SELECT current_task FROM Annotators WHERE id=?))";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $result = $stmt->get_result();
  $row = $result->fetch_assoc();

  if($result->num_rows > 0){
    if ($row['id'] != $data_id){
      echo ('Claim ID and Annotator task do not match.  ');
      file_put_contents($file, "Claim ID and Annotator task do not match" . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
    }

    $conn->begin_transaction();
    try {
      update_table($conn, "INSERT INTO $claim_table(id, claim, data_source, annotator, page, claim_type, search_order, total_annotation_time, annotation_time_events, challenges, taken_flag, evidence_annotators_num, date_made) SELECT MAX(id ) + 1, ?, ?, ?, ?, 0, ?, ?, ?,?,0, 0,? FROM $claim_table", 'siissssss', $generated_claim, $data_id, $user_id, $row['page'], $order, $total_time, $times, $challenge, $date);
      update_table($conn, "INSERT INTO $claim_table(id, claim, data_source, annotator, page, claim_type, search, hyperlinks, search_order, total_annotation_time, annotation_time_events, challenges, ref_claim, taken_flag, evidence_annotators_num, date_made) SELECT MAX(id ) + 1, ?, ?, ?, ?, 1, ?,?,?, ?, ?, ?, ?, 0, 0,? FROM $claim_table", 'siisssssssss', $generated_claim_extended, $data_id, $user_id, $row['page'], $search, $hyperlinks, $order, $total_time, $times, $challenge_extended, $generated_claim, $date);
      update_table($conn, "INSERT INTO $claim_table(id, claim, data_source, annotator, page, claim_type, search, hyperlinks, search_order, total_annotation_time, annotation_time_events, challenges, ref_claim, taken_flag, evidence_annotators_num, date_made) SELECT MAX(id ) + 1, ?, ?, ?, ?, 2, ?,?,?, ?, ?, ?, ?, 0, 0,? FROM $claim_table", 'siisssssssss', $generated_claim_manipulation, $data_id, $user_id, $row['page'], $search, $hyperlinks, $order, $total_time, $times, $challenge_manipulation, $generated_claim, $date);
      $float_time = 0;
      if($total_time < 1200){
        $float_time = floatval($total_time);
      }
      update_table($conn, "UPDATE Annotators SET current_task=0, finished_claim_annotations=finished_claim_annotations+1, annotation_time = annotation_time + ?  WHERE id=?",'ii', $float_time, $user_id);
      update_table($conn, "UPDATE $claim_data_table SET taken_flag=0, annotators_num = annotators_num+1 WHERE id=?", 'i', $data_id);
      $conn->commit();
    }catch (mysqli_sql_exception $exception) {
      $conn->rollback();
      file_put_contents($file, 'Error when trying to update tables! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
      throw $exception;
    }
    $conn->close();
  }
}
else if ($req == "reload-claim"){

  $user_id = $_GET["user_id"];
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $back_count = $_GET['back_count'];# - 1;

  $back_count_ext = intval($_GET['back_count']) + 1;
  $back_count_man = intval($_GET['back_count']) + 2;


  file_put_contents($file, "Reload Claim: " . $user_id. ' ' .PHP_EOL, FILE_APPEND | LOCK_EX);


  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  $sql = "SELECT id, claim, data_source, annotator, page, claim_type, search_order, total_annotation_time, annotation_time_events, challenges, taken_flag, evidence_annotators_num, date_made FROM $claim_table WHERE annotator = ? AND date_made  > DATE_SUB(CURDATE(), INTERVAL 1 DAY) ORDER BY date_made DESC LIMIT 1 OFFSET ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii", $user_id, $back_count);
  $stmt->execute();
  $result = $stmt->get_result();

  $sql = "SELECT claim, search, hyperlinks, challenges FROM $claim_table WHERE annotator = ? AND date_made  > DATE_SUB(CURDATE(), INTERVAL 1 DAY) ORDER BY date_made DESC LIMIT 1 OFFSET ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii", $user_id, $back_count_ext);
  $stmt->execute();
  $result_c2 = $stmt->get_result();

  $sql = "SELECT claim, challenges FROM $claim_table WHERE annotator = ? AND date_made  > DATE_SUB(CURDATE(), INTERVAL 1 DAY) ORDER BY date_made DESC LIMIT 1 OFFSET ?";

  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii", $user_id, $back_count_man);
  $stmt->execute();
  $result_c3 = $stmt->get_result();
  //echo $row[1];
  $row = $result->fetch_assoc();
  $row_c2 = $result_c2->fetch_assoc();
  $row_c3 = $result_c3->fetch_assoc();

  if($result->num_rows > 0 && $result_c2->num_rows > 0 && $result_c3->num_rows > 0){
    $sql = "SELECT selected_id, manipulation, multiple_pages, is_table, veracity FROM $claim_data_table WHERE id = ?";
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("i", $row['data_source']);
    $stmt->execute();
    $result = $stmt->get_result();

    $data = $result->fetch_assoc();


    echo json_encode(array($row['claim'], $row_c2['claim'], $row_c3['claim'], $row['data_source'], $data['selected_id'], $data['manipulation'], $data['multiple_pages'], $row['page'], $row_c2['search'], $row_c2['hyperlinks'], $row['search_order'], $row['total_annotation_time'], $row['annotation_time_events'], $row['challenges'], $row_c2['challenges'], $row_c3['challenges'], $data['is_table'], $data['veracity']));
  }else{
    echo json_encode(array(-1));
  }
}
else if ($req == "claim-resubmission"){
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  file_put_contents($file, "Resubmit request from annotator " . $user_id. ' ' . $date.PHP_EOL, FILE_APPEND | LOCK_EX);

  $data_id = $_POST["data_id"];
  $generated_claim =  $_POST['claim'];
  $generated_claim_extended = $_POST['claim_extended'];
  $generated_claim_manipulation = $_POST['claim_manipulation'];
  $challenge = $_POST['challenge'];
  $challenge_extended = $_POST['challenge_extended'];
  $challenge_manipulation = $_POST['challenge_manipulation'];

  $search = $_POST['search'];
  $hyperlinks = $_POST['hyperlinks'];
  $order = $_POST['order'];
  $times = $_POST['times'];
  $total_time = $_POST['total_time'];

  file_put_contents($file, $user_id.PHP_EOL. $data_id.PHP_EOL . $generated_claim.PHP_EOL . $generated_claim_extended.PHP_EOL . $generated_claim_manipulation.PHP_EOL . $challenge.PHP_EOL . $challenge_extended.PHP_EOL . $challenge_manipulation.PHP_EOL . $search.PHP_EOL . $hyperlinks.PHP_EOL . $order.PHP_EOL . $times.PHP_EOL . $total_time.PHP_EOL . $date.PHP_EOL, FILE_APPEND | LOCK_EX);

  if ($search != 'null'){
    $search = implode(" [SEP] ", json_decode($search));
  }else{
    $search = NULL;
  }
  if ($hyperlinks != 'null'){
    $hyperlinks = implode(" [SEP] ", json_decode($hyperlinks));
  }else{
    $hyperlinks = NULL;
  }
  if ($order != 'null'){
    $order = implode(" [SEP] ", json_decode($order));
  }else{
    $order = NULL;
  }
  if ($times != 'null'){
    $times = implode(" [SEP] ", json_decode($times));
  }else{
    $times = NULL;
  }

  // $challenge = implode(" [SEP] ", json_decode($challenge));
  // $challenge_extended = implode(" [SEP] ", json_decode($challenge_extended));
  // $challenge_manipulation = implode(" [SEP] ", json_decode($challenge_manipulation));

  // $sql = "SELECT id, page, selected_id FROM ClaimAnnotationData WHERE (taken_flag = 1 AND id = (SELECT current_task FROM Annotators WHERE id=?))";
  // $sql = "SELECT id, page, selected_id FROM $claim_data_table WHERE (id = (SELECT current_task FROM Annotators WHERE id=?))";
  $sql = "SELECT id FROM $claim_table WHERE data_source = ? AND annotator = ? AND claim_type = 0";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii", $data_id, $user_id);
  $stmt->execute();
  $result = $stmt->get_result();
  $row = $result->fetch_assoc();

  $id_ex = intval($row['id']) + 1;
  $id_man =intval($row['id']) + 2;

  if($result->num_rows > 0){

    $conn->begin_transaction();
    try {
      update_table($conn, "UPDATE $claim_table SET claim =?, search_order=?, total_annotation_time=?, annotation_time_events=?, challenges=?, date_modified =? WHERE id=?", 'ssssssi', $generated_claim, $order, $total_time, $times, $challenge, $date, $row['id']);
      update_table($conn, "UPDATE $claim_table SET claim =?, search_order=?, total_annotation_time=?, annotation_time_events=?, challenges=?, date_modified=?, search=?, hyperlinks=? WHERE id=?", 'ssssssssi', $generated_claim_extended, $order, $total_time, $times, $challenge_extended, $date, $search, $hyperlinks, $id_ex);
      update_table($conn, "UPDATE $claim_table SET claim =?, search_order=?, total_annotation_time=?, annotation_time_events=?, challenges=?, date_modified=?, search=?, hyperlinks=? WHERE id=?", 'ssssssssi', $generated_claim_manipulation, $order, $total_time, $times, $challenge_manipulation, $date, $search, $hyperlinks, $id_man);
      $conn->commit();
    }catch (mysqli_sql_exception $exception) {
      $conn->rollback();
      file_put_contents($file, 'Error when trying to update resubmission tables! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
      throw $exception;
    }
    $conn->close();
  }
}
else{
  file_put_contents($file, "Not found." . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  echo "Not found";
}

?>
