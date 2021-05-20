<?php
ini_set('session.gc_maxlifetime', 86400);
session_set_cookie_params(86400);
session_start();

function update_table($conn, $sql_command, string $types , ...$vars ) {
  $date = date("Y-m-d H:i:s");
  $file = '../logs/evidence_annotation.log';
  $sql2 = $sql_command; // Add flag that current claim is taken. Need to be freed when evidence is submitted,
  $stmt= $conn->prepare($sql2);
  $stmt->bind_param($types, ...$vars);
  $stmt->execute();
  $err = "Error description update contents: " . $sql_command . ' ' . $stmt -> error . $stmt->affected_rows;
  file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
}


mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);

$date = date("Y-m-d H:i:s");
$file = '../logs/evidence_annotation.log';
// $req = $argv[1];
// $user_id = $argv[2];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $req = $_POST["request"];
}else if ($_SERVER['REQUEST_METHOD'] === 'GET'){
  $req = $_GET["request"];
}else{
  $req = $argv[1];
}

$user_id = $_SESSION['user'];
$finished_calibration = $_SESSION['finished_calibration'];

if ($finished_calibration == 2){
  $evidence_table = "Evidence";
  $claim_table = "Claims";
}else if ($finished_calibration == 1){
  $evidence_table = "CalibrationEvidence";
  $claim_table = "CalibrationEvidenceClaimsP2";
} else if ($finished_calibration == 0){
  $evidence_table = "CalibrationEvidence";
  $claim_table = "CalibrationEvidenceClaimsP1";
}

if ($_SESSION['annotation_mode'] != 'evidence') {
  file_put_contents($file, "Annotator " . $user_id ." is assigned to different task" . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
  echo -2;
  return;
}


$db_params = parse_ini_file( dirname(__FILE__).'/db_params.ini', false);
$annotations_params = parse_ini_file( dirname(__FILE__).'/annotation_params.ini', false);

if ($req == "report-claim"){ //&& $finished_calibration == 1

  // $user_id = $_POST["user_id"];
  $claim_id = $_POST["claim_id"];
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
  if($result->num_rows > 0){
    if ($row['current_task'] != 0) {
      $sql = "SELECT id, claim FROM $claim_table WHERE id = ?";
      $stmt= $conn->prepare($sql);
      $stmt->bind_param("i", $row['current_task']);
      $stmt->execute();
      $result = $stmt->get_result();
      $row = $result->fetch_assoc();

      $report_text = $_POST['report_text'];
      $report_text = implode(" [SEP] ", json_decode($report_text));

      $conn->begin_transaction();
      try {
        update_table($conn, "UPDATE $claim_table SET taken_flag=0,skipped=?, skipped_by=? WHERE id=?", 'sii', $report_text, $user_id, $claim_id);//add reported by
        update_table($conn, "UPDATE Annotators SET current_task=0, reported_claims = reported_claims + 1 WHERE id=?", 'i', $user_id);
        $conn->commit();
      }catch (mysqli_sql_exception $exception) {
        $conn->rollback();
        file_put_contents($file, 'Error when trying to update tables for skipping! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        throw $exception;
      }
    }else{
      #echo 'No task assigned. Cannot skip.';
      file_put_contents($file, 'No task assigned. Cannot skip.' . $date.PHP_EOL, FILE_APPEND | LOCK_EX);
    }
  }
  $conn->close();
}
else if ($req == "next-claim"){
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

  file_put_contents($file, "A claim request from " . $user_id.PHP_EOL, FILE_APPEND | LOCK_EX);

  //echo $row[1];
  if($result->num_rows > 0){
    if ($row['current_task'] != 0) {
      $sql = "SELECT id, claim FROM $claim_table WHERE id = ?";
      $stmt= $conn->prepare($sql);
      $stmt->bind_param("i", $row['current_task']);
      $stmt->execute();
      $result = $stmt->get_result();
      $row = $result->fetch_assoc();
      $output =  array($row['id'], $row['claim']);
      echo json_encode($output);
    } else {
      $choice = mt_rand() / mt_getrandmax();
      $prob_new = $annotations_params['RATIO_NEW_CLAIMS'];
      $max_annotators_per_claim = $annotations_params['MAX_ANNOTATORS_PER_CLAIM'];
      $duplicate_annotator_num = rand(0,1);
      if($choice < $prob_new || $finished_calibration!=2){
        $sql = "SELECT cl.id, cl.claim, cl.skipped, cl.annotator FROM $claim_table cl WHERE (cl.evidence_annotators_num = (SELECT MIN(cq.evidence_annotators_num) FROM $claim_table cq) AND cl.taken_flag=0  AND cl.skipped IS NULL AND cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND  (cl.evidence_annotators_num<=$max_annotators_per_claim OR $finished_calibration!=2) AND cl.annotator != $user_id +1 AND NOT EXISTS (SELECT ev.claim FROM $evidence_table ev WHERE (ev.annotator = $user_id AND ev.claim = cl.id))) ORDER BY RAND() LIMIT 1 ";
        // $sql = "SELECT cl.id, cl.claim, cl.skipped, cl.annotator FROM $claim_table cl WHERE (cl.evidence_annotators_num = (SELECT MIN(cq.evidence_annotators_num) FROM $claim_table cq) AND cl.taken_flag=0 AND cl.skipped IS NULL AND cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND  cl.evidence_annotators_num<=$max_annotators_per_claim AND cl.annotator != $user_id +1 AND cl.id NOT IN (SELECT ev.claim FROM $evidence_table ev WHERE (ev.annotator = $user_id AND ev.claim = cl.id))) ORDER BY RAND() LIMIT 1 ";
        $result = $conn->query($sql);
        $err = "Error description: select claim 1" . $conn -> error;
        file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        $row = $result->fetch_assoc();
        $output =  array($row['id'], $row['claim']);
        if(empty($row['id'])){
          $sql = "SELECT cl.id, cl.claim, cl.skipped, cl.annotator FROM $claim_table cl WHERE  (cl.evidence_annotators_num > $duplicate_annotator_num AND cl.taken_flag=0 AND cl.skipped IS NULL AND cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND (cl.evidence_annotators_num<=$max_annotators_per_claim OR $finished_calibration!=2) AND cl.annotator != $user_id +1 AND NOT EXISTS (SELECT ev.claim FROM $evidence_table ev WHERE (ev.annotator = $user_id AND ev.claim = cl.id))) ORDER BY RAND() LIMIT 1";
          $result = $conn->query($sql);
          $err = "Error description: select claim 2" . $conn -> error;
          file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
          $row = $result->fetch_assoc();
          $output =  array($row['id'], $row['claim']);
        }
      }else{
        $sql = "SELECT cl.id, cl.claim, cl.skipped, cl.annotator FROM $claim_table cl WHERE (cl.evidence_annotators_num > $duplicate_annotator_num AND cl.taken_flag=0 AND cl.skipped IS NULL AND cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND cl.evidence_annotators_num<=$max_annotators_per_claim  AND cl.annotator != $user_id +1 AND NOT EXISTS (SELECT ev.claim FROM $evidence_table ev WHERE (ev.annotator = $user_id AND ev.claim = cl.id))) ORDER BY RAND() LIMIT 1";
        $result = $conn->query($sql);
        $err = "Error description select claim 3: " . $conn -> error;
        file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        $row = $result->fetch_assoc();
        $output =  array($row['id'], $row['claim']);
        if(empty($row['id'])){
          $sql = "SELECT cl.id, cl.claim, cl.skipped, cl.annotator FROM $claim_table cl WHERE (cl.evidence_annotators_num = (SELECT MIN(cq.evidence_annotators_num) FROM $claim_table cq) AND cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND cl.taken_flag=0 AND cl.skipped IS NULL AND cl.evidence_annotators_num<=$max_annotators_per_claim AND cl.annotator != $user_id + 1 AND NOT EXISTS (SELECT ev.claim FROM $evidence_table ev WHERE (ev.annotator = $user_id AND ev.claim = cl.id))) ORDER BY RAND() LIMIT 1";
          $result = $conn->query($sql);
          $err = "Error description select claim 4: " . $conn -> error;
          file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
          $row = $result->fetch_assoc();
          $output =  array($row['id'], $row['claim']);
        }
      }
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

      $conn->begin_transaction();
      try {
        if(!is_null($row['id'])){
        update_table($conn, "UPDATE Annotators SET current_task=? WHERE id=?", 'ii', $row['id'], $user_id);
        if ($finished_calibration == 2){
          update_table($conn, "UPDATE Claims SET taken_flag=1 WHERE id=?", 'i', $row['id']);
        }
      }
        file_put_contents($file, 'Returned Claim ' . $row['id'] . ' to user ' .  $user_id.PHP_EOL, FILE_APPEND | LOCK_EX);
        $conn->commit();
      }catch (mysqli_sql_exception $exception) {
        $conn->rollback();
        file_put_contents($file, 'Error when trying to update tables for next claim! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
        throw $exception;
      }
      $conn->close();
    }
  }
}
else if ($req == "evidence-submission"){

  // phpinfo();
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  $user_id = $_POST["user_id"];
  $claim_id = $_POST["claim_id"];

  file_put_contents($file, "Got Submission from " . $user_id. ' ' . $claim_id .PHP_EOL, FILE_APPEND | LOCK_EX);

  $evidence1 = $_POST['evidence1'];
  $details1 = $_POST['details1'];
  $evidence2 = $_POST['evidence2'];
  $details2 = $_POST['details2'];
  $evidence3 = $_POST['evidence3'];
  $details3 = $_POST['details3'];

  $verdict = $_POST['verdict'];
  $challenge = $_POST['challenge'];

  $search = $_POST['search'];
  $hyperlinks = $_POST['hyperlinks'];
  $order = $_POST['order'];
  $page_search = $_POST['page_search'];

  $times = $_POST['times'];
  $total_time = $_POST['total_time'];

  $questions = $_POST['questions'];
  $answers = $_POST['answers'];



  $evidence1 =   implode(" [SEP] ", json_decode($evidence1));
  $details1 = implode(" [SEP] ", json_decode($details1));

  if ($evidence2 != 'null'){
    $evidence2 =  implode(" [SEP] ", json_decode($evidence2));
    $details2 =  implode(" [SEP] ", json_decode($details2)) ;
  }else{
    $evidence2 = NULL;
    $details2 = NULL;
  }

  if($evidence3 != 'null'){
    $evidence3 = implode(" [SEP] ", json_decode($evidence3));
    $details3 =implode(" [SEP] ", json_decode($details3));
  }else{
    $evidence3 = NULL;
    $details3 = NULL;
  }
  // if ($challenge != 'null'){
  //   $challenge =  implode(" [SEP] ", json_decode($challenge)) ;
  // }else{
  //   $challenge = NULL;
  // }


  if ($search != 'null'){
    $search =  implode(" [SEP] ", json_decode($search)) ;
  }else{
    $search = NULL;
  }

  if ($hyperlinks != 'null'){
    $hyperlinks =  implode(" [SEP] ", json_decode($hyperlinks));
  }else{
    $hyperlinks = NULL;
  }
  if ($order != 'null'){
    $order =   implode(" [SEP] ", json_decode($order));
  }else{
    $order = NULL;
  }
  if ($page_search != 'null'){
    $page_search =  implode(" [SEP] ", json_decode($page_search));
  }else{
    $page_search = NULL;
  }
  if ($questions != 'null'){
    $questions = implode(" [SEP] ", json_decode($questions)) ;
    $answers =  implode(" [SEP] ", json_decode($answers));
  }else{
    $questions = NULL;
    $answers = NULL;
  }
  if ($times != 'null'){
    $times = implode(" [SEP] ", json_decode($times));
  }else{
    $times = NULL;
  }

  file_put_contents($file, $user_id.PHP_EOL.$claim_id.PHP_EOL.$evidence1.PHP_EOL.$details1.PHP_EOL.$evidence2.PHP_EOL.$details2.PHP_EOL.$evidence3.PHP_EOL.$details3.PHP_EOL.$verdict.PHP_EOL.$challenge.PHP_EOL.$search.PHP_EOL.$hyperlinks.PHP_EOL.$order.PHP_EOL.$page_search.PHP_EOL.$times.PHP_EOL.$total_time.PHP_EOL.$questions.PHP_EOL.$answers.PHP_EOL.$date.PHP_EOL, FILE_APPEND | LOCK_EX);

  // $sql = "SELECT cl.id FROM $claim_table cl WHERE (cl.taken_flag = 1 AND cl.id = (SELECT a.current_task FROM Annotators a WHERE a.id=?))";
  $sql = "SELECT cl.id FROM $claim_table cl WHERE (cl.id = (SELECT a.current_task FROM Annotators a WHERE a.id=?))";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $result = $stmt->get_result();
  $err = "Error description, evidence submission get claim: ". $conn -> error;
  file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
  $row = $result->fetch_assoc();

  if($result->num_rows > 0){
    if ($row['id'] != $claim_id){
      #echo ('Claim ID and Annotator task do not match.  ');
      file_put_contents($file, 'Claim ID and Annotator task do not match.' .$date.PHP_EOL, FILE_APPEND | LOCK_EX);
    }
    $float_time = floatval($total_time);

    $float_time_adjusted = 0;
    if($float_time < 1200){
      $float_time_adjusted = $float_time;
    }

    $conn->begin_transaction();
    try {
      update_table($conn, "INSERT INTO $evidence_table(annotator, claim, verdict, evidence1, details1, evidence2, details2, evidence3, details3, search, hyperlinks, search_order, page_search, total_annotation_time, annotation_time_events, challenges, questions, answers, date_made) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?)", 'iisssssssssssssssss', $user_id, $claim_id, $verdict, $evidence1, $details1, $evidence2, $details2, $evidence3, $details3, $search, $hyperlinks, $order, $page_search, $total_time, $times, $challenge, $questions, $answers, $date);
      update_table($conn, "UPDATE Annotators SET current_task=0, finished_evidence_annotations=finished_evidence_annotations + 1, annotation_time = annotation_time + ? WHERE id=?",'ii',$float_time_adjusted, $user_id);
      update_table($conn, "UPDATE $claim_table SET taken_flag=0, evidence_annotators_num = evidence_annotators_num+1 WHERE id=?", 'i', $claim_id);
      $conn->commit();
    }catch (mysqli_sql_exception $exception) {
      $conn->rollback();
      file_put_contents($file, 'Error when trying to update tables submission! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
      throw $exception;
    }
  }else{
    file_put_contents($file, 'No claim for user found.'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
  }
  $conn -> close();
}
else if ($req == "evidence-resubmission"){

  // phpinfo();
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  $user_id = $_POST["user_id"];
  $claim_id = $_POST["claim_id"];

  file_put_contents($file, "Got Resubmission from " . $user_id. ' ' . $claim_id .PHP_EOL, FILE_APPEND | LOCK_EX);

  $evidence1 = $_POST['evidence1'];
  $details1 = $_POST['details1'];
  $evidence2 = $_POST['evidence2'];
  $details2 = $_POST['details2'];
  $evidence3 = $_POST['evidence3'];
  $details3 = $_POST['details3'];

  $verdict = $_POST['verdict'];
  $challenge = $_POST['challenge'];

  $search = $_POST['search'];
  $hyperlinks = $_POST['hyperlinks'];
  $order = $_POST['order'];
  $page_search = $_POST['page_search'];

  $times = $_POST['times'];
  $total_time = $_POST['total_time'];

  $questions = $_POST['questions'];
  $answers = $_POST['answers'];



  $evidence1 =   implode(" [SEP] ", json_decode($evidence1));
  $details1 = implode(" [SEP] ", json_decode($details1));

  if ($evidence2 != 'null'){
    $evidence2 =  implode(" [SEP] ", json_decode($evidence2));
    $details2 =  implode(" [SEP] ", json_decode($details2)) ;
  }else{
    $evidence2 = NULL;
    $details2 = NULL;
  }

  if($evidence3 != 'null'){
    $evidence3 = implode(" [SEP] ", json_decode($evidence3));
    $details3 =implode(" [SEP] ", json_decode($details3));
  }else{
    $evidence3 = NULL;
    $details3 = NULL;
  }
  // if ($challenge != 'null'){
  //   $challenge =  implode(" [SEP] ", json_decode($challenge)) ;
  // }else{
  //   $challenge = NULL;
  // }


  if ($search != 'null'){
    $search =  implode(" [SEP] ", json_decode($search)) ;
  }else{
    $search = NULL;
  }

  if ($hyperlinks != 'null'){
    $hyperlinks =  implode(" [SEP] ", json_decode($hyperlinks));
  }else{
    $hyperlinks = NULL;
  }
  if ($order != 'null'){
    $order =   implode(" [SEP] ", json_decode($order));
  }else{
    $order = NULL;
  }
  if ($page_search != 'null'){
    $page_search =  implode(" [SEP] ", json_decode($page_search));
  }else{
    $page_search = NULL;
  }
  if ($questions != 'null'){
    $questions = implode(" [SEP] ", json_decode($questions)) ;
    $answers =  implode(" [SEP] ", json_decode($answers));
  }else{
    $questions = NULL;
    $answers = NULL;
  }
  if ($times != 'null'){
    $times = implode(" [SEP] ", json_decode($times));
  }else{
    $times = NULL;
  }

  file_put_contents($file, $user_id.PHP_EOL.$claim_id.PHP_EOL.$evidence1.PHP_EOL.$details1.PHP_EOL.$evidence2.PHP_EOL.$details2.PHP_EOL.$evidence3.PHP_EOL.$details3.PHP_EOL.$verdict.PHP_EOL.$challenge.PHP_EOL.$search.PHP_EOL.$hyperlinks.PHP_EOL.$order.PHP_EOL.$page_search.PHP_EOL.$times.PHP_EOL.$total_time.PHP_EOL.$questions.PHP_EOL.$answers.PHP_EOL.$date.PHP_EOL, FILE_APPEND | LOCK_EX);

  $sql = "SELECT id FROM $evidence_table WHERE claim = ? AND annotator = ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii",$claim_id, $user_id);
  $stmt->execute();
  $result = $stmt->get_result();
  $err = "Error description, evidence resubmission get claim: ". $conn -> error;
  file_put_contents($file, $err.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
  $row = $result->fetch_assoc();

  if($result->num_rows > 0){
    $float_time = floatval($total_time);

    $conn->begin_transaction();
    try {
      update_table($conn, "UPDATE $evidence_table SET verdict=?, evidence1=?, details1=?, evidence2=?, details2=?, evidence3=?, details3=?, search=?, hyperlinks=?, search_order=?, page_search=?, total_annotation_time=?, annotation_time_events=?, challenges=?, questions=?, answers=?, date_modified=? WHERE id = ?", 'sssssssssssssssssi', $verdict, $evidence1, $details1, $evidence2, $details2, $evidence3, $details3, $search, $hyperlinks, $order, $page_search, $total_time, $times, $challenge, $questions, $answers, $date, $row['id']);
      // update_table($conn, "INSERT INTO Evidence(annotator, claim, verdict, evidence1, details1, evidence2, details2, evidence3, details3, search, hyperlinks, search_order, page_search, total_annotation_time, annotation_time_events, challenges, questions, answers, date_made) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?)", 'iisssssssssssssssss', $user_id, $claim_id, $verdict, $evidence1, $details1, $evidence2, $details2, $evidence3, $details3, $search, $hyperlinks, $order, $page_search, $total_time, $times, $challenge, $questions, $answers, $date);
      // update_table($conn, "UPDATE Annotators SET current_task=0, finished_evidence_annotations=finished_evidence_annotations + 1, annotation_time = annotation_time + ? WHERE id=?",'ii',$float_time, $user_id);
      // update_table($conn, "UPDATE Claims SET taken_flag=0, evidence_annotators_num = evidence_annotators_num+1 WHERE id=?", 'i', $claim_id);
      $conn->commit();
    }catch (mysqli_sql_exception $exception) {
      $conn->rollback();
      file_put_contents($file, 'Error when trying to update tables submission! Rollback...'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
      throw $exception;
    }
  }else{
    file_put_contents($file, 'No claim for user found.'.$date.PHP_EOL, FILE_APPEND | LOCK_EX);
  }
  $conn -> close();
}
else if ($req == "reload-evidence"){

  $user_id = $_GET["user_id"];
  $servername = "localhost";
  $username = $db_params['user'];
  $password = $db_params['password'];
  $dbname = $db_params['database'];

  $back_count = $_GET['back_count'];# - 1;


  file_put_contents($file, "Reload Evidence: " . $user_id. ' ' .PHP_EOL, FILE_APPEND | LOCK_EX);


  $conn = new mysqli($servername, $username, $password, $dbname);

  if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
  }

  $sql = "SELECT id, claim, verdict, evidence1, details1, evidence2, details2, evidence3, details3, search, hyperlinks, search_order, page_search, total_annotation_time, annotation_time_events, challenges, questions, answers, date_made FROM $evidence_table WHERE annotator = ? AND date_made  > DATE_SUB(CURDATE(), INTERVAL 1 DAY) ORDER BY date_made DESC LIMIT 1 OFFSET ?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("ii", $user_id, $back_count);
  $stmt->execute();
  $result = $stmt->get_result();

  $row = $result->fetch_assoc();
  //echo $row[1];
  if($result->num_rows > 0){
    $sql = "SELECT claim FROM $claim_table WHERE id = ?";
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("i", $row['claim']);
    $stmt->execute();
    $result = $stmt->get_result();

    $claim = $result->fetch_assoc();
    echo json_encode(array($row['claim'], $claim['claim'], $row['verdict'], $row['evidence1'], $row['details1'], $row['evidence2'], $row['details2'], $row['evidence3'], $row['details3'], $row['search'], $row['hyperlinks'], $row['search_order'], $row['page_search'], $row['total_annotation_time'], $row['annotation_time_events'], $row['challenges'],  $row['questions'], $row['answers']));
  }else{
    echo json_encode(array(-1));
  }
}
else{
  file_put_contents($file, 'Could not match request.' .$date.PHP_EOL, FILE_APPEND | LOCK_EX);
  #echo "Not found";
}

?>
