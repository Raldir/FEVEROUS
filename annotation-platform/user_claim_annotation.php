<?php


function get_claim_list($conn, $annotator){
  $id_data_source_skipped_list = array();
  $id_data_source_list = array();


  $sql = "SELECT data_source, skipped FROM Claims WHERE annotator=?";
  $stmt= $conn->prepare($sql);
  $stmt->bind_param("i", $annotator);#, $_SESSION["user"]);
  $stmt->execute();
  $result_anno1 = $stmt->get_result();
  $iterator = 0;
  while($row = $result_anno1->fetch_assoc())
  {
    if($row['skipped'] !=''){
      $id_data_source_skipped_list[$iterator] = $row['data_source'];
    }
    $id_data_source_list[$iterator] = $row['data_source'];
    $iterator +=1;
  }

  return array(array_unique($id_data_source_list, SORT_STRING), array_unique($id_data_source_skipped_list, SORT_STRING));


}

session_start();

if (!isset($_SESSION["user"])){
  echo file_get_contents('login.html');
  echo "<!--";
}else if ($_SESSION['annotation_mode'] != 'claim'){
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
  if (isset($_GET["open_issue"])){
    $_SESSION['current_issue'] =  $_GET["open_issue"];
  }else{
    $_SESSION['current_issue'] = 0;
  }
}

$sql = "SELECT annotator_name, finished_calibration, calibration_score, calibration_score_2 FROM Annotators WHERE id = ?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("i", $_SESSION['user']);
$stmt->execute();
$annotator1_result = $stmt->get_result();
$annotator1_row = $annotator1_result->fetch_assoc();
$annotator1 = $annotator1_row['annotator_name'];


list($id_data_source_list, $id_data_source_skipped_list) = get_claim_list($conn, $_SESSION['user']);


$sql = "SELECT id, claim, data_source,annotator,page, claim_type, challenges, skipped FROM Claims WHERE data_source = ? AND annotator=?";
$stmt= $conn->prepare($sql);
$stmt->bind_param("ii", $id_data_source_list[$_SESSION['current_issue']],$_SESSION["user"]);#, $_SESSION["user"]);
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


if ($_SERVER['REQUEST_METHOD'] === 'GET'){
  if ($_GET["request"] == "load-highlight"){
    echo json_encode(array($claim_data['is_table'], $claim_data['selected_id'],$_SESSION['current_issue']));
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


    $.get('user_claim_annotation.php', {request:'load-highlight'},function(data,status,xhr){
      console.log(data);
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
        <h3 class='text-center pb-5'>Claim Annotation User Interface</h3>
        <hr style="height:5px;background-color: #333;">
        <div class="mx-auto embed-responsive embed-responsive-21by9" style="width:80vh;">
          <iframe id="my-wikipedia" class="embed-responsive-item" src="http://mediawiki.feverous.co.uk/index.php/<?php echo $claim_data['page'] ?>"></iframe>
        </div>
        <h3 class='text-center pt-5'>Generated Claims</h3>
        <?php
        if ($anno1_c1['skipped'] != ''){
          $skipped_text = explode(' [SEP] ', $anno1_c1['skipped']);
          echo "<div class='bg-danger'><p class='text-center mt-5' id='claim-1'>Claim using Highlight(" .  $data_veracity . "): " . "<b>" . $anno1_c1['claim'] . "</b></p>";
          echo "<p>Reported for: </p>";
          echo "<ol>";
          for ($i = 0; $i < count($skipped_text); $i++) {
            if ($skipped_text[$i]!= ''){
              echo "<li>" . $skipped_text[$i] . "</li>";
            }
          }
          echo "</ol></div>";
        }else{
          echo "<p class='text-center mt-5' id='claim-1'>Claim using Highlight(" .  $data_veracity . "): " . "<b>" . $anno1_c1['claim'] . "</b></p>";
        }
        ?>
        <?php
        if ($anno1_c2['skipped'] != ''){
          $skipped_text = explode(' [SEP] ', $anno1_c2['skipped']);
          echo "<div class='bg-danger'><p class='text-center mt-5' id='claim-2'>Claim beyond Highlight:" . "(" .  $data_multiple_pages . "): " . "<b>" . $anno1_c2['claim'] . '</b></p>';
          echo "<p>Reported for: </p>";
          echo "<ol>";
          for ($i = 0; $i < count($skipped_text); $i++) {
            if ($skipped_text[$i]!= ''){
              echo "<li>" . $skipped_text[$i] . "</li>";
            }
          }
          echo "</ol></div>";
        }else{
          echo "<p class='text-center mt-5' id='claim-2'>Claim beyond Highlight:" . "(" .  $data_multiple_pages . "): " . "<b>" . $anno1_c2['claim'] . '</b></p>';
        }
        ?>
        <?php
        if ($anno1_c3['skipped'] != ''){
          $skipped_text = explode(' [SEP] ', $anno1_c3['skipped']);
          echo  "<div class='bg-danger'><p class='text-center mt-5  bg-danger' id='claim-3'>Manipulation " . "(" .  $claim_data['manipulation'] . "): " . "<b>" . $anno1_c3['claim'] . '</b></p>';
          echo "<p>Reported for: </p>";
          echo "<ol>";
          for ($i = 0; $i < count($skipped_text); $i++) {
            if ($skipped_text[$i]!= ''){
              echo "<li>" . $skipped_text[$i] . "</li>";
            }
          }
          echo "</ol></div>";
        }else{
          echo  "<p class='text-center mt-5' id='claim-3'>Manipulation " . "(" .  $claim_data['manipulation'] . "): " . "<b>" . $anno1_c3['claim'] . '</b></p>';
        }
        ?>
      </div>
      <div class="col-1 bg-success bg-light m-3 border text-center">
        <h5 class="list-group-item-heading">Claims</h5>
        <?php
          foreach ($id_data_source_list as $key => $value) {
            if ($key == $_SESSION['current_issue']){
              echo "<a href='?open_issue=$key'
              type='button' id='Annotation-$key' class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
              title='$key'> Claim $value
              </a>";
            }else{
              echo "<a href='?open_issue=$key'
              type='button' id='Annotation-$key' class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
              title='$key'> Claim $value
              </a>";
            }
        }
        ?>
      </div>
      <div class="col-1 bg-success bg-light m-3 border text-center">
        <h5 class="list-group-item-heading">Reported Claims</h5>
        <?php
        if (count($id_data_source_skipped_list) == 0){
          echo "No claims have been reported.";
        }else{
          foreach ($id_data_source_skipped_list as $key => $value) {
            if ($key == $_SESSION['current_issue']){
              echo "<a href='?open_issue=$key'
              type='button' id='Annotation-$key' class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden active' data-toggle='tooltip' data-placement='right' data-html='true'
              title='$key'> Claim $value
              </a>";
            }else{
              echo "<a href='?open_issue=$key'
              type='button' id='Annotation-$key' class='btn btn-outline-secondary btn-sm mb-1 w-90 overflow-hidden' data-toggle='tooltip' data-placement='right' data-html='true'
              title='$key'> Claim $value
              </a>";
            }
          }
        }
        ?>
      </div>
    </div>
  </div>

</body>
</html>
