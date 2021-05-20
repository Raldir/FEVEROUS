var base_url = 'http://mediawiki.feverous.co.uk/index.php/';
$.ajaxSetup({async:false});

$(window).on('load', function() {

  //$( document ).ready(function() {

  var status_page = localStorage.getItem('status-page');
  if (status_page == 'open'){
    $('body').remove();
  }else{
    run_page();
  }
});

function log_out(){
  $.ajax({
    url: "annotation-service/logout.php",
    type: "GET",
    success: function(data){
      localStorage.clear();
    }
  });
}


function auto_logout(){
  var idleMax = 20; // Logout after 25 minutes of IDLE
  var idleTime = 0;

  var idleInterval = setInterval(timerIncrement, 60000);  // 1 minute interval
  $( "body" ).mousemove(function( event ) {
    idleTime = 0; // reset to zero
  });

  // count minutes
  function timerIncrement() {
    idleTime = idleTime + 1;
    if (idleTime > idleMax) {
      log_out();
      location.reload();
    }
    // else if (idleTime + 3 > idleMax){
    //   alert('Please move your courser or otherwise you will be logged out.');
    // }
  }
}


function setup_js(){
  $(function () {
    $('[data-toggle="popover"]').popover();
  });
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  });
  $('select').selectpicker();
}

function run_page(){
  auto_logout();
  localStorage.setItem('status-page', 'open');
  $("body").append('<iframe id="my-wikipedia"></iframe>');
  $("#my-wikipedia").prop('src', localStorage.getItem('last-url')) ;
  $('#my-wikipedia').on("load", function() {
    Processor.reload_elements();
  });
  setup_js();
  Processor.init();

  $(".adjust-evidence-selection").on('click', function(e) {
    $('#popup').popup('hide');
  });

  function confirmation_screen_set(num, evidence1, details1){
    var has_tok_errors = 0;
    if (evidence1 != null && evidence1.length > 0){
      var list = $('#evidence-confirmation').append('<ul>Set ' + num + ': </ul>').find('ul').last();
      for (var key in Highlighter.anno_parents[num]){
        if (Highlighter.anno_parents[num][key].length == 0){
          continue;
        }
        if(key.includes('sentence') || key.includes('item') || key.includes('caption')){
          for (var i = 0; i <Highlighter.anno_parents[num][key].length; i++) {
            var space = 'margin-left: ' + (i * 2).toString() +  'em';
            var style = details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])].indexOf("Tokenization error in the highlighted sentence:") >= 0 ? 'color: red;font-weight: bold;' + space : space;

            list.append('<li style="' + style + '">' +   details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])] + '</li>');
          }
          var space = 'margin-left: ' + ((i + 2)* 2).toString() +  'em';
          var style = details1[evidence1.indexOf(key)].indexOf("Tokenization error in the highlighted sentence:") >= 0 ? 'color: red;font-weight: bold;' + space : space;
          list.append('<li style="' + style + '">' +  details1[evidence1.indexOf(key)] + '</li>');
        }
        else if (key.includes('header_cell')){
          for (var i = 0; i <Highlighter.anno_parents[num][key].length; i++) {
            var space = 'margin-left: ' + ((i) * 2).toString() +  'em';
            var style = details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])].indexOf("Tokenization error in the highlighted sentence:") >= 0 ? 'color: red;font-weight: bold;' + space : space;
            list.append('<li style="' + style + '">' +  details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])]  + '</li>');
          }
          var space = 'margin-left: ' + ((i + 2)).toString() +  'em';
          var style = details1[evidence1.indexOf(key)].indexOf("Tokenization error in the highlighted sentence:") >= 0 ? 'color: red;font-weight: bold;' + space : space;
          content = ('<table style="width:100%"><tr> <th>' +  details1[evidence1.indexOf(key)] + '</th> </tr></table>');
          list.append('<li style="' + style + '">' +   content + '</li>');
          }
        else if (key.includes('cell')){
          var cell_count = 0;
          var headers = [];
          for (var i = 0; i <Highlighter.anno_parents[num][key].length; i++) {
            var space = 'margin-left: ' + ((i + cell_count) * 2 ).toString() +  'em';
            var style = details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])].indexOf("Tokenization error in the highlighted sentence:") >= 0 ? 'color: red;font-weight: bold;' : space;
            if(Highlighter.anno_parents[num][key][i].includes('header')){
              headers.push(details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])]);
            }else{
              list.append('<li style="' + style + '">' +   details1[evidence1.indexOf(Highlighter.anno_parents[num][key][i])] + '</li>');
            }
          }
          content = '<table style="width:100%"><tr> <th>';
          content += headers.join(' | ');
          content += '</th> </tr><tr> <td>' + details1[evidence1.indexOf(key)] + '</td></tr></table>';
          list.append('<li style="' + style + '">' +   content + '</li>');
        }
        console.log(style);
        if(style.includes('color: red;font-weight: bold;')){
          has_tok_errors = 1;
        }
      }
    }
    console.log(has_tok_errors);
    return has_tok_errors;
  }

  $(".my_popup").on('click', function(e) {
    $('.evidence-annotation-submit-button').prop('disabled', false);
    if(annotation_complete()){
      $('#popup').popup('show');
      $('#current-claim-confirmation').text('');
      $('#verdict-confirmation').text('Verdict: ');
      $('#evidence-confirmation').text('');
      $('#challenge-confirmation').text('Main Challenge: ');

      var verdict = $("#evidence-annotation-verdict-selector option:selected").text();
      $('#current-claim-confirmation').text($('#current-claim').text());
      $('#verdict-confirmation').append($("#evidence-annotation-verdict-selector option:selected").text());
      $('#challenge-confirmation').append($("#evidence-annotation-challenge-selector option:selected").text());
      [evidence1, details1] = Highlighter.get_selected_annotations(1);
      [evidence2, details2] = Highlighter.get_selected_annotations(2);
      [evidence3, details3] = Highlighter.get_selected_annotations(3);
      var has_tok_errors1 = confirmation_screen_set(1, evidence1, details1);
       $('#evidence-confirmation').append('<hr style="height:5px;background-color: #333;">');
      var has_tok_errors2 = confirmation_screen_set(2, evidence2, details2);
       $('#evidence-confirmation').append('<hr style="height:5px;background-color: #333;">');
      var has_tok_errors3 = confirmation_screen_set(3, evidence3, details3);
      if(has_tok_errors1 == 1 || has_tok_errors1 == 2 || has_tok_errors1 == 3){
        $('.evidence-annotation-submit-button').prop('disabled', true);
      }
    }
  });

  $(window).on('beforeunload', function(){
    localStorage.setItem('status-page', 'reload');
    if (localStorage.getItem('back-counter') > 0){
      Processor.reset_evidence_menu();
      localStorage.setItem('back-counter', 0);
    }
  });
  // $(window).onpopstate = function(event) {
  //     // make the parent window go back
  //     alert('yao');
  //     top.history.back();
  //   };

  $(".logout").on('click', function(e) {
    log_out();
    window.location.reload();
  });

  function annotation_complete(){
    [evidence1, details1] = Highlighter.get_selected_final_annotations(1);
    [evidence2, details2] = Highlighter.get_selected_final_annotations(2);
    [evidence3, details3] = Highlighter.get_selected_final_annotations(3);


    // var evidence = JSON.parse(localStorage.getItem('annotations'));
    evidence1 = JSON.stringify(evidence1);
    details1 = JSON.stringify(details1);
    evidence2 = JSON.stringify(evidence2);
    details2 = JSON.stringify(details2);
    evidence3 = JSON.stringify(evidence3);
    details3 = JSON.stringify(details3);

    var verdict = $( "#evidence-annotation-verdict-selector option:selected").text();
    // var challenge_el = $("#evidence-annotation-challenge-selector option:selected");//.text().split(",");
    var challenge = $("#evidence-annotation-challenge-selector option:selected").text();//.text().split(",");

    if (verdict == 'Select verdict' || verdict == ''){
      $("#evidence-annotation-verdict-selector").parent().addClass('border border-danger');//parent().parent().attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
    }
    // else if (evidence1 == '[]' && evidence2 == '[]' && evidence3 == '[]'){
    //   $(".annotated-evidence-div").addClass('border border-danger');
    // }
    else if((evidence1 == '[]' || evidence1 == 'null') && ((evidence2 != '[]' && evidence2 != 'null') || (evidence3 != '[]' && evidence3 != 'null'))) {
      alert('Evidence set 1 is empty but 2 or 3 are not. Please make sure to start with evidence set 1!');
    }
    else if((evidence1 == evidence2 || evidence1 == evidence3) && evidence1 != '[]' && evidence1 !== 'null'){
      alert('Some evidence sets are identical. Please do not submit identical annotation sets!');
    }
    else if(evidence2 == evidence3 && evidence2 != '[]' && evidence2 !== 'null'){
      alert('Some evidence sets are identical. Please do not submit identical annotation sets!');
    }
    else if (challenge == '[]' || challenge == '[""]' || challenge == 'Select challenge' || challenge == ''){
      $( "#evidence-annotation-challenge-selector").parent().addClass('border border-danger');
    }
    else{
      return true;
    }
    return false;
  }

  function prepare_submission(){
    [evidence1, details1] = Highlighter.get_selected_final_annotations(1);
    [evidence2, details2] = Highlighter.get_selected_final_annotations(2);
    [evidence3, details3] = Highlighter.get_selected_final_annotations(3);
    // var evidence = JSON.parse(localStorage.getItem('annotations'));
    evidence1 = JSON.stringify(evidence1);
    details1 = JSON.stringify(details1);
    evidence2 = JSON.stringify(evidence2);
    details2 = JSON.stringify(details2);
    evidence3 = JSON.stringify(evidence3);
    details3 = JSON.stringify(details3);
    var search = JSON.parse(localStorage.getItem('search'));
    search = JSON.stringify(search);
    var hyperlinks = JSON.parse(localStorage.getItem('hyperlinks'));
    hyperlinks = JSON.stringify(hyperlinks);
    var order = JSON.parse(localStorage.getItem('order'));
    //order = JSON.stringify(order);
    var page_search = JSON.parse(localStorage.getItem('page_search'));
    page_search = JSON.stringify(page_search);
    questions = JSON.stringify(['NA']);
    answers = JSON.stringify(['NA']);


    var verdict = $( "#evidence-annotation-verdict-selector option:selected").text();
    // var challenge_el = $("#evidence-annotation-challenge-selector option:selected");//.text().split(",");
    var challenge = $("#evidence-annotation-challenge-selector option:selected").text();//.text().split(",");

    // var challenge = [];
    // for (var i = 0; i < challenge_el.length; i++) {
    //   challenge.push($(challenge_el[i]).text());
    // }
    // challenge = JSON.stringify(challenge);
    if (annotation_complete() == true){
      if (evidence1 == 'null'){
        evidence1 = JSON.stringify([]);
        details1 = JSON.stringify([]);
      }
      order.push('finish');
      order= JSON.stringify(order);
      var times = JSON.parse(localStorage.getItem('times'));
      times.push(new Date().getTime());
      times = times.map(function(element){
        return ((parseInt(element) - parseInt(times[0])) / 1000).toString();
      });
      var total_time = times[times.length-1];
      times = JSON.stringify(times);
      var submission_dict =   { user_id: Processor.user_id, claim_id: Processor.claim_id, evidence1: evidence1, details1: details1, evidence2: evidence2, details2: details2, evidence3: evidence3, details3: details3, verdict: verdict, challenge: challenge, search: search, hyperlinks: hyperlinks, order: order, page_search: page_search, times: times, total_time:total_time, questions:questions, answers:answers}

      return submission_dict;
    }
  }

  $(document.body).on('click', '.evidence-annotation-resubmit-button', function(event) {
    var submission_dict = prepare_submission();
    if (submission_dict == null){
      return;
    }
    submission_dict.request = 'evidence-resubmission'
    $.post('annotation-service/evidence_annotation_api.php',submission_dict,
    function(data,status,xhr){
      if(data == -2){
        log_out();
        location.reload();
      }
      if(status !='success'){
        alert("Some error while communicating with the server... Please note the associated claim down and the time it occured.")
      }
      Processor.reset_evidence_menu();
      localStorage.setItem('back-counter', 0);
      Processor.get_next_claim_for_evidence_annotation();
      $(document.body).find(".evidence-annotation-resubmit-button").replaceWith('<button class="my_popup fa fa-check btn btn-success button-responsive"> Submit Annotation </button>');
      $(function () {
        $('[data-toggle="popover"]').popover();
      })
    }
    ,'text');
  });

  $(document.body).on('click', '.evidence-annotation-submit-button', function(event) {
    var submission_dict = prepare_submission();
    if (submission_dict == null){
      return;
    }
    submission_dict.request = 'evidence-submission';

    $.post('annotation-service/evidence_annotation_api.php', submission_dict,
    function(data,status,xhr){
      if(data == -2){
        log_out();
        location.reload();
      }
      if(status !='success'){
        alert("Some error while communicating with the server... Please note the associated claim down and the time it occured.")
      }
      Processor.reset_evidence_menu();
      localStorage.setItem('back-counter', 0);
      Processor.get_next_claim_for_evidence_annotation();
      $('#popup').popup('hide');
    }
    ,'text');
  });

  $(document.body).on('click', '.report-item', function(event) {
    if($(this).hasClass("active")){
      $(this).removeClass("active");
      // $(this).selectpicker("refresh");
    }else{
      $(this).addClass("active");
    }
  });


  $(document.body).on('click', '#go-back', function(event) {
    [evidence1, details1] = Highlighter.get_selected_annotations(1);
    [evidence2, details2] = Highlighter.get_selected_annotations(2);
    [evidence3, details3] = Highlighter.get_selected_annotations(3);
    var back_counter = localStorage.getItem('back-counter');
    if( back_counter == 0 && (evidence1 != null && evidence1.length > 0 || evidence2 != null && evidence2.length > 0 || evidence3 !=null && evidence3.length > 0)){
      alert('Cannot go back to other claims during annotation! Finish your current annotation to move back to other claims.')
      return;
    }

    function convert_database_data_to_interface(evidence, details){
      var evidence1_set = new Set([]);
      var anno_element1 = {};
      var anno_parent1 = {};
      for (var i = 0; i < evidence.length; i++) {
        var curr_ev = evidence[i].split(" [CON] ");
        curr_ev.forEach(item => evidence1_set.add(item));
        curr_ev.forEach(item => (item in anno_element1) ? anno_element1[item]+=1 : anno_element1[item]=1);
        anno_parent1[curr_ev[0]] = curr_ev.slice(1, curr_ev.length);

      }
      evidence = Array.from(evidence1_set);
      var details1_proc = []
      var details1_dict = {};
      for (var i = 0; i < details.length; i++) {
        var ent = details[i].split(" [CON] ");
        details1_dict[ent[0]] = ent[1];
      }
      for (var i = 0; i < evidence.length; i++) {
        details1_proc.push(details1_dict[evidence[i]]);
      }
      return [evidence, details1_proc, anno_element1, anno_parent1];
    }

    $.get('annotation-service/evidence_annotation_api.php', {user_id: Processor.user_id, request: 'reload-evidence',
    back_count:back_counter},function(data,status,xhr){
      if (status == 'error'){
        alert('Server problem');
      }
      if(data == -2){
        log_out();
        location.reload();
      }
      if(data[0] != -1){
        var claim_id = data[0];
        var claim = data[1];
        var verdict = data[2];
        var evidence1_raw = (data[3] == null || data[3][0] == "" || data[3] == "") ? [] : data[3].split(" [SEP] ");
        var details1_raw = (data[3] == null || data[3][0] == "" || data[3] == "") ? [] : data[4].split(" [SEP] ");
        let [evidence1, details1, anno_element1, anno_parent1] = convert_database_data_to_interface(evidence1_raw, details1_raw);
        var evidence2_raw = (data[5] == null || data[5][0] == "" || data[5] == "") ? [] : data[5].split(" [SEP] ");
        var details2_raw = (data[5] == null || data[5][0] == "" || data[5] == "") ? [] : data[6].split(" [SEP] ");
        let [evidence2, details2, anno_element2, anno_parent2] = convert_database_data_to_interface(evidence2_raw, details2_raw);
        var evidence3_raw = (data[7] == null || data[7][0] == "" || data[7] == "") ? [] : data[7].split(" [SEP] ");
        var details3_raw = (data[7] == null || data[7][0] == "" || data[7] == "") ? [] : data[8].split(" [SEP] ");
        let [evidence3, details3, anno_element3, anno_parent3] = convert_database_data_to_interface(evidence3_raw, details3_raw);

        var search = (data[9] != null) ? data[9].split(" [SEP] ") : null;
        var hyperlinks = (data[10] != null) ? data[10].split(" [SEP] ") : null;
        var search_order = data[11].split(" [SEP] ");
        var page_search = (data[12] != null) ? data[12].split(" [SEP] ") : null;
        var total_annotation_time = data[13].split(" [SEP] ");
        var annotation_time_events = (data[14] != null) ? data[14].split(" [SEP] ") : null;
        var challenges = data[15].split(" [SEP] ");
        var questions = data[16].split(" [SEP] ");
        var answers = data[17].split(" [SEP] ");

        Processor.reset_evidence_menu();

        var evidence = {1: evidence1, 2: evidence2, 3: evidence3};
        var details = {1: details1, 2: details2, 3:details3};
        var anno_elements = {1: anno_element1, 2: anno_element2, 3:anno_element3};
        var anno_parents = {1: anno_parent1, 2: anno_parent2, 3:anno_parent3};

        localStorage.setItem('annotations', JSON.stringify(evidence));
        localStorage.setItem('details', JSON.stringify(details));
        localStorage.setItem('anno_elements', JSON.stringify(anno_elements));
        localStorage.setItem('anno_parents', JSON.stringify(anno_parents));

        [evidence, details] = Highlighter.get_annotations();
        Highlighter.init_parents();

        for (var i = 0; i < evidence.length; i++) {
          if(evidence[i] in Highlighter.anno_parents[Highlighter.get_active_annotation_set()]){
          add_evidence_to_interface(evidence[i], details[i]);
        }
        }

        if (evidence.length > 0){
          $("#my-wikipedia").prop('src', base_url + evidence[0].split('_')[0]);
        }
        Highlighter.init();


        localStorage.setItem("search", JSON.stringify(search));
        localStorage.setItem("hyperlinks", JSON.stringify(hyperlinks));
        localStorage.setItem("page_search", JSON.stringify(page_search));
        localStorage.setItem("order", JSON.stringify(search_order));
        localStorage.setItem('times', JSON.stringify(annotation_time_events));

        Processor.claim_id = claim_id;
        Processor.claim_text = claim;

        console.log(parseInt(localStorage.getItem('back-counter')));
        var back_counter = parseInt(localStorage.getItem('back-counter')) + 1;
        localStorage.setItem('back-counter', back_counter);
        localStorage.setItem("jump-url", 0);
        $("#evidence-annotation-verdict-selector").val(verdict);
        $("#evidence-annotation-verdict-selector").selectpicker("refresh");
        $("#evidence-annotation-challenge-selector").val(challenges);
        $("#evidence-annotation-challenge-selector").selectpicker("refresh");
        $('#current-claim').text(claim);

        $(document.body).find(".my_popup").replaceWith('<button class="evidence-annotation-resubmit-button fa fa-refresh btn btn-primary"> Resubmit Annotation </button>');

        // $("#question-enough-selector").val('default');
        // $("#question-enough-selector").selectpicker('refresh');
        // $(".report-item").removeClass('active');
        // $('#report-note').prop('value', '');
        // $('.generated-claim-question').prop('value','');
        // $('.generated-claim-answer').prop('value', '');

        $('#go-forward').prop('disabled', false);
      }else{
        alert('No previously annotated evidence found.');
      }
    }, 'json');
  });

  $(document.body).on('click', '#go-forward', function(event) {
    var back_counter = localStorage.setItem('back-counter', 0);
    Processor.reset_evidence_menu();
    localStorage.setItem('back-counter', 0);
    location.reload();
  });


  $(document.body).on('click', '#report-button', function(event) {
    var active_text = [];
    tags = $('.report-item');
    for(var i = 0; i < tags.length; i++){
      if ($(tags[i]).hasClass("active")){
        active_text.push($(tags[i]).text());
      }
    }
    var custom_note = $('.dropdown-item#report-note').val();
    active_text.push(custom_note);
    active_text = JSON.stringify(active_text);
    if (active_text == '[""]'){
      alert('Please specify why you want to report this claim.');
    }else{
      $.post('annotation-service/evidence_annotation_api.php', { user_id: Processor.user_id, claim_id: Processor.claim_id, request: "report-claim", report_text: active_text},
      function(data,status,xhr){
        if(data == -2){
          log_out();
          location.reload();
        }
        Processor.reset_evidence_menu();
        Processor.get_next_claim_for_evidence_annotation();
        localStorage.setItem('back-counter', 0);
      }
      ,'text');
    }});

    $(document.body).on('click', '.evidence-delete-button', function(event) {
      id = $(this).parent().text().split(' delete')[0];
      Highlighter.evidence_highlighter_delete(id);
      // var ele_trans = id.replaceAll('.', '\\.').replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?');
      // if (id.indexOf('\\') >=0){
      //   $("[id='" + id +  "'].evidence-element").remove();
      // }else{
      //   // console.log(element_trans);
      //   $("[id='" + ele_trans +  "'].evidence-element").remove();
      // }
      //console.log(ele_trans);
    });

    $(document.body).on('click', '.evidence-set', function(event) {
      $('body').find('button').filter(function() {
        Highlighter.undraw_all_annotations();
        $('.evidence-element').remove();
        var id = $(this).attr('id');
        if(id != null && id.slice(-1) == Highlighter.get_active_annotation_set()){
          $(this).removeClass('btn-outline-danger');
        }
      });
      var set_id = $(this).attr('id').slice(-1);
      localStorage.setItem('active_annotation_set', set_id);
      $(this).addClass('btn-outline-danger');
      Highlighter.apply_to_all_elements(Highlighter.redraw_annotations);
      var evidence, details = [];
      [evidence, details] = Highlighter.get_annotations();
      if (evidence != null){
        for (var i = 0; i < evidence.length; i++) {
            if(evidence[i] in Highlighter.anno_parents[Highlighter.get_active_annotation_set()]){
          add_evidence_to_interface(evidence[i], details[i]);
        }
        }
      }
    });
  }

  class Processor {

    static init(){

      console.log("INIT");
      //Variables loaded from localStorage
      Processor.annotation_type = localStorage.getItem('annotation-type');
      Processor.user_id = localStorage.getItem('user');

      var evidence, details = [];
      [evidence, details] = Highlighter.get_annotations();
      // var evidence = JSON.parse(localStorage.getItem('annotations'));
      // var details = JSON.parse(localStorage.getItem('details'));
      // var search = JSON.parse(localStorage.getItem('search'));
      // var hyperlinks = JSON.parse(localStorage.getItem('hyperlinks'));

      if(localStorage.getItem('order')== null){
        localStorage.setItem("order", JSON.stringify(['start']));
        localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
      }
      // localStorage.setItem("order", JSON.stringify(['start']));
      // localStorage.setItem('times', JSON.stringify([new Date().getTime()]));

      localStorage.setItem('back-counter', 0);
      localStorage.setItem("active_annotation_set", 1);
      $('#go-forward').prop('disabled', true);

      Processor.claim_id = null;
      Processor.claim_text = null;

      Processor.get_next_claim_for_evidence_annotation();

      Highlighter.init_parents();
      if (evidence != null){
        for (var i = 0; i < evidence.length; i++) {
          if(evidence[i] in Highlighter.anno_parents[Highlighter.get_active_annotation_set()]){
          add_evidence_to_interface(evidence[i], details[i]);
        }
        }
      }
      $(window).on('popstate', function() {
        Processor.log_back_button();
        history.back();
      });
    }

    static reload_elements(){

      var iframeDoc = $("#my-wikipedia")[0].contentWindow.document;
      Processor.doc = iframeDoc;
      //var $jqObject = $(iframeDoc).find("body");

      $(iframeDoc).find('#mw-indicator-mw-helplink').remove();
      $(iframeDoc).find('.mw-editsection').remove();
      $(iframeDoc).find('#mw-search-top-table').hide();
      //$(iframeDoc).find('#mw-head').hide();
      $(iframeDoc).find('.mw-search-profile-tabs').remove();
      $(iframeDoc).find('#mw-indicator-mw-helplink').remove();

      Processor.adjust_searchbar();
      $(Processor.doc).find('#p-search').append("<input type='text' id='page-search' placeholder='Page search'>");

      if (localStorage.getItem('first-load') == 'false') {
        localStorage.setItem('last-url', $("#my-wikipedia")[0].contentWindow.location.href);
      }else{
        localStorage.setItem('first-load', 'false');
      }
      setTimeout(function(){$('#my-wikipedia').css('visibility', 'visible');}, 100);
      $(Processor.doc).find('body').hide(0).show(0);
      Processor.log_updated_page();
      //localStorage.setItem("jump-url", 0);

      Highlighter.init();
      Processor.add_search_listeners();
    }

    static add_search_listeners(){

      if (window.history && window.history.pushState) {
        window.history.pushState('forward', null, './#forward');
      }

      $(Processor.doc).on('click', '.searchButton', function(event){
        var search_text = $(Processor.doc).find('#searchInput').val();
        // Processor.add_search_to_interface(search_text);
        Processor.log_search(search_text);
        $('#my-wikipedia').css('visibility', 'hidden');
      });

      $(Processor.doc).on('click', '.suggestions-result', function(event){
        var search_text = $(Processor.doc).find('#searchInput').val();
        // Processor.add_search_to_interface(search_text);
        Processor.log_search(search_text);
        $('#my-wikipedia').css('visibility', 'hidden');
      });

      $(Processor.doc).on('click', '.suggestions-special', function(event){
        var search_text = $(Processor.doc).find('#searchInput').val();
        Processor.log_search('Contains...' + search_text);
        $('#my-wikipedia').css('visibility', 'hidden');
      });

      $(Processor.doc).on('click', 'a', function(event){
        var href = $(this).attr("href");
        var check = $(this).attr("class");
        // console.log(check);
        if(href!= null && check != 'mw-searchSuggest-link'){
          var href_text = $(this).text();
          Processor.add_hyperlink_to_interface(href_text);
          Processor.log_hyperlinks(href_text);
          //$('#my-wikipedia').css('visibility', 'hidden');
          // setTimeout(function(){$('#my-wikipedia').css('visibility', 'visible');}, 100);
          //  $(Processor.doc).find('body').hide(0).show(0);
        }
      });


      $(Processor.doc).on('keypress', '.searchButton', (function (e) {
        if (e.which == 13) {
          var search_text = $('#searchInput').val();
          // Processor.add_search_to_interface(search_text);
          Processor.log_search(search_text);
          $('#my-wikipedia').css('visibility', 'hidden');
        }
      }));

      // $("#my-wikipedia")[0].contentWindow.document;
      $(Processor.doc).find("#page-search").on('keypress', function(e) {
        if (e.which == 13) {
          var page_search = JSON.parse(localStorage.getItem('page_search'));
          var order = JSON.parse(localStorage.getItem('order'));
          var times = JSON.parse(localStorage.getItem('times'));
          var v = $(this).val();
          $(Processor.doc).find(".results").css('background','#ffffff');
          $(Processor.doc).find(".results").removeClass("results");
          if (page_search == null){
            page_search = [];
          }
          page_search.push(v);
          // if (order == null){
          //   order = [];
          //   times = [];
          //   // localStorage.setItem("order", JSON.stringify(['start']));
          //   // localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
          // }
          if(v!='') {
            order.push('Page search: ' + v);
            $(Processor.doc).find(Highlighter.elements).each(function () {
              if (v != "" && $(this).text().search(new RegExp(v,'gi')) != -1) {
                $(this).addClass("results");
                $(Processor.doc).find(".results").css('background', '#7b8596');
                // color: white;addClass("results");
              }
            });
          }else{
            order.push('page-search-reset');
          }
          times.push(new Date().getTime());
          localStorage.setItem('times', JSON.stringify(times));
          localStorage.setItem("order", JSON.stringify(order));
          localStorage.setItem("page_search", JSON.stringify(page_search));
        }
      });
    }

    static add_search_to_interface(element){
      //text =  '<input type="text" class="search-term-element" value= ' + element + '> ';
      var text =  '<p class="search-term-element"> Search: ' + element + '</p> ';
      $(".search-terms-annotation-div").append(text);
    }

    static add_hyperlink_to_interface(element){
      //text =  '<input type="text" class="search-term-element" value= ' + element + '> ';
      var text =  '<p class="search-term-element"> Hyperlink: ' + element + '</p> ';
      $(".search-terms-annotation-div").append(text);
    }

    static adjust_searchbar(){
      var ele = $(Processor.doc).find('#p-search');
      var div_search = '<div id="search-div"> </div>';
      $(Processor.doc).find('body').prepend(div_search);
      var search_element = $(Processor.doc).find('#search-div');
      search_element.append(ele);
      // ele.prependTo($(Processor.doc).find('body'));
      search_element.css("position", "relative");
      search_element.css("left", "75%");
      search_element.css("bottom", "3%");
      search_element.css("padding", "2%");

      $(Processor.doc).find('#mw-head').remove();
      $(Processor.doc).find('#siteNotice').remove();

    }


    static log_updated_page(){
      var order = JSON.parse(localStorage.getItem('order'));
      var times = JSON.parse(localStorage.getItem('times'));

      order.push('Now on: ' + $("#my-wikipedia")[0].contentWindow.location.href.split('http://mediawiki.feverous.co.uk/index.php/')[1]);
      times.push(new Date().getTime());

      localStorage.setItem('times', JSON.stringify(times));
      localStorage.setItem("order", JSON.stringify(order));
    }

    static log_back_button(){
      var order = JSON.parse(localStorage.getItem('order'));
      var times = JSON.parse(localStorage.getItem('times'));
      // if (order == null){
      //   order = [];
      //   times = [];
      // }

      order.push('back-button-clicked');
      times.push(new Date().getTime());

      localStorage.setItem('times', JSON.stringify(times));
      localStorage.setItem("order", JSON.stringify(order));
    }


    static log_search(element){
      var search = JSON.parse(localStorage.getItem('search'));
      var order = JSON.parse(localStorage.getItem('order'));
      var times = JSON.parse(localStorage.getItem('times'));
      if (search == null){
        search = [];
      }
      // if (order == null){
      //   order = [];
      //   times = [];
      // }
      search.push(element);
      order.push('search: ' + element);
      times.push(new Date().getTime());

      localStorage.setItem('times', JSON.stringify(times));
      localStorage.setItem("search", JSON.stringify(search));
      localStorage.setItem("order", JSON.stringify(order));
    }

    static log_hyperlinks(element){
      var hyperlinks = JSON.parse(localStorage.getItem('hyperlinks'));
      var order = JSON.parse(localStorage.getItem('order'));
      var times = JSON.parse(localStorage.getItem('times'));
      if (hyperlinks == null){
        hyperlinks = [];
      }
      // if (order == null){
      //   order = [];
      //   times = [];
      // }
      hyperlinks.push(element);
      order.push('hyperlink: ' + element);
      times.push((new Date().getTime()));

      localStorage.setItem('times',  JSON.stringify(times));
      localStorage.setItem("hyperlinks", JSON.stringify(hyperlinks));
      localStorage.setItem("order", JSON.stringify(order));
    }


    static get_next_claim_for_evidence_annotation(){
      $.get('annotation-service/evidence_annotation_api.php', { user_id: Processor.user_id, request: 'next-claim'},function(data,status,xhr){
        if (status != 'success'){
          alert("Some error while communicating with the server... Please note the associated claim down and the time it occured.");
        }else{
          console.log(data[0]);
          if (data[0] === 'finished-calibration'){
            log_out();
            window.location.replace("after_phase1_evidence_annotation.html");
          }else if (data[0] === 'phase2'){
            log_out();
            window.location.replace("after_phase1_evidence_annotation.html");
          }
          Processor.claim_id = data[0];
          Processor.claim_text = data[1];
          $('#current-claim').text(Processor.claim_text);
        }
        $('.login-input').attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
      }, 'json');

      var jump_url = localStorage.getItem("jump-url");
      if (jump_url == 0){
        //window.location.href = data_url;
        $("#my-wikipedia").prop('src', base_url + '?search=');
        localStorage.setItem("jump-url", 1);
      }

    }


    static reset_evidence_menu(){
      $('.evidence-element').remove();
      Highlighter.undraw_all_annotations();
      Highlighter.reset_annotations();
      $('.search-term-element').remove();
      localStorage.setItem("search", null);
      localStorage.setItem("hyperlinks", null);
      localStorage.setItem("page_search", null);
      localStorage.setItem("order", JSON.stringify(['start']));
      localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
      // localStorage.setItem("order", JSON.stringify([]));
      // localStorage.setItem('times', JSON.stringify([]));
      localStorage.setItem("active_annotation_set", 1);
      //localStorage.setItem('first-load', true);
      localStorage.setItem("jump-url", 0);
      $('#go-forward').prop('disabled', true);
      //localStorage.setItem("jump-url", 0);
      $("#evidence-annotation-verdict-selector").val('Select verdict');
      $("#evidence-annotation-verdict-selector").selectpicker("refresh");
      $("#evidence-annotation-challenge-selector").val('Select challenge');
      $("#evidence-annotation-challenge-selector").selectpicker("refresh");

      $('#current-claim').text('Nothing fetched.');
      $("#question-enough-selector").val('default');
      $("#question-enough-selector").selectpicker('refresh');

      $(".report-item").removeClass('active');

      $('#report-note').prop('value', '');

      $('.generated-claim-question').prop('value','');
      $('.generated-claim-answer').prop('value', '');
      //  $( "#dropdown-toggle option:contains('Nothing selected')").prop('selected',true);//text('Choose here');
      //$(".option").removeClass('active');
      //$( "#evidence-annotation-verdict-selector").prop('value',null);//text('Choose here');
      //localStorage.setItem("jump-url", 0);
    }

  }

  function add_evidence_to_interface(element, details){
    if(element.includes('_section_') || element.includes('_title')){
      return;
    }
    var text = '<span class="evidence-element" id="' +  element + '">';
    text += '<details>';
    // text += "<summary>" + element + '</summary>';
    text += "<summary>" + element +'<button style="float:right; font-size:12px" class="evidence-delete-button btn btn-sm btn-danger"> delete </button> </summary>';
    text +=  '<p class="evidence-details">' + details + '</p>';
    text += "</details>";
    // text = '<label for="evidence-element">' + element + '</label>';
    var element_trans = element.replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('.', '\\.').replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?');
    if (element.indexOf('\\') >=0){
      text += "<hr width=" + $('#' + element).css("width") + '\%>';
    }else{
      text += "<hr width=" + $('#' + element_trans).css("width") + '\%>';
    }
    text += '</span>';
    $(".annotated-evidence-div").append(text);
    return text
  }
