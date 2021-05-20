<?php
session_start();

if (!isset($_SESSION["user"])){
echo file_get_contents('login.html');
echo "<!--";
}

$db_params = parse_ini_file( dirname(__FILE__).'/annotation-service/db_params.ini', false);

$servername = "localhost";
$username = $db_params['user'];
$password = $db_params['password'];
$dbname = $db_params['database'];

$conn = new mysqli($servername, $username, $password, $dbname);

$verdict_mismatches_file = file_get_contents("annotation-service/evidence_annotation_verdict_mismatches_P2.json");
$verdict_mismatches = json_decode($verdict_mismatches_file, true);
$claim_table = "CalibrationEvidenceClaimsP2";

$current_issue = 0;
if (isset($_GET["open_issue"])){
  $current_issue =  $_GET["open_issue"];
}else{
  $current_issue = 0;
}

$verdict_mismatch = $verdict_mismatches[$current_issue];

$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, claim, challenges FROM CalibrationEvidence ev WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $verdict_mismatch[0]);
$stmt->execute();
$result_anno1 = $stmt->get_result();
$anno1 = $result_anno1->fetch_assoc();

$verdict_mismatch = $verdict_mismatches[$current_issue];
$sql = "SELECT id, verdict, evidence1, evidence2, evidence3, details1, details2, details3, annotator, challenges FROM CalibrationEvidence ev WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $verdict_mismatch[1]);
$stmt->execute();
$result_anno2 = $stmt->get_result();
$anno2 = $result_anno2->fetch_assoc();

$sql = "SELECT claim FROM $claim_table WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno1['claim']);
$stmt->execute();
$result_claim = $stmt->get_result();
$claim = $result_claim->fetch_assoc()['claim'];

$sql = "SELECT annotator_name FROM Annotators WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno1['annotator']);
$stmt->execute();
$annotator1_result = $stmt->get_result();
$annotator1 = $annotator1_result->fetch_assoc()['annotator_name'];

$sql = "SELECT annotator_name FROM Annotators WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno2['annotator']);
$stmt->execute();
$annotator2_result = $stmt->get_result();
$annotator2 = $annotator2_result->fetch_assoc()['annotator_name'];


if ($_SERVER['REQUEST_METHOD'] == "POST"){
  if (isset($_POST['a1'])){
    $adjudication = 'Annotator1 correct';
  }
  else if (isset($_POST['a2'])){
    $adjudication = 'Annotator2 correct.';
  }
  else if (isset($_POST['a3'])){
    $adjudication = 'Both correct.';
  }
  else if (isset($_POST['a1'])){
    $adjudication = 'Both wrong.';
  }

  $sql = "INSERT INTO Adjudication(annotator, mode, annotation1, annotation2, adjudication, comment) VALUES(?, 'evidence', ?, ?, ?, ?)";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("iiiss", $_SESSION['user'], $anno1['id'], $anno2['id'], $adjudication, $_POST['comment']);
  $stmt->execute();
  // $result_comment = $stmt->get_result();
  // $comment = $result_comment->fetch_assoc();

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

  <style type="text/css">
  .container-fluid {
    width: auto !important;
    margin-right: 10% !important;
    margin-left: 10% !important;
  }


  </style>
</head>
<body>
  <div class="container-fluid p-3">
    <div class="row">
      <div class="col-9 m-5">
        <div class= "text-center m-5 border border-secondary">
          <?php  echo "<b>" . $claim  . '</b>' . ' (' . $anno1['claim'] . ')'?>
        </div>

        <div class= " m-5 border border-primary">
          <?php
          $sql = "SELECT adjudication, comment, annotator FROM Adjudication WHERE ? = annotation1 AND ? = annotation2";
          $stmt= $conn->prepare($sql);
          $stmt->bind_param("ii", $anno1['id'], $anno2['id']);
          $stmt->execute();
          $result_comm1 = $stmt->get_result();

          while ($data = $result_comm1->fetch_assoc()){
            $sql = "SELECT annotator_name FROM Annotators WHERE id = ?";
            $stmt= $conn->prepare($sql);
            $stmt->bind_param("i", $data['annotator']);
            $stmt->execute();
            $comment_ann_result = $stmt->get_result();
            $comment_ann = $comment_ann_result->fetch_assoc()['annotator_name'];

            echo $comment_ann . ": " . $data['adjudication'] . "; " . $data['comment'];
            echo '<br>';
          }


          ?>
        </div>
        <div class="m-5 border border-secondary">
        <div class="row">
          <div class="col-6 pl-2 bg-light">
            <p class="badge badge-primary float-right"><?php echo $annotator1; ?></p>
          </div>
          <div class="col-6 pr-2 bg-light">
            <p class="badge badge-primary float-right"><?php echo $annotator2; ?></p>
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
            <h4 class="float-left">Challenge: <?php echo $anno1['challenges']; ?></h4>
          </div>
          <div class="col-6 pr-2 bg-light text-danger">
            <h4 class="float-left">Challenge: <?php echo $anno2['challenges']; ?></h4>
          </div>
        </div>
        <div class="row">
          <div class="col-6 pl-2 bg-light">
            <h5 class="list-group-item-heading">Evidence Set 1</h5>
            <ol class="list-group">
              <?php
              if ($anno1['evidence1'] != ""){
                $evidence1 = explode(" [SEP] ", $anno1['evidence1']);
                $evidence1_details = explode(" [SEP] ", $anno1['details1']);
                for($i=0; $i<count($evidence1); $i++) {
                  $title = str_replace(" ", "_", explode("_", $evidence1[$i])[0]);
                  echo "<li class='list-group-item'>";
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                  echo $evidence1_details[$i];
                  echo "</li>";
                }
              }
              ?>
            </ol>
          </div>
          <div class="col-6 pr-2 bg-light">
            <h5 class="list-group-item-heading">Evidence Set 1</h5>
            <ol class="list-group">
              <?php
              if ($anno2['evidence1'] != ""){
                $evidence1 = explode(" [SEP] ", $anno2['evidence1']);
                $evidence1_details = explode(" [SEP] ", $anno2['details1']);
                for($i=0; $i<count($evidence1); $i++) {
                  $title = str_replace(" ", "_", explode("_", $evidence1[$i])[0]);
                  echo "<li class='list-group-item'>";
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence1[$i] . '</a>' . ' : ';
                  echo $evidence1_details[$i];
                  echo "</li>";
                }
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
                $evidence2 = explode(" [SEP] ", $anno1['evidence2']);
                $evidence2_details = explode(" [SEP] ", $anno1['details2']);
                for($i=0; $i<count($evidence1); $i++) {
                    $title = str_replace(" ", "_", explode("_", $evidence2[$i])[0]);
                  echo "<li class='list-group-item'>";
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence2[$i] . '</a>' . ' : ';
                  echo $evidence2_details[$i];
                  echo "</li>";
                }
              }
              ?>
            </ol>
          </div>
          <div class="col-6 pr-2 bg-light">
            <h5 class="list-group-item-heading">Evidence Set 2</h5>
            <ol class="list-group">
              <?php
              if ($anno2['evidence2'] != ""){
                $evidence2 = explode(" [SEP] ", $anno2['evidence2']);
                $evidence2_details = explode(" [SEP] ", $anno2['details2']);
                for($i=0; $i<count($evidence1); $i++) {
                  echo "<li class='list-group-item'>";
                  $title = str_replace(" ", "_", explode("_", $evidence2[$i])[0]);
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence2[$i] . '</a>' . ' : ';
                  echo $evidence2_details[$i];
                  echo "</li>";
                }
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
                $evidence3 = explode(" [SEP] ", $anno1['evidence3']);
                $evidence3_details = explode(" [SEP] ", $anno1['details3']);
                for($i=0; $i<count($evidence1); $i++) {
                  echo "<li class='list-group-item'>";
                  $title = str_replace(" ", "_", explode("_", $evidence3[$i])[0]);
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence3[$i] . '</a>' . ' : ';
                  echo $evidence3_details[$i];
                  echo "</li>";
                }
              }
              ?>
            </ol>
          </div>
          <div class="col-6 pr-2 bg-light">
            <h5 class="list-group-item-heading">Evidence Set 3</h5>
            <ol class="list-group">
              <?php
              if ($anno2['evidence3'] != ""){
                $evidence3 = explode(" [SEP] ", $anno2['evidence3']);
                $evidence3_details = explode(" [SEP] ", $anno2['details3']);
                for($i=0; $i<count($evidence3); $i++) {
                  echo "<li class='list-group-item'>";
                  $title = str_replace(" ", "_", explode("_", $evidence3[$i])[0]);
                  echo '<a href=http://mediawiki.feverous.co.uk/index.php?title=' . $title . '>' .$evidence3[$i] . '</a>' . ' : ';
                  echo $evidence3_details[$i];
                  echo "</li>";
                }
              }
              ?>
            </ol>
          </div>
        </div>
      </div>

        <div class="text-center p-5">
          <form action="#" method="post">
            <label for="exampleInputPassword1">Notes/Comments:</label>
            <input type="text" name="comment" class="form-control" id="notes" placeholder="Notes...">
            <br>
            <button name="a1" type='submit' class="btn btn-primary center" id='adjudication-a1'> Annotation 1 is correct.</button>
            <button name="a2" type='submit' class="btn btn-secondary center" id='adjudication-a2'> Annotation 2 is correct. </button>
            <button name="a3" type='submit' class="btn btn-success center" id='adjudication-bt'> Both are correct. </button>
            <button name="a4" type='submit' class=" btn btn-danger center" id='adjudication-bf'> Both are wrong. </button>
          </form>
            </div>
          </div>
          <div class="col-2 bg-success bg-light border text-center">
            <h5 class="list-group-item-heading">Disputes</h5>
            <?php
            // foreach ($inbox as &) {
            for($i=0; $i<count($verdict_mismatches); $i++) {
              echo "<a href='?open_issue=$i'
              type='button' class='btn btn-outline-secondary btn-sm mb-1 w-75 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
              title='$i'> Claim $i
              </a>";
            }//da war $sub_email[abbr]
            ?>
          </div>
        </div>
      </div>

    </body>
    </html>
