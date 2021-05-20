<?php

function compute_precision($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence, $gold_evidence2, $gold_evidence3){
  $precision_count = 0;
  $precision_total = 0;
  foreach ($pred_evidence as $key => $pred){
    foreach ($pred as $key2 => $eve)
    {
      if (in_array($eve, $gold_evidence[$key]) || in_array($eve, $gold_evidence2[$key]) || in_array($eve, $gold_evidence3[$key])){
        $precision_count +=1;
      }
      $precision_total +=1;
    }
  }
  foreach ($pred_evidence2 as $key => $pred){
    foreach ($pred as $key2 => $eve)
    {
      if (in_array($eve, $gold_evidence[$key]) || in_array($eve, $gold_evidence2[$key]) || in_array($eve, $gold_evidence3[$key])){
        $precision_count +=1;
      }
      $precision_total +=1;
    }
  }
  foreach ($pred_evidence3 as $key => $pred){
    foreach ($pred as $key2 => $eve)
    {
      if (in_array($eve, $gold_evidence[$key]) || in_array($eve, $gold_evidence2[$key]) || in_array($eve, $gold_evidence3[$key])){
        $precision_count +=1;
      }
      $precision_total +=1;
    }
  }

  $precision_score = $precision_count / $precision_total;

  return $precision_score;
}

function compute_recall($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence){
  $recall_count = 0;
  $recall_total = 0;
  foreach ($gold_evidence as $key => $gold){
    if($gold==['']){
      continue;
    }
    $recall_count +=1;
    $recall_total +=1;
    $in_1 = 1;
    $in_2 = 1;
    $in_3 = 1;
    foreach ($gold as $key2 => $g)
    {
      if (!in_array($g, $pred_evidence[$key])){
        $in_1 =0;
        break;
      }
    }
    foreach ($gold as $key2 => $g)
    {
      if (!in_array($g, $pred_evidence2[$key])){
        $in_2 =0;
        break;
      }
    }
    foreach ($gold as $key2 => $g)
    {
      if (!in_array($g, $pred_evidence3[$key])){
        $in_3 =0;
        break;
      }
    }
    if($in_1==0 && $in_2==0 && $in_3==0){
      $recall_count -=1;
    }
  }
  return array($recall_count, $recall_total);
}

function calculate_scores($conn, $user, $phase, $phase_num){
  $sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, claim, challenges FROM CalibrationEvidence ev WHERE annotator=?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $user);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();

  $pred_verdicts  = array();
  $pred_evidence = array();
  $pred_evidence2 = array();
  $pred_evidence3 = array();
  $pred_challenge = array();

  while($row = $result_anno1->fetch_assoc())
  {
    if (in_array($row['claim'], $phase)){
      $pred_verdicts[$row['claim']] = $row['verdict'];
      $pred_challenge[$row['claim']] = $row['challenges'];
      $pred_evidence[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence1']));
      $pred_evidence2[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence2']));
      $pred_evidence3[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence3']));
    }
  }

  $sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, claim, challenges FROM CalibrationGoldEvidence ev";
  $stmt= $conn->prepare($sql);
  $stmt->execute();
  $result_anno2 = $stmt->get_result();

  $gold_verdicts = array();
  $gold_challenge = array();
  $gold_evidence = array();
  $gold_evidence2 = array();
  $gold_evidence3 = array();
  while($row = $result_anno2->fetch_assoc())
  {
    if (in_array($row['claim'], $phase)){
      $gold_verdicts[$row['claim']] = $row['verdict'];
      $gold_evidence[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence1']));
      $gold_evidence2[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence2']));
      $gold_evidence3[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['evidence3']));
      $gold_challenge[$row['claim']] = get_main_evidence(explode(" [SEP] ", $row['challenges']));
    }
  }


  $correct_challenge = 0;
  $length = count($pred_challenge);
  foreach ($pred_challenge as $key => $pred)
  {
    if (in_array($pred, $gold_challenge[$key])){
      $correct_challenge +=1;
    }
  }
  $challenge_score = $correct_challenge / $length;

  $correct = 0;
  $length = count($pred_verdicts);
  foreach ($pred_verdicts as $key => $pred)
  {
    if ($pred == $gold_verdicts[$key]){
      $correct +=1;
    }
  }
  $score = $correct / $length;


  list($recall_count1, $recall_total1) = compute_recall($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence);
  list($recall_count2, $recall_total2) = compute_recall($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence2);
  list($recall_count3, $recall_total3) = compute_recall($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence3);


  $recall_count = $recall_count1 + $recall_count2 + $recall_count3;
  $recall_total = $recall_total1 + $recall_total2 + $recall_total3;
  $recall_score = $recall_count / $recall_total;

  $precision_score = compute_precision($pred_evidence, $pred_evidence2, $pred_evidence3, $gold_evidence, $gold_evidence2, $gold_evidence3);

  $f1_score = (2 * $precision_score * $recall_score) / ($precision_score + $recall_score);

  $score_string =  $score . ' [SEP] ' . $recall_score . ' [SEP] ' . $precision_score . ' [SEP] ' . $f1_score . ' [SEP] ' . $challenge_score . ' [SEP] ' . $recall_count;

  // echo $score_string;

  $conn->begin_transaction();
  try {
    if ($phase_num == 1){
      $sql = "UPDATE Annotators SET calibration_score=? WHERE id=?";
    }else if ($phase_num == 2){
      $sql = "UPDATE Annotators SET calibration_score_2=? WHERE id=?";
    }
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("si", $score_string, $_SESSION["user"]);
    $stmt->execute();
    $conn->commit();
  }catch (mysqli_sql_exception $exception) {
    $conn->rollback();
    throw $exception;
  }
  return array($score, $recall_score, $precision_score, $f1_score, $challenge_score, $recall_count);
}

function get_main_evidence($evidence){
  $evidence_new = array();
  foreach ($evidence as &$value) {
    if((!strpos($value, ' [CON] ')) && (strpos($value,'_title') !== false || strpos($value,'_header_') !== false || strpos($value,'_section') !== false)){
      continue;
    }else{
      array_push($evidence_new,  explode(" [CON] ", $value)[0]);
    }
  }
  return $evidence_new;
}

function get_main_evidence_and_details($evidence, $details){
  $evidence_new = array();
  $details_new = array();
  foreach ($evidence as $key=>&$value) {
    if((!strpos($value, ' [CON] ')) && (strpos($value,'_title') !== false || strpos($value,'_header_') !== false || strpos($value,'_section') !== false)){
      continue;
    }else{
      array_push($evidence_new,  explode(" [CON] ", $value)[0]);
      array_push($details_new, $details[$key]);
    }
  }
  if(!strpos($value, ' [CON] ')){
    return array($evidence_new, $details_new);
  }else{
      return array($evidence_new, $details);
  }
}

function get_context($evidence){
  $evidence_context = array();
  foreach ($evidence as &$value) {
    $parts =  explode(" [CON] ", $value);
    $evidence_context[$parts[0]] = array_slice($parts, 1);
  }
  return $evidence_context;
}

function convert_old_details($evidence_main, $details){

  if(count($evidence_main) == 0){
    return $details;
  }
  if(!strpos($details[0], '[CON]')){
    $details_new = array();
    for($i = 0; $i < count($evidence_main); ++$i) {
      $details_new[$evidence_main[$i]] = $details[$i];
    }
  }else{
    $details_new = array();
    for($i = 0; $i < count($details); ++$i) {
      $curr = explode(" [CON] ", $details[$i]);
      $details_new[$curr[0]] = $curr[1];
    }
  }
  return $details_new;
}

session_start();

if (!isset($_SESSION["user"])){
  echo file_get_contents('login.html');
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


if ($_GET["request"] != "load-highlight"){
  $current_issue = 0;
  if (isset($_GET["open_issue"])){
    $current_issue =  $_GET["open_issue"];
  }else{
    $current_issue = 0;
  }

  if (isset($_GET["phase"])){
    $_SESSION['phase'] =  $_GET["phase"];
  } else if (!isset($_SESSION['phase'])){
    $_SESSION['phase'] =  1;
  }
}


$sql = "SELECT annotator_name, finished_calibration, calibration_score, calibration_score_2, annotation_mode FROM Annotators WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $_SESSION["user"]);
$stmt->execute();
$annotator1_result = $stmt->get_result();
$annotator1_row = $annotator1_result->fetch_assoc();
$annotator1 = $annotator1_row['annotator_name'];
$finished_calibration = $annotator1_row['finished_calibration'];
$annotation_mode = $annotator1_row['annotation_mode'];

if($finished_calibration < $_SESSION['phase'] || $annotation_mode !='evidence'){
  echo $finished_calibration;
  echo $_SESSION['phase'];
  echo 'Please finish your calibration annotations for that given phase first. You can then see your statistics here.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}

if($_SESSION['phase'] ==  1){
  $calibration_table = "CalibrationEvidenceClaimsP1";
  $claim_id_map = array(1,2, 3, 4,5,6,7, 8, 9 ,10);
  $calibration_score =  $annotator1_row['calibration_score'];
  $comments = array();
}else if ($_SESSION['phase'] ==  2){
  $calibration_table = "CalibrationEvidenceClaimsP2";
  $claim_id_map = array(64,66,67,68,69,70,71,72,73,74,75,76);
  $calibration_score =  $annotator1_row['calibration_score_2'];
  $comments = array();
}

if($calibration_score == 0 && $finished_calibration == 1 && $_SESSION['phase'] ==  1  && $annotation_mode == 'evidence'){
  $score_array = calculate_scores($conn, $_SESSION["user"], $claim_id_map, 1);
}else if($calibration_score==0 && $finished_calibration== 2 && $_SESSION['phase'] ==  2  && $annotation_mode == 'evidence'){
  $score_array = calculate_scores($conn, $_SESSION["user"], $claim_id_map, 2);
}
else if ($calibration_score !=0){
  $score_array = explode(" [SEP] ", $calibration_score);
}
$calibration_score = $score_array[0];
$recall_score = $score_array[1];
$precision_score = $score_array[2];
$f1_score = $score_array[3];
$challenge_score = $score_array[4];
$recall_count = $score_array[5];

// }


$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, claim, challenges FROM CalibrationEvidence ev WHERE claim = ? AND annotator=?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("ii", $claim_id_map[$current_issue],$_SESSION["user"]);#, $_SESSION["user"]);
$stmt->execute();
$result_anno1 = $stmt->get_result();
$anno1 = $result_anno1->fetch_assoc();


$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, claim, challenges FROM CalibrationGoldEvidence ev WHERE claim = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $claim_id_map[$current_issue]);
$stmt->execute();
$result_anno2 = $stmt->get_result();
$anno2 = $result_anno2->fetch_assoc();

$sql = "SELECT claim, data_source FROM $calibration_table WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno2['claim']);
$stmt->execute();
$result_claim = $stmt->get_result();
$claim = $result_claim->fetch_assoc()['claim'];


$all_gold_annotations = array_merge(get_main_evidence(explode(" [SEP] ", $anno2['evidence1'])), get_main_evidence(explode(" [SEP] ", $anno2['evidence2'])), get_main_evidence(explode(" [SEP] ", $anno2['evidence3'])));
$all_predicted_annotations = array_merge(get_main_evidence(explode(" [SEP] ", $anno1['evidence1'])), get_main_evidence(explode(" [SEP] ", $anno1['evidence2'])), get_main_evidence(explode(" [SEP] ", $anno1['evidence3'])));



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

  <script type="text/javascript">
  $.ajaxSetup({async:false});

  $(function () {
    $('[data-toggle="popover"]').popover()
  })
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  })
  $('select').selectpicker();


  function redraw_annotations(type, identifier, annotations, iframe){
    if (annotations != null){
      for (var i = 0; i < annotations.length; i++) {
        $(iframe).find(type).filter(function() {
          var raw_id= $(this).find("span").text();
          var is_right = raw_id === annotations[i];
          if (is_right){
            $(this).css( "background-color", 'yellow').css('outline', '2px solid black');//css('border', '2px solid black');
          }
          ;
        });
      }
    }
  }

  function reload_elements(iframe_id, anno_id){
if ($(anno_id).text() != ''){
    var evidence = JSON.parse($(anno_id).text());
    var iframe_1 = $(iframe_id)[0].contentWindow.document;
    redraw_annotations('td', '_cell_', evidence, iframe_1);
    redraw_annotations('th', '_cell_', evidence, iframe_1);
    redraw_annotations('p', '_sentence_', evidence,  iframe_1);
    redraw_annotations('li', '_item_', evidence,  iframe_1);
    redraw_annotations('caption', '_table_caption_', evidence,  iframe_1);
  }
  }

  $(window).on('load', function() {
    reload_elements('#ev-set1-iframe', '#evidence-info-1');
    reload_elements('#ev-set1-iframe-gold', '#evidence-info-1-gold');
    reload_elements('#ev-set2-iframe', '#evidence-info-2');
    reload_elements('#ev-set2-iframe-gold', '#evidence-info-2-gold');
    reload_elements('#ev-set3-iframe', '#evidence-info-3');
    reload_elements('#ev-set3-iframe-gold', '#evidence-info-3-gold');
    $('#ev-set1-iframe').on("load", function() {
      reload_elements('#ev-set1-iframe', '#evidence-info-1');
    });
    $('#ev-set1-iframe-gold').on("load", function() {
      reload_elements('#ev-set1-iframe-gold', '#evidence-info-1-gold');
    });
    $('#ev-set2-iframe').on("load", function() {
      reload_elements('#ev-set2-iframe', '#evidence-info-2');
    });
    $('#ev-set2-iframe-gold').on("load", function() {
      reload_elements('#ev-set2-iframe-gold', '#evidence-info-2-gold');
    });
    $('#ev-set3-iframe').on("load", function() {
      reload_elements('#ev-set3-iframe', '#evidence-info-3');
    });
    $('#ev-set3-iframe-gold').on("load", function() {
      reload_elements('#ev-set3-iframe-gold', '#evidence-info-3-gold');
    });


  });



</script>


<style type="text/css">
.container-fluid {
  width: auto !important;
  margin-right: 10% !important;
  margin-left: 10% !important;
}

.list-in {
  background-color: chartreuse;

}

.list-out {
  background-color:#ff6666 ;
}


</style>
</head>
<body>
  <div class="container-fluid p-1">
    <div class="row">
      <div class="col-10">
        <a href="annotation-service/logout.php">Logout</a>
        <h3 class='text-center pb-5'>Evidence Annotation Calibration Evaluation</h3>
        <div class="text-center"><?php echo "Verdict accuracy: <b>" . $calibration_score . "</b>"?></div>
        <div class="text-center"><button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info" data-toggle="popover" data-html="true"  data-content="Scores if selected main challenge is in the set of all possible challenges given the gold evidence"></button> <?php echo "Challenge score: <b>" . $challenge_score . "</b>"?></div>
        <div class="text-center"><button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info" data-toggle="popover" data-html="true"  data-content="Fraction of correctly predicted evidence pieces among all predicted evidence pieces"></button>  <?php echo "Evidence precision: <b>" . $precision_score . "</b>"?></div>
        <div class="text-center"><button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info" data-toggle="popover" data-html="true"  data-content="Fraction of correctly predicted evidence sets (correct meaning containing all evidence pieces) among all gold evidence sets"></button> <?php echo "Evidence recall: <b>" . $recall_score . "</b>"?></div>
        <div class="text-center"><?php echo "Number of complete evidence sets: <b>" . $recall_count . "</b>"?></div>
        <hr style="height:5px;background-color: #333;">
        <div class= "text-center m-5 border border-secondary">
          <?php  echo "<b>" . $claim  . '</b>' . ' (' . $anno2['claim'] . ')'?>
        </div>
        <div class= " m-5 border border-primary">
          <?php
          if (array_key_exists($current_issue, $comments)){
            echo $comments[$current_issue];
          }
          ?>
        </div>
        <div class="m-5 border border-secondary">
          <div class="row">
            <div class="col-6 pl-2 bg-light">
              <p class="badge badge-primary float-right">You</p>
            </div>
            <div class="col-6 pr-2 bg-light">
              <p class="badge badge-primary float-right">Gold</p>
            </div>
          </div>
          <div class="row">
            <div class="col-6 pl-2 bg-light text-danger">
              <h4 class="float-left">Verdict: <?php echo $anno1['verdict']; ?></h4>
            </div>
            <div class="col-6 pr-2 bg-light text-danger">
              <h4 class="float-left">Verdict: <?php echo $anno2['verdict']; ?></h4>
            </div>
          </div>
          <div class="row">
            <div class="col-6 pl-2 bg-light text-danger">
              <h5 class='float-left'>Challenge: <?php echo $anno1['challenges']?></h5>
            </div>
            <div class="col-6 pr-2 bg-light text-danger">
              <h5 class='float-left'>Challenge options: <?php echo $anno2['challenges']?></h5>
            </div>
          </div>
          <div class="row">
            <div class="col-6 pl-2 bg-light">
              <h5 class="list-group-item-heading">Evidence Set 1</h5>
              <ol class="list-group">
                <?php
                if ($anno1['evidence1'] != ""){
                  list($evidence1, $details1) = get_main_evidence_and_details(explode(" [SEP] ", $anno1['evidence1']), explode(" [SEP] ", $anno1['details1']));
                  $evidence1_context = get_context(explode(" [SEP] ", $anno1['evidence1']));
                  $evidence1_details =  convert_old_details($evidence1, $details1);


                  foreach ($evidence1 as $i => $value) {
                    if($evidence1 == ''){
                      continue;
                    }
                    $eve_array = explode("_", $evidence1[$i]);
                    $title = str_replace(" ", "_", $eve_array[0]);

                    if (in_array($evidence1[$i], $all_gold_annotations ))
                    {
                      echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence1_' . $i . '"role="button" aria-expanded="false">';
                    }else{
                      echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence1_' . $i . '"role="button" aria-expanded="false">';
                    }
                    echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                    echo $evidence1_details[$evidence1[$i]];
                    echo '<div class="collapse bg-secondary border"  id="collapseevidence1_' . $i . '">';
                    foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                      echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                    }
                    echo '</div>';
                    echo '</li>';
                  }
                  echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence1" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                  echo '<div class="collapse" id="collapseevidence1"><div class="card card-body">
                  <span id="evidence-info-1"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set1-iframe" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                  }
                  ?>
                </ol>
              </div>
              <div class="col-6 pr-2 bg-light">
                <h5 class="list-group-item-heading">Evidence Set 1</h5>
                <ol class="list-group">
                  <?php
                  if ($anno2['evidence1'] != ""){
                    // echo json_encode(explode(" [SEP] ", $anno2['evidence1']));
                    // echo json_encode(explode(" [SEP] ", $anno2['details1']));
                    list($evidence1, $details1) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence1']), explode(" [SEP] ", $anno2['details1']));
                    //
                    // echo json_encode($evidence1);
                    // echo json_encode($details1);
                    $evidence1_context = get_context(explode(" [SEP] ", $anno2['evidence1']));
                    $evidence1_details =  convert_old_details($evidence1, $details1);



                    foreach ($evidence1 as $i => $value) {
                      if($evidence1 == ''){
                        continue;
                      }
                      $eve_array = explode("_", $evidence1[$i]);
                      $title = str_replace(" ", "_", $eve_array[0]);

                      if (in_array($evidence1[$i], $all_predicted_annotations ))
                      {
                        echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence1gold_' . $i . '"role="button" aria-expanded="false">';
                      }else{
                        echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence1gold_' . $i . '"role="button" aria-expanded="false">';
                      }
                      echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                      echo $evidence1_details[$evidence1[$i]];
                      echo '<div class="collapse bg-secondary border"  id="collapseevidence1gold_' . $i . '">';
                      foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                        echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                      }
                      echo '</div>';
                      echo '</li>';
                    }
                    echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence1-gold" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                    echo '<div class="collapse" id="collapseevidence1-gold"><div class="card card-body">
                    <span id="evidence-info-1-gold"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set1-iframe-gold" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                    }
                    ?>
                  </ol>
                </div>
              </div>
              <div class="row">
                <div class="col-6 pl-2 bg-light">
                  <h5 class="list-group-item-heading">Evidence Set 2</h5>
                  <ol class="list-group">
                    <?php
                    if ($anno1['evidence2'] != ""){
                      list($evidence2, $details2) = get_main_evidence_and_details(explode(" [SEP] ", $anno1['evidence2']), explode(" [SEP] ", $anno1['details2']));
                      $evidence2_context = get_context(explode(" [SEP] ", $anno1['evidence2']));
                      $evidence2_details =  convert_old_details($evidence2, $details2);



                      foreach ($evidence2 as $i => $value) {
                        if($evidence2 == ''){
                          continue;
                        }
                        $eve_array = explode("_", $evidence2[$i]);
                        $title = str_replace(" ", "_", $eve_array[0]);

                        if (in_array($evidence2[$i], $all_gold_annotations ))
                        {
                          echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence2_' . $i . '"role="button" aria-expanded="false">';
                        }else{
                          echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence2_' . $i . '"role="button" aria-expanded="false">';
                        }
                        echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence2[$i] . '</a>' . ' : ';
                        echo $evidence2_details[$evidence2[$i]];
                        echo '<div class="collapse bg-secondary border"  id="collapseevidence2_' . $i . '">';
                        foreach ($evidence2_context[$evidence2[$i]] as &$value) {
                          echo "<p class='ml-1'>" . $value .  ": " . $evidence2_details[$value] . "</p>";
                        }
                        echo '</div>';
                        echo '</li>';
                      }
                      echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence2" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                      echo '<div class="collapse" id="collapseevidence2"><div class="card card-body">
                      <span id="evidence-info-2"hidden>'. json_encode($evidence2) . '</span><iframe id="ev-set2-iframe" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                      }
                      ?>
                    </ol>
                  </div>
                  <div class="col-6 pr-2 bg-light">
                    <h5 class="list-group-item-heading">Evidence Set 2</h5>
                    <ol class="list-group">
                      <?php
                      if ($anno2['evidence2'] != ""){
                        list($evidence2, $details2) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence2']), explode(" [SEP] ", $anno2['details2']));
                        $evidence2_context = get_context(explode(" [SEP] ", $anno2['evidence2']));
                        $evidence2_details =  convert_old_details($evidence2, $details2);

                        foreach ($evidence2 as $i => $value) {
                          if($evidence2 == ''){
                            continue;
                          }
                          $eve_array = explode("_", $evidence2[$i]);
                          $title = str_replace(" ", "_", $eve_array[0]);

                          if (in_array($evidence2[$i], $all_predicted_annotations ))
                          {
                            echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence2gold_' . $i . '"role="button" aria-expanded="false">';
                          }else{
                            echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence2gold_' . $i . '"role="button" aria-expanded="false">';
                          }
                          echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence2[$i] . '</a>' . ' : ';
                          echo $evidence2_details[$evidence2[$i]];
                          echo '<div class="collapse bg-secondary border"  id="collapseevidence2gold_' . $i . '">';
                          foreach ($evidence2_context[$evidence2[$i]] as &$value) {
                            echo "<p class='ml-1'>" . $value .  ": " . $evidence2_details[$value] . "</p>";
                          }
                          echo '</div>';
                          echo '</li>';
                        }
                        echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence2-gold" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                        echo '<div class="collapse" id="collapseevidence2-gold"><div class="card card-body">
                        <span id="evidence-info-2-gold"hidden>'. json_encode($evidence2) . '</span><iframe id="ev-set2-iframe-gold" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                        }
                        ?>
                      </ol>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col-6 pl-2 bg-light">
                      <h5 class="list-group-item-heading">Evidence Set 3</h5>
                      <ol class="list-group">
                        <?php
                        if ($anno1['evidence3'] != ""){
                          list($evidence3, $details3) = get_main_evidence_and_details(explode(" [SEP] ", $anno1['evidence3']), explode(" [SEP] ", $anno1['details3']));
                          $evidence3_context = get_context(explode(" [SEP] ", $anno1['evidence3']));
                          $evidence3_details =  convert_old_details($evidence3, $details3);


                          foreach ($evidence3 as $i => $value) {
                            if($evidence3 == ''){
                              continue;
                            }
                            $eve_array = explode("_", $evidence3[$i]);
                            $title = str_replace(" ", "_", $eve_array[0]);

                            if (in_array($evidence3[$i], $all_gold_annotations ))
                            {
                              echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence3_' . $i . '"role="button" aria-expanded="false">';
                            }else{
                              echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence3_' . $i . '"role="button" aria-expanded="false">';
                            }
                            echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence3[$i] . '</a>' . ' : ';
                            echo $evidence3_details[$evidence3[$i]];
                            echo '<div class="collapse bg-secondary border"  id="collapseevidence3_' . $i . '">';
                            foreach ($evidence3_context[$evidence3[$i]] as &$value) {
                              echo "<p class='ml-1'>" . $value .  ": " . $evidence3_details[$value] . "</p>";
                            }
                            echo '</div>';
                            echo '</li>';
                          }
                          echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence3" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                          echo '<div class="collapse" id="collapseevidence3"><div class="card card-body">
                          <span id="evidence-info-3"hidden>'. json_encode($evidence3) . '</span><iframe id="ev-set3-iframe" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                          }
                          ?>
                        </ol>
                      </div>
                      <div class="col-6 pr-2 bg-light">
                        <h5 class="list-group-item-heading">Evidence Set 3</h5>
                        <ol class="list-group">
                          <?php
                          if ($anno2['evidence3'] != ""){
                            list($evidence3, $details3) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence3']), explode(" [SEP] ", $anno2['details3']));
                            $evidence3_context = get_context(explode(" [SEP] ", $anno2['evidence3']));
                            $evidence3_details =  convert_old_details($evidence3, $details3);



                            foreach ($evidence3 as $i => $value) {
                              if($evidence3 == ''){
                                continue;
                              }
                              $eve_array = explode("_", $evidence3[$i]);
                              $title = str_replace(" ", "_", $eve_array[0]);

                              if (in_array($evidence3[$i], $all_predicted_annotations ))
                              {
                                echo '<li class="list-group-item"  data-toggle="collapse" href="#collapseevidence3gold_' . $i . '"role="button" aria-expanded="false">';
                              }else{
                                echo '<li class="list-group-item list-out"  data-toggle="collapse" href="#collapseevidence3gold_' . $i . '"role="button" aria-expanded="false">';
                              }
                              echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence3[$i] . '</a>' . ' : ';
                              echo $evidence3_details[$evidence3[$i]];
                              echo '<div class="collapse bg-secondary border"  id="collapseevidence3gold_' . $i . '">';
                              foreach ($evidence3_context[$evidence3[$i]] as &$value) {
                                echo "<p class='ml-1'>" . $value .  ": " . $evidence3_details[$value] . "</p>";
                              }
                              echo '</div>';
                              echo '</li>';
                            }
                            echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence3-gold" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                            echo '<div class="collapse" id="collapseevidence3-gold"><div class="card card-body">
                            <span id="evidence-info-3-gold"hidden>'. json_encode($evidence3) . '</span><iframe id="ev-set3-iframe-gold" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                            }
                            ?>
                          </ol>
                        </div>
                      </div>
                    </div>

                  </div>
                  <div class="col-1 bg-success bg-light border text-center">
                    <h5 class="list-group-item-heading">Calibration Claims</h5>
                    <?php
                    // foreach ($inbox as &) {
                    for($i=0; $i<count($claim_id_map); $i++) {
                      if ($i == $current_issue){
                        echo "<a href='?open_issue=$i'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$i'> Claim $i
                        </a>";
                      }else{
                        echo "<a href='?open_issue=$i'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$i'> Claim $i
                        </a>";
                      }
                    }//da war $sub_email[abbr]
                    ?>
                    <h5 class="list-group-item-heading">Calibration Phase</h5>
                    <?php
                    // foreach ($inbox as &) {
                    for($i=1; $i<3; $i++) {
                      if ($i == $_SESSION['phase']){
                        echo "<a href='?phase=$i'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$i'> Phase $i
                        </a>";
                      }else{
                        echo "<a href='?phase=$i'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$i'> Phase $i
                        </a>";
                      }
                    }//da war $sub_email[abbr]
                    ?>
                  </div>
                </div>
              </div>

            </body>
            </html>
