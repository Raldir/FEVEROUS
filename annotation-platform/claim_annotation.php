<?php
ini_set('session.gc_maxlifetime', 86400);
session_set_cookie_params(86400);
session_start();
// Start the session
// Check user login or not
if(!isset($_SESSION["user"]) ||  $_SESSION['annotation_mode'] != 'claim'){
    include file_get_contents('index.php');
    echo "<!--";
}else if( $_SESSION['finished_calibration'] == 2 && $_SESSION['active']<= 0){
  echo 'Your account has not yet been activated for the main annotation. Please contact your project coordinator in case of unclarities.';
  $_SESSION = array();
  session_destroy();
  echo "<!--";
}else if( $_SESSION['finished_calibration'] == 1 && $_SESSION['calibration_score'] == 0){
  echo 'Your calibration has not been evaluated yet. Please get in contact with your project coordinator in case of unclarities.';
  $_SESSION = array();
  session_destroy();
  echo "<!--";
}
?>

<html>
<head>
  <link rel="stylesheet" href="css/style_claim_annotation.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.13.1/css/bootstrap-select.css" />


  <script src="js/extensions/jquery.js"></script>
  <script src="js/extensions/jquery.md5.js"></script>
  <script src="js/extensions/jquery_ui.js"></script>
  <script src="js/extensions/inputfit.js"></script>
  <script src="https://unpkg.com/@popperjs/core@2"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.13.1/js/bootstrap-select.min.js"></script>



  <script src="js/highlighter.js"></script>
  <script src="js/claim_annotation.js"></script>

  <meta name="viewport" content="width=device-width"/>
</head>

<body style="font-family: sans-serif">

  <div class="topnav" id="myTopnav">
    <a href="user-details.php" id="user-details" class="fa fa-user-circle-o">User Details</a>
    <a href="annotation_guidelines/Claim_annotation/claim_guidelines_v1-63.pdf" target="_blank" class="guidelines fa fa-file-pdf-o">Annotation Guidelines</a>
    <a href="" class="logout fa fa-sign-out" style="text-align:right">Logout</a>
    <?php if ($_SESSION['finished_calibration'] !=2) echo '<a class="fa fa-exclamation" style="color:red; text-align:left"> CALIBRATION MODE. COMPLETE THE FOLLOWING ANNOTATIONS AND RECEIVE FEEDBACK ON THEM. <i class="fa fa-exclamation"> </i></a>';?>
  </div>

<div class="menu-frame" id="my-menu-frame">
  <div class="claim-generation-specifications">
    <p id='claim_url'> No url retrieved. </p>
    <button id= 'go-back' class="btn btn-primary fa fa-arrow-circle-left fa-lg pull-left button-responsive-info"></button>
    <button id= 'go-forward' class=" btn btn-primary fa fa-lg fa-arrow-circle-right pull-left button-responsive-info" disabled></button>
  </div>


  <div class="generated-claim-div" id="generated-claim-div">
    <button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info" data-toggle="popover" data-html="true"  data-content="The first claim should exclusively use information from the highlighted table/sentences (including table captions/page title). The claim can either align with the contents in the highlight or contradict it. (i.e. true and false claims).
    <ul>
    <li> A claim should be a single well-formed sentence. It should end with a period; it should follow correct capitalization of entity names (e.g. `India', not `india'); numbers can be formatted in any appropriate English format (including as words for smaller quantities).
    <li> A claim based on a table highlight should combine information of multiple cells if possible.
    <li> A claim based on highlighted sentences should not simply paraphrase a highlighted sentence or concatenate sentences.
    <li> Generated claims must not be subjective and be verifiable using publicly available information/knowledge.
    <li> The claim should be as unambiguous as possible and avoid vague or speculative language (e.g. might be, may be, could be, rarely, many, barely or other indeterminate count words)
    <li> The claim must be understood by itself (i.e. no pronouns)
    <li>Claims should not be about contemporary political topics
    "></button>
    <span  id='claim-highlight' class="box-label">Not specified.</span>
    <input type="text"  spellcheck="true" class='generated-claim' id='generated-claim' value="">
    <select id="claim-annotation-challenge-selector" class="selectpicker ">
       <option value="Select challenge" selected disabled hidden>Select challenge</option>
        <option value="Multi-hop Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title="Multi-hop reasoning will be the main challenge for verifying that claim, i.e. several documents will be required for verification.">Multi-hop Reasoning</span>'>Multi-hop Reasoning</option>
        <option value="Numerical Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title=" Numerical reasoning required to verify the claim will be the main challenge, i.e. reasoning that involves numbers or arithmetic calculations.">Numerical Reasoning</span>'>Numerical Reasoning</option>
        <option value="Combining Tables/Lists and Text" data-content='<span data-toggle="tooltip" data-placement="right" title="Combining list(s)/table(s) with information from text will be the the main challenge, i.e. when the Text provides important context to Tables/List to be understood.">Combining Tables/Lists and Text</span>'>Combining Tables/Lists and Text</option>
        <option value="Entity Disambiguation" data-content='<span data-toggle="tooltip" data-placement="right" title="Disambiguating an entity is the main challenge for verifying a given claim.">Entity Disambiguation</span>'>Entity Disambiguation</option>
        <option value="Search terms not in claim" data-content='<span data-toggle="tooltip" data-placement="right" title=" Finding relevant search terms to pages with required evidence to verify a given claim goes beyond searching for terms located in the claim itself.">Search terms not in claim</span>'>Search terms not in claim</option>
      <option value="Other" data-content='<span data-toggle="tooltip" data-placement="right" title="If none of the above challenges can be identified.">Other'>Other</option>
    </select>
    <button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info"  data-html="true"  data-placement="right" data-toggle="popover" title="Expected Verification Challenges" data-content=	"We want to know what you think is the main challenge for assessing the veracity and retrieving evidence for the claim you have created.
    <ul>
    <li><b>Search terms not in claim</b> The main challenge is expected to be finding relevant search terms to pages with required evidence to verify a given claim goes beyond searching for terms located in the claim itself.</li>
    <li><b>Multi-hop Reasoning</b>  Multi-hop reasoning will be the main challenge for verifying that claim, i.e. several documents will be required for verification. </li>
    <li><b>Numerical reasoning</b> Numerical reasoning required to verify the claim will be the main challenge, i.e. reasoning that involves numbers or arithmetic calculations. </li>
    <li><b>Combining Tables/Lists and Text </b> Combining list(s)/table(s) with information from text will be the the main challenge, i.e. when the Text provides important context to Tables/List to be understood </li>
    <li><b>Entity Disambiguation</b> Disambiguating an entity is the expected main challenge for verifying a given claim. </li>
    <li><b>Other</b> If none of the above challenges can be identified. </li>
    "></button>
    <br>
    <br>
    <button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info"  data-html="true" data-toggle="popover" data-content="The second claim should be based on the highlight, but must include information beyond the highlighted table/sentences. <ul>
      <li> <b> Same page </b>: Include information outside of the highlight but on the same page.
      <li> <b> Multiple pages </b>: Include information from other wikipedia page(s). You can search freely through Wikipedia using the search function and use available hyperlinks on the pages.
      </ul>
     You are free in deciding to modify the previously created claim that uses only the highlight or to create an unrelated one (that still includes information from the highlight)."></button>
    <span  id='multiple-pages' class="box-label">Not specified.</span>
    <input type="text" spellcheck="true"  class='generated-claim-extended' id='generated-claim-extended' value="">
    <select id="claim-annotation-challenge-selector-extended" class="selectpicker">
       <option value="Select challenge" selected disabled hidden>Select challenge</option>
        <option value="Multi-hop Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title="Multi-hop reasoning will be a challenge for verifying that claim, i.e. several documents will be required for verification.">Multi-hop Reasoning</span>'>Multi-hop Reasoning</option>
        <option value="Numerical Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title=" Numerical reasoning required to verify the claim will be a challenge, i.e. reasoning that involves numbers or arithmetic calculations.">Numerical Reasoning</span>'>Numerical Reasoning</option>
        <option value="Combining Tables/Lists and Text" data-content='<span data-toggle="tooltip" data-placement="right" title=" Combining list(s)/table(s) with information from text will be the the main challenge, i.e. when the Text provides important context to Tables/List to be understood.">Combining Tables/Lists and Text</span>'>Combining Tables/Lists and Text</option>
        <option value="Entity Disambiguation" data-content='<span data-toggle="tooltip" data-placement="right" title="Disambiguating an entity is the main challenge for verifying a given claim.">Entity Disambiguation</span>'>Entity Disambiguation</option>
        <option value="Search terms not in claim" data-content='<span data-toggle="tooltip" data-placement="right" title=" Finding relevant search terms to pages with required evidence to verify a given claim goes beyond searching for terms located in the claim itself.">Search terms not in claim</span>'>Search terms not in claim</option>
      <option value="Other" data-content='<span data-toggle="tooltip" data-placement="right" title="If none of the above challenges can be identified.">Other'>Other</option>
    </select>
    <br>
    <br>
    <button type="button" class="btn btn-sm btn-info small h-5 fa fa-info rounded-circle button-responsive-info" data-toggle="popover" data-html="true" data-content="Modify the specified claim with the shown mutations type: <br> <ul> <li> <b> More Specific</b>: Make the claim more specific so that the new claim	is a specialization (as opposed to a generalization)
    <li> <b> Generalization </b>: Make the claim more general so that the new claim can be implied by the original claim (by making the meaning less specific)
    <li> <b> Negation </b>: Negate the meaning of the claim.
    <li> <b> Multiple Pages </b>: Incorporate information from multiple Wikipedia articles into the claim.
    <li> <b> Paraphrasing </b>: Rephrase the claim so that it has the same meaning
    <li> <b> Entity Substitution </b>: Substitute an entity in the claim to alternative from either the same or a different set of things.
    </ul>"></button>
    <span id='manipulations' class="box-label">Not specified. </span>
    <input type="text" spellcheck="true"  class='generated-claim-manipulation' id='generated-claim-manipulation' value="">
    <select id="claim-annotation-challenge-selector-manipulation" class="selectpicker">
       <option value="Select challenge" selected disabled hidden>Select challenge</option>
        <option value="Multi-hop Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title="Multi-hop reasoning will be a challenge for verifying that claim, i.e. several documents will be required for verification.">Multi-hop Reasoning</span>'>Multi-hop Reasoning</option>
        <option value="Numerical Reasoning" data-content='<span data-toggle="tooltip" data-placement="right" title=" Numerical reasoning required to verify the claim will be a challenge, i.e. reasoning that involves numbers or arithmetic calculations.">Numerical Reasoning</span>'>Numerical Reasoning</option>
        <option value="Combining Tables/Lists and Text" data-content='<span data-toggle="tooltip" data-placement="right" title=" Combining list(s)/table(s) with information from text will be the the main challenge, i.e. when the Text provides important context to Tables/List to be understood.">Combining Tables/Lists and Text</span>'>Combining Tables/Lists and Text</option>
        <option value="Entity Disambiguation" data-content='<span data-toggle="tooltip" data-placement="right" title="Disambiguating an entity is the main challenge for verifying a given claim.">Entity Disambiguation</span>'>Entity Disambiguation</option>
        <option value="Search terms not in claim" data-content='<span data-toggle="tooltip" data-placement="right" title=" Finding relevant search terms to pages with required evidence to verify a given claim goes beyond searching for terms located in the claim itself.">Search terms not in claim</span>'>Search terms not in claim</option>
      <option value="Other" data-content='<span data-toggle="tooltip" data-placement="right" title="If none of the above challenges can be identified.">Other'>Other</option>
    </select>
    <br>
</div>

<div id="submission-buttons">
  <button type='button' class="fa fa-undo btn btn-secondary button-responsive" id='generated-claim-return'> Jump to Highlight</button>
  <button type='button' class="fa fa-check btn btn-success button-responsive" id='generated-claim-submit'> Submit Claims</button>
  <button type='button' class="fa fa-flag btn btn-warning button-responsive" id='generated-claim-skip' <?php if ($_SESSION['finished_calibration'] !=2) echo 'disabled';?>> Skip</button>
</div>

</div>
</body>
</html>
