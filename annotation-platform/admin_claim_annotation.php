<?php

function get_annotators($conn){
  $sql = "SELECT id, annotator_name, active, current_task, finished_claim_annotations, number_logins, annotation_time, skipped_data, calibration_score, calibration_score_2 FROM Annotators WHERE annotation_mode=?";
  $stmt= $conn->prepare($sql);
  $mode = 'claim';
  $stmt->bind_param("s", $mode);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();

  $id_name_list = array();
  $id_current_task_list = array();
  $id_finished_claim_annotations_list= array();
  $id_number_logins_list =  array();
  $id_annotation_time_list =  array();
  $id_skipped_data_list =  array();
  $id_calibration_score_list = array();

  while($row = $result_anno1->fetch_assoc())
  {
    if ($row['active'] == 1 && $row['id'] > 23){
      $id_name_list[$row['id']] = $row['annotator_name'];
      $id_current_task_list[$row['id']] = $row['current_task'];
      $id_number_logins_list[$row['id']] = $row['number_logins'];
      $id_annotation_time_list[$row['id']] = $row['annotation_time'];
      $id_skipped_data_list[$row['id']] = $row['skipped_data'];
      $id_finished_claim_annotations_list[$row['id']] = $row['finished_claim_annotations'];
      $id_calibration_score_list[$row['id']] = (explode('[SEP]', $row['calibration_score'])[0] + explode('[SEP]', $row['calibration_score_2'])[0]) / 2;
    }
  }

  return array($id_name_list, $id_current_task_list, $id_number_logins_list, $id_annotation_time_list, $id_skipped_data_list, $id_calibration_score_list, $id_finished_claim_annotations_list);
}

function get_claim_list($conn, $annotator, $date){
  $id_claim_list = array();
  $claim_skipped_list = array();

   // cl.date_made  < DATE_SUB(CURDATE(), INTERVAL 1 DAY)
   // STR_TO_DATE('2021-03-12T19:30', '%Y-%m-%eT%H:%i');
    // STR_TO_DATE(?, '%Y-%m-%eT%H:%i')
  $sql = "SELECT data_source,skipped FROM Claims WHERE annotator=? AND date_made > STR_TO_DATE(?, '%Y-%m-%eT%H:%i')";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("is", $annotator, $date);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();
  $iterator = 0;
  while($row = $result_anno1->fetch_assoc())
  {
    $id_claim_list[$iterator] = $row['data_source'];
    if(!array_key_exists($row['data_source'], $claim_skipped_list) || $claim_skipped_list[$row['data_source']] == 0){
      if(($row['skipped'] == '') && (!array_key_exists($row['data_source'], $claim_skipped_list))) {
          $claim_skipped_list[$row['data_source']] = 0;
      }else if($row['skipped'] != ''){
        $claim_skipped_list[$row['data_source']] = $row['skipped'];
      }
    }
    $iterator +=1;
  }

  return array(array_unique($id_claim_list, SORT_STRING), $claim_skipped_list);


}

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

list($id_name_list, $id_current_task_list, $id_number_logins_list, $id_annotation_time_list, $id_skipped_data_list, $id_calibration_score_list, $id_finished_claim_annotations_list) = get_annotators($conn);

if ($_GET["request"] != "load-highlight"){
  if (isset($_GET["open_issue"])){
    $_SESSION['current_issue'] =  $_GET["open_issue"];
  }else{
    $_SESSION['current_issue'] = 0;
  }

  if (isset($_GET["annotator"])){
    $_SESSION['current_annotator'] =  $_GET["annotator"];
  } else if (!isset($_SESSION['current_annotator'])){
    $_SESSION['current_annotator'] =  24;
  }
  if (isset($_GET["filter_time"])){
    $_SESSION['filter_time'] = $_GET['filter_time'];
  } else if (!isset($_SESSION['filter_time'])){
    $_SESSION['filter_time'] =  '2021-03-16T19:30';
  }
}
// echo $_SESSION['filter_time'];

if($_SESSION['user'] > 22){
  echo 'You are not authorized to use this tool.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}else if ($_SESSION['annotation_mode'] != 'claim'){
  echo 'Wrong annotator type. You are not authorized to use this tool.';
  echo '<a href="annotation-service/logout.php">Logout</a>';
  echo "<!--";
}

$sql = "SELECT annotator_name, finished_calibration, calibration_score, calibration_score_2 FROM Annotators WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $_SESSION['current_annotator']);
$stmt->execute();
$annotator1_result = $stmt->get_result();
$annotator1_row = $annotator1_result->fetch_assoc();
$annotator1 = $annotator1_row['annotator_name'];


list($claim_id_map, $claim_skipped_list) = get_claim_list($conn, $_SESSION['current_annotator'], $_SESSION['filter_time']);

$sql = "SELECT id, claim, data_source,annotator,page, claim_type, challenges, skipped FROM Claims WHERE data_source = ? AND annotator=?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("ii", $claim_id_map[$_SESSION['current_issue']],$_SESSION["current_annotator"]);#, $_SESSION["user"]);
$stmt->execute();
$result_anno1 = $stmt->get_result();
$anno1_c1 = $result_anno1->fetch_assoc();
$anno1_c2 = $result_anno1->fetch_assoc();
$anno1_c3 = $result_anno1->fetch_assoc();


$sql = "SELECT page, selected_id, is_table, multiple_pages, veracity, manipulation FROM ClaimAnnotationData WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $anno1_c1['data_source']);
$stmt->execute();
$result_claim = $stmt->get_result();
$claim_data = $result_claim->fetch_assoc();
$data_veracity = (($claim_data['veracity'] == 0) ? 'false' : 'true');
$data_multiple_pages = (($claim_data['multiple_pages'] == 0) ? 'Same page' : 'Multiple pages');

if ($_SERVER['REQUEST_METHOD'] == "POST"){
  if ($_POST['request'] == "report-claim"){ //&& $finished_calibration == 1

    $report_text = $_POST['report_text'];
    $report_text = implode(" [SEP] ", json_decode($report_text));
    if($_POST['claim_num'] == 1){
      $report_claim_id = $anno1_c1['id'];
    }else if ($_POST['claim_num'] == 2){
      $report_claim_id = $anno1_c2['id'];
    }else if ($_POST['claim_num'] == 3){
      $report_claim_id = $anno1_c3['id'];
    }
    $sql = "UPDATE Claims SET taken_flag=0,skipped=?, skipped_by=? WHERE id=?";
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("sii", $report_text, $_SESSION['user'], $report_claim_id);
    $stmt->execute();

  }
  else if($_POST['request'] == 'deactivate-annotator'){
    $sql = "UPDATE Annotators SET active=-1 WHERE id=?";
    $stmt= $conn->prepare($sql);
    $stmt->bind_param("i",$_SESSION['current_annotator']);
    $stmt->execute();
  }
  else if($_POST['request'] == 'production_report'){
    $date = date("Y-m-d H:i:s");
    $file = "statistics/output/production_report_claim/" . $date . ".csv";
    $txt = fopen($file, "w") or die("Unable to open file!");
    fwrite($txt, "Annotator \t Number logins \t Total Annotation sets \t Total Annotations \t Total Annotation time (sec) \t Average Annotation time (sec)\n");
    foreach ($id_name_list as $key => $value) {
        $average_annotation_time = ($id_annotation_time_list[$key] / $id_finished_claim_annotations_list[$key]);
        fwrite($txt, $value . " \t " . $id_number_logins_list[$key] . " \t " . $id_finished_claim_annotations_list[$key] . " \t " . $id_finished_claim_annotations_list[$key] * 3 . " \t "  . $id_annotation_time_list[$key] . " \t " .  $average_annotation_time . "\n");
    }
    fclose($txt);
    echo $file;
    return;
  }
}
else if ($_SERVER['REQUEST_METHOD'] === 'GET'){
  if ($_GET["request"] == "load-highlight"){
    echo json_encode(array($claim_data['is_table'], $claim_data['selected_id'],$_SESSION['current_issue']));
    return;
  }
  else if ($_GET['request'] == 'load-results'){
    echo json_encode($calibration_score_details);
    return;
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
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.13.1/js/bootstrap-select.min.js"></script>
  <script src="https://cdn.jsdelivr.net/gh/vast-engineering/jquery-popup-overlay@2/jquery.popupoverlay.min.js"></script>


  <script type="text/javascript">
  $.ajaxSetup({async:false});

  $(function () {
    $('[data-toggle="popover"]').popover()
  })
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  })
  $('select').selectpicker();
  $(window).on('load', function() {


    $.get('admin_claim_annotation.php', {request:'load-highlight'},function(data,status,xhr){
      var is_table = data[0];
      var selected_id = data[1];
      var iframeDoc = $("#my-wikipedia")[0].contentWindow.document;
      if(is_table == 1){
        $(iframeDoc).find("p:contains('" + selected_id.replaceAll('.', '\\.').replaceAll("''", "'").replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").next().css('border-style','solid').css('border-width', 'thick').css('border-color', 'coral');
        var offset = $(iframeDoc).find("p:contains('" + selected_id.replaceAll('.', '\\.').replaceAll("''", "'").replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").next().offset();
      }else{
        var sentences = selected_id.replaceAll("''", "'").split(" [SEP] ");
        var offset = $(iframeDoc).find("p:contains('" + sentences[0].replaceAll('.', '\\.').replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").offset();
        for(var i = 0; i < sentences.length; i++){
          $(iframeDoc).find("p").filter(function() {
            if($(this).find('span').text() ==  sentences[i]){
              $(this).css( "background-color", 'coral');
            }
          });
        }
      }
      if (offset != null){
        offset.left -= 20;
        $("#my-wikipedia").contents().scrollTop(offset.top);
      }
    },'json');

    function getSum(total, num) {
      return total + Math.round(num);
    }

    $(document.body).on('click', '#deactivate-annotator', function(event){
      $.post('admin_claim_annotation.php', {request: 'deactivate-annotator'},function(data,status,xhr){
        $('#deactivate-annotator').append('<p> Done! </p>');
        // $('#result-box').text("Output:" + score_list);
      }).fail(function(xhr, status, error) {console.log(error)});
    });

    $(document.body).on('click', '.report-item', function(event) {
      if($(this).hasClass("active")){
        $(this).removeClass("active");
        // $(this).selectpicker("refresh");
      }else{
        $(this).addClass("active");
      }
    });

    $(document.body).on('click', '#production-report', function(event) {
      $.post('admin_claim_annotation.php', {request: 'production_report'},function(data,status,xhr){
        var name = data;
        event.preventDefault();  //stop the browser from following
        window.location.href = data;
        // $('#result-box').text("Output:" + score_list);
      }).fail(function(xhr, status, error) {console.log(error)});
    });



    function report_button_listener(button_num, report_button_num, report_item_num, report_note_num){
      $(document.body).on('click', report_button_num, function(event) {
        var active_text = [];
        tags = $(report_item_num);
        for(var i = 0; i < tags.length; i++){
          if ($(tags[i]).hasClass("active")){
            active_text.push($(tags[i]).text());
          }
        }
        var custom_note = $('.dropdown-item' + report_note_num).val();
        active_text.push(custom_note);
        active_text = JSON.stringify(active_text);
        console.log(active_text);
        if (active_text == '[""]'){
          alert('Please specify why you want to report this claim.');
        }else{
          $.post('admin_claim_annotation.php', {request: "report-claim", report_text: active_text, claim_num:button_num},
          function(data,status,xhr){
            $(report_button_num).append('<p> Done! </p>');
          }
          ,'text');
        }});
      }

      report_button_listener(1,'#report-button-1', '.report-item-1', '#report-note-1')
      report_button_listener(2,'#report-button-2', '.report-item-2', '#report-note-2')
      report_button_listener(3,'#report-button-3', '.report-item-3', '#report-note-3')


      $(document.body).on('change', '#meeting-time', function(event) {
      var datetimeval = $("#meeting-time").val();
      console.log(datetimeval);
      $.get('admin_claim_annotation.php', {request: 'update-filter-time', filter_time: datetimeval},function(data,status,xhr){
        // $('#result-box').text("Output:" + score_list);
      }).fail(function(xhr, status, error) {console.log(error)});
      location.reload();
    });

    });



    </script>

    <style type="text/css">
    .container-fluid {
      width: auto !important;
      margin-right: 10% !important;
      margin-left: 10% !important;
    }

    .border-3 {
      border-width:3px !important;
    }

    .list-in {
      background-color: chartreuse;

    }

    .a-button{
      background: 	#D3D3D3;
    }
    .list-out {
      background-color:#ff6666 ;
    }
    </style>
  </head>
  <body>
    <div class="container-fluid p-3">
      <div class="row">
        <div class="col-9 m-2">
          <a href="annotation-service/logout.php">Logout</a>
          <h3 class='text-center pb-5'>Claim Annotation Admin Interface</h3>
          <?php  echo " <button type='button' class='btn btn-dark' data-toggle='popover' data-placement='left' data-html='true'  data-content='Current task: " . $id_current_task_list[$_SESSION['current_annotator']] . "<br> Number logins: " . $id_number_logins_list[$_SESSION['current_annotator']] . "<br>Total Annotations: " . $id_finished_claim_annotations_list[$_SESSION['current_annotator']] . "<br>Total Annotation time: " . $id_annotation_time_list[$_SESSION['current_annotator']] . "s<br>Average Annotation time: " . ($id_annotation_time_list[$_SESSION['current_annotator']] / $id_finished_claim_annotations_list[$_SESSION['current_annotator']]) . "s<br>Skipped highlights: " . $id_skipped_data_list[$_SESSION['current_annotator']] . "<br>Calibration score:" . $id_calibration_score_list[$_SESSION['current_annotator']] .  "'>Annotator Status</button>"; ?>
          <button name="deactivate" class="btn btn-danger center" id='deactivate-annotator'> Deactivate Annotator. </button>
          <button name="production-report" class="btn btn-info pull-right" id='production-report'> Download Production Report. </button>
          <input class="pull-right" type="datetime-local" id="meeting-time" name="meeting-time" value=<?php echo $_SESSION['filter_time'] ?>>
          <hr style="height:5px;background-color: #333;">
          <div class="mx-auto embed-responsive embed-responsive-21by9" style="width:80vh;">
            <iframe id="my-wikipedia" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php/<?php echo $claim_data['page'] ?>"></iframe>
          </div>
          <p class='text-center mt-5  <?php if ($anno1_c1['skipped'] != '') echo 'bg-danger'; ?>' id='claim-1'>Claim using Highlight <?php  echo "(" .  $data_veracity . "): " . "<b>" . $anno1_c1['claim'] . '</b>'?></p>
            <p class='text-center'>Challenge: <?php echo $anno1_c1['challenges']?></p>
            <div class="text-center">
              <button type="button" id='report-button-1' class="btn btn-warning fa fa-exclamation-triangle" >Report Claim</button>
              <button type="button" class="btn btn-danger dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <span class="sr-only">Toggle Dropdown</span>
              </button>
              <div class="dropdown-menu">
                <a class="dropdown-item report-item-1 report-item"  value="NEI">Cannot be verified using any publicly available information </a>
                <a class="dropdown-item report-item-1 report-item" value="NEI">Does not meet the claim generation guidelines</a>
                <a class="dropdown-item report-item-1 report-item"  value="supported">Ungrammatical, spelling mistakes, typographical errors</a>
                <a class="dropdown-item report-item-1 report-item"  value="supported">Required evidence is not displayed correctly <br> (e.g. tokenization errors, wrongly formatted tables)</a>
                <input id= 'report-note-1' class="dropdown-item" placeholder='Enter Note...'>
              </div>
            </div>
            <p class='text-center mt-5 <?php if ($anno1_c2['skipped'] != '') echo 'bg-danger'; ?>' id='claim-2'>Claim beyond Highlight: <?php  echo "(" .  $data_multiple_pages . "): " . "<b>" . $anno1_c2['claim'] . '</b>'?> </p>
              <p class='text-center'>Challenge: <?php echo $anno1_c2['challenges']?></p>
              <div class="text-center">
                <button type="button" id='report-button-2' class="btn btn-warning fa fa-exclamation-triangle button-responsive" >Report Claim</button>
                <button type="button" class="btn btn-danger dropdown-toggle dropdown-toggle-split .button-responsive" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                  <span class="sr-only">Toggle Dropdown</span>
                </button>
                <div class="dropdown-menu">
                  <a class="dropdown-item report-item-2 report-item"  value="NEI">Cannot be verified using any publicly available information </a>
                  <a class="dropdown-item report-item-2 report-item" value="NEI">Does not meet the claim generation guidelines</a>
                  <a class="dropdown-item report-item-2 report-item"  value="supported">Ungrammatical, spelling mistakes, typographical errors</a>
                  <a class="dropdown-item report-item-2 report-item"  value="supported">Required evidence is not displayed correctly <br> (e.g. tokenization errors, wrongly formatted tables)</a>
                  <input id= 'report-note-2' class="dropdown-item" placeholder='Enter Note...'>
                </div>
              </div>
              <p class='text-center mt-5 <?php if ($anno1_c3['skipped'] != '') echo 'bg-danger'; ?>' id='claim-3'>Manipulation: <?php  echo "(" .  $claim_data['manipulation'] . "): " . "<b>" . $anno1_c3['claim'] . '</b>'?> </p>
                <p class='text-center'>Challenge: <?php echo $anno1_c3['challenges']?></p>
                <div class="text-center">
                  <button type="button" id='report-button-3' class="btn btn-warning fa fa-exclamation-triangle button-responsive" >Report Claim</button>
                  <button type="button" class="btn btn-danger dropdown-toggle dropdown-toggle-split .button-responsive" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                    <span class="sr-only">Toggle Dropdown</span>
                  </button>
                  <div class="dropdown-menu">
                    <a class="dropdown-item report-item-3 report-item"  value="NEI">Cannot be verified using any publicly available information </a>
                    <a class="dropdown-item report-item-3 report-item" value="NEI">Does not meet the claim generation guidelines</a>
                    <a class="dropdown-item report-item-3 report-item"  value="supported">Ungrammatical, spelling mistakes, typographical errors</a>
                    <a class="dropdown-item report-item-3 report-item"  value="supported">Required evidence is not displayed correctly <br> (e.g. tokenization errors, wrongly formatted tables)</a>
                    <input id= 'report-note-3' class="dropdown-item" placeholder='Enter Note...'>
                  </div>
                </div>
              </div>
              <div class="col-1 bg-success bg-light border text-center">
                <h5 class="list-group-item-heading">Claims <?php echo '(' . (count($claim_id_map) - array_count_values($claim_skipped_list)[0]) .  '/' . count($claim_id_map) . ')'?></h5>
                <?php
                foreach ($claim_id_map as $key => $value) {
                  if ($claim_skipped_list[$value] != '0'){
                    $is_skipped = 'style="background-color:red;"';
                  }else{
                    $is_skipped = '';
                  }
                  if ($key == $_SESSION['current_issue']){
                    echo "<a href='?open_issue=$key'
                    type='button' id='Annotation-$key' class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                    title='$key'> Claim $value
                    </a>";
                  }else{
                    echo "<a href='?open_issue=$key'
                    type='button' id='Annotation-$key' $is_skipped class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                    title='$key'> Claim $value
                    </a>";
                  }
                }
                ?>
              </div>
              <div class="col-1 bg-success bg-light border text-center">
                <h5 class="list-group-item-heading">Annotator <?php echo '(' . count($id_name_list) . ')'?></h5>
                <?php
                foreach ($id_name_list as $key => $value) {
                  if ($key == $_SESSION['current_annotator']){
                    echo "
                    <a href='?annotator=$key'
                    type='button' class='btn btn-outline-secondary btn-sm mb-1 w-80 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
                    title='$key'> $value
                    </a>";
                  }else{
                    echo "<a href='?annotator=$key'
                    type='button' class='btn btn-outline-secondary btn-sm mb-1 w-80 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
                    title='$key'> $value
                    </a>";
                  }
                }
                ?>
              </div>
          </div>
        </div>

      </body>
      </html>
