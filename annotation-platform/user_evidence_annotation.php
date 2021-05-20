<?php
$evidence_table = "Evidence";
$claim_table = "Claims";

// $evidence_table = "CalibrationEvidence";
// $claim_table = "CalibrationClaims";

$claim_table2 = "CalibrationEvidenceClaimsP2";

function get_annotations_from_annotator($conn, $annotator_id){
  global $evidence_table, $claim_table;
  $sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, claim FROM $evidence_table ev WHERE annotator=?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $annotator_id);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();

  $pred_id_verdict = array();

  while($row = $result_anno1->fetch_assoc())
  {
    $pred_id_verdict[$row['claim']] = $row['verdict'];
  }
  return $pred_id_verdict;
}

function get_multiple_annotations($conn, $claim_list){
  global $evidence_table, $claim_table, $claim_table;
  $sql = "SELECT id FROM $claim_table  WHERE evidence_annotators_num >= ?";
  $stmt= $conn->prepare($sql);
  $annotations_num = 2;
  $stmt->bind_param("i", $annotations_num);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();

  $id_double_list = array();

  while($row = $result_anno1->fetch_assoc())
  {
    if (array_key_exists($row['id'], $claim_list)){
    $id_double_list[$row['id']] = $row['id'];
  }
  }

  // foreach ($id_double_list as $key => $value){
  // $sql = "SELECT annotator FROM $evidence_table  WHERE claim=?";
  // $stmt= $conn->prepare($sql);
  // $stmt->bind_param("i", $key);#, $_SESSION["user"]);
  // $stmt->execute();
  // $result_anno1 = $stmt->get_result();
  // $id_double_list[$key] = $result_anno1['annotator'];
  // }
  return $id_double_list;

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
}
else if ($_SESSION['annotation_mode'] != 'evidence'){
  echo 'Wrong annotator type. You are not authorized to use this tool.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}
else if ($_SESSION['finished_calibration'] != 2 || $_SESSION['active'] <= 0){
  echo 'You have not finished the calibration yet.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}
$db_params = parse_ini_file( dirname(__FILE__).'/annotation-service/db_params.ini', false);

$servername = "localhost";
$username = $db_params['user'];
$password = $db_params['password'];
$dbname = $db_params['database'];

$conn = new mysqli($servername, $username, $password, $dbname);


$current_issue = 0;
if (isset($_GET["open_issue"])){
  $current_issue =  $_GET["open_issue"];
}else{
  $current_issue = 0;
}

$annotator_id_verdict = get_annotations_from_annotator($conn, $_SESSION['user']);
$id_double_list = get_multiple_annotations($conn, $annotator_id_verdict);
$claim_id_map = array_keys($annotator_id_verdict);


$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, claim, challenges FROM $evidence_table ev WHERE claim = ? AND annotator=?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("ii", $current_issue, $_SESSION['user']);#, $_SESSION["user"]);
$stmt->execute();
$result_anno1 = $stmt->get_result();
$anno1 = $result_anno1->fetch_assoc();

$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, claim, challenges, annotator FROM $evidence_table ev WHERE claim = ? AND annotator!=?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("ii", $current_issue, $_SESSION['user']);#, $_SESSION["user"]);
$stmt->execute();
$result_anno2 = $stmt->get_result();
$anno2 = $result_anno2->fetch_assoc();



$sql = "SELECT claim FROM $claim_table WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno1['claim']);
$stmt->execute();
$result_claim = $stmt->get_result();
$claim = $result_claim->fetch_assoc()['claim'];

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
    if (annotations != null && annotations !=''){
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
      redraw_annotations('h2', '_section_',  evidence,  iframe_1);
      redraw_annotations('h3', '_section_',  evidence,  iframe_1);
      redraw_annotations('h4', '_section_',  evidence,  iframe_1);
      redraw_annotations('h5', '_section_',  evidence,  iframe_1);
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
  background-color: 	#D3D3D3;

}

.list-out {
  background-color:	#D3D3D3 ;
}


</style>
</head>
<body>
  <div class="container-fluid p-4">
    <div class="row">
      <div class="col-9">
        <a href="annotation-service/logout.php">Logout</a>
        <h3 class='text-center pb-5'>Evidence Annotation User Interface</h3>
        <hr style="height:5px;background-color: #333;">
        <div class= "text-center m-5 border border-secondary">
          <?php  echo "<b>" . $claim  . '</b>' . ' (' . $anno1['claim'] . ')'?>
        </div>
        <div class="m-5 border border-secondary">
          <div class="row">
            <div class="col-6 pl-2 bg-light">
              <p class="badge badge-primary float-right">You </p>
            </div>
            <div class="col-6 pr-2 bg-light">
              <p class="badge badge-primary float-right">Other Annotator  </p>
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


                  for($i=0; $i<count($evidence1); $i++) {
                    $eve_array = explode("_", $evidence1[$i]);
                    $title = str_replace(" ", "_", $eve_array[0]);

                  echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence1_' . $i . '"role="button" aria-expanded="false">';
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                  echo $evidence1_details[$evidence1[$i]];
                  echo '<div class="collapse bg-secondary border"  id="collapseevidence1_' . $i . '">';
                  foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                    echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                  }
                  echo '</div>';
                  echo "</li>";
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
                    list($evidence1, $details1) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence1']), explode(" [SEP] ", $anno2['details1']));
                    $evidence1_context = get_context(explode(" [SEP] ", $anno2['evidence1']));
                    $evidence1_details =  convert_old_details($evidence1, $details1);


                    for($i=0; $i<count($evidence1); $i++) {
                      $eve_array = explode("_", $evidence1[$i]);
                      $title = str_replace(" ", "_", $eve_array[0]);

                    echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence1gold_' . $i . '"role="button" aria-expanded="false">';
                    echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                    echo $evidence1_details[$evidence1[$i]];
                    echo '<div class="collapse bg-secondary border"  id="collapseevidence1gold_' . $i . '">';
                    foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                      echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                    }
                    echo '</div>';
                    echo "</li>";
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
                      $evidence1_context = get_context(explode(" [SEP] ", $anno1['evidence2']));
                      $evidence1_details =  convert_old_details($evidence1, $details1);


                      for($i=0; $i<count($evidence1); $i++) {
                        $eve_array = explode("_", $evidence1[$i]);
                        $title = str_replace(" ", "_", $eve_array[0]);

                      echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence2_' . $i . '"role="button" aria-expanded="false">';
                      echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                      echo $evidence1_details[$evidence1[$i]];
                      echo '<div class="collapse bg-secondary border"  id="collapseevidence2_' . $i . '">';
                      foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                        echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                      }
                      echo '</div>';
                      echo "</li>";
                    }
                      echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence2" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                      echo '<div class="collapse" id="collapseevidence2"><div class="card card-body">
                      <span id="evidence-info-2"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set2-iframe" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                      }
                      ?>
                  </div>
                  <div class="col-6 pr-2 bg-light">
                    <h5 class="list-group-item-heading">Evidence Set 2</h5>
                    <ol class="list-group">
                      <?php
                      if ($anno2['evidence2'] != ""){
                        list($evidence1, $details1) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence2']), explode(" [SEP] ", $anno2['details2']));
                        $evidence1_context = get_context(explode(" [SEP] ", $anno2['evidence2']));
                        $evidence1_details =  convert_old_details($evidence1, $details1);


                        for($i=0; $i<count($evidence1); $i++) {
                          $eve_array = explode("_", $evidence1[$i]);
                          $title = str_replace(" ", "_", $eve_array[0]);

                        echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence2gold_' . $i . '"role="button" aria-expanded="false">';
                        echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                        echo $evidence1_details[$evidence1[$i]];
                        echo '<div class="collapse bg-secondary border"  id="collapseevidence2gold_' . $i . '">';
                        foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                          echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                        }
                        echo '</div>';
                        echo "</li>";
                      }
                        echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence2-gold" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                        echo '<div class="collapse" id="collapseevidence2-gold"><div class="card card-body">
                        <span id="evidence-info-2-gold"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set2-iframe-gold" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
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
                          list($evidence2, $details2) = get_main_evidence_and_details(explode(" [SEP] ", $anno1['evidence3']), explode(" [SEP] ", $anno1['details3']));
                          $evidence1_context = get_context(explode(" [SEP] ", $anno1['evidence3']));
                          $evidence1_details =  convert_old_details($evidence1, $details1);


                          for($i=0; $i<count($evidence1); $i++) {
                            $eve_array = explode("_", $evidence1[$i]);
                            $title = str_replace(" ", "_", $eve_array[0]);

                          echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence3_' . $i . '"role="button" aria-expanded="false">';
                          echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                          echo $evidence1_details[$evidence1[$i]];
                          echo '<div class="collapse bg-secondary border"  id="collapseevidence3_' . $i . '">';
                          foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                            echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                          }
                          echo '</div>';
                          echo "</li>";
                        }
                          echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence3" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                          echo '<div class="collapse" id="collapseevidence3"><div class="card card-body">
                          <span id="evidence-info-3"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set3-iframe" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                          }
                          ?>
                        </ol>
                      </div>
                      <div class="col-6 pr-2 bg-light">
                        <h5 class="list-group-item-heading">Evidence Set 3</h5>
                        <ol class="list-group">
                          <?php
                          if ($anno2['evidence3'] != ""){
                            list($evidence1, $details1) = get_main_evidence_and_details(explode(" [SEP] ", $anno2['evidence3']), explode(" [SEP] ", $anno2['details3']));
                            $evidence1_context = get_context(explode(" [SEP] ", $anno2['evidence3']));
                            $evidence1_details =  convert_old_details($evidence1, $details1);

                            for($i=0; $i<count($evidence1); $i++) {
                              $eve_array = explode("_", $evidence1[$i]);
                              $title = str_replace(" ", "_", $eve_array[0]);

                            echo '<li class="list-group-item" data-toggle="collapse" href="#collapseevidence3gold_' . $i . '"role="button" aria-expanded="false">';
                            echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                            echo $evidence1_details[$evidence1[$i]];
                            echo '<div class="collapse bg-secondary border"  id="collapseevidence3gold_' . $i . '">';
                            foreach ($evidence1_context[$evidence1[$i]] as &$value) {
                              echo "<p class='ml-1'>" . $value .  ": " . $evidence1_details[$value] . "</p>";
                            }
                            echo '</div>';
                            echo "</li>";
                          }
                            echo  '<a class="btn btn-primary" data-toggle="collapse" href="#collapseevidence3-gold" role="button" aria-expanded="false" aria-controls="collapseExample">  Show Article </a>';
                            echo '<div class="collapse" id="collapseevidence3-gold"><div class="card card-body">
                            <span id="evidence-info-3-gold"hidden>'. json_encode($evidence1) . '</span><iframe id="ev-set3-iframe-gold" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php?title=' . $title . '"></iframe></div></div>';
                            }
                            ?>
                          </ol>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="col-1 bg-success bg-light border text-center">
                    <h5 class="list-group-item-heading">Claims</h5>
                    <?php
                    foreach ($annotator_id_verdict as $key => $value) {
                      if ($key == $current_issue){
                        echo "<a href='?open_issue=$key'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$key'> Claim $key
                        </a>";
                      }else{
                        echo "<a href='?open_issue=$key'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$key'> Claim $key
                        </a>";
                      }
                    }
                    ?>
                  </div>
                  <div class="col-1 bg-success bg-light border text-center">
                    <h5 class="list-group-item-heading">QA Claims</h5>
                    <?php
                    foreach ($id_double_list as $key => $value) {
                      if ($key == $current_issue){
                        echo "<a href='?open_issue=$key'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$key'> Claim $key
                        </a>";
                      }else{
                        echo "<a href='?open_issue=$key'
                        type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                        title='$key'> Claim $key
                        </a>";
                      }
                    }
                    ?>
                  </div>
                </div>
              </div>
            </body>
            </html>
