var base_url = 'http://mediawiki.feverous.co.uk/index.php/';
$.ajaxSetup({async:false});

$(window).on('load', function() {
  var status_page = localStorage.getItem('status-page');
  if (status_page == 'open'){
    $('body').remove();
  }else{
    run_page();
  }
});
//localStorage.setItem("jump-url", 0);

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

function run_page(){
  auto_logout();
  localStorage.setItem('status-page', 'open');
  $("body").append('<iframe id="my-wikipedia"></iframe>');
  $("#my-wikipedia").prop('src', localStorage.getItem('last-url'));

  $('#my-wikipedia').on("load", function() {
    Processor.reload_elements();
  });

  $(function () {
    $('[data-toggle="popover"]').popover();
  })

  $(function () {
    $('[data-toggle="tooltip"]').tooltip()
  })

  $('input').inputfit();
  $('.evidence-retrieval').attr('data-toggle', 'tooltip').attr('title', 'New Title').tooltip();


  Processor.init();

  $(window).on('beforeunload', function(){
    localStorage.setItem('status-page', 'reload');
    if (localStorage.getItem('back-counter') > 0){
      Processor.reset_claim_generation_menu();
      localStorage.setItem('back-counter', 0);
    }
    //Reset order when page is reloaded. Reaosnable? Prob not.

    // var order = JSON.parse(localStorage.getItem('order'));
    // order.push('Reload page');
    // localStorage.setItem('order', JSON.stringify(order));

  });

  $(".logout").on('click', function(e) {
    log_out();
    window.location.reload();
  });

  $(document.body).on('click', '#generated-claim-skip', function(event) {
    $.get('annotation-service/claim_annotation_api.php', { user_id: Processor.user_id, request: 'skip-annotation'},function(data,status,xhr){
      if (status == 'error'){
        alert('Server problem');
      }else{
        if(data == -2){
          log_out();
          location.reload();
        }
        localStorage.setItem('back-counter', 0);
        Processor.reset_claim_generation_menu();
        Processor.get_data_for_claim_generation();
        location.reload(); //Until bug is fixed
      }
    });
  });


  $(document.body).on('click', '#go-forward', function(event) {
    var back_counter = localStorage.setItem('back-counter', 0);
    Processor.reset_claim_generation_menu();
    localStorage.setItem('back-counter', 0);
    location.reload();
  });


  $(document.body).on('click', '#go-back', function(event) {
    var generated_claim = $("#generated-claim").val();
    var back_counter = localStorage.getItem('back-counter');
    if( back_counter == 0 && generated_claim != null && generated_claim != ''){
      alert('Cannot go back to other claims during annotation! Finish your current annotation to move back to other claims.')
      return;
    }

    $.get('annotation-service/claim_annotation_api.php', {user_id: Processor.user_id, request: 'reload-claim',
    back_count:back_counter},function(data,status,xhr){
      if (status == 'error'){
        alert('Server problem');
      }
      if(data == -2){ // Not sure this works as it should return array
        log_out();
        location.reload();
      }
      if(data[0] != -1){
        var claim = data[0];
        var claim_extended = data[1];
        var claim_manipulation = data[2];
        var data_source = data[3];
        var selected_id = data[4];
        var manipulation = data[5];
        var multiple_pages = data[6];
        var page = data[7];
        if (data[8] != null){
          var search = data[8].split(" [SEP] ");
        }else{
          var search = null;
        }
        if(data[9] != null){
          var hyperlinks = data[9].split(" [SEP] ");
        }else{
          var hyperlinks = null;
        }
        var search_order = data[10].split(" [SEP] ");
        var total_annotation_time = data[11].split(" [SEP] ");
        if (data[12] != null){
          var annotation_time_events = data[12].split(" [SEP] ");
        }else{
          var annotation_time_events = null;
        }
        var challenges = data[13];
        var challenges_ext = data[14];
        var challenges_man = data[15];
        var is_table = data[16];
        var veracity = data[17];


        Processor.reset_claim_generation_menu();
        var back_counter = parseInt(localStorage.getItem('back-counter')) + 3;

        localStorage.setItem('back-counter', back_counter);
        localStorage.setItem("jump-url", 0);
        localStorage.setItem("search", JSON.stringify(search));
        localStorage.setItem("hyperlinks", JSON.stringify(hyperlinks));
        localStorage.setItem("order", JSON.stringify(search_order));
        localStorage.setItem('times', JSON.stringify(annotation_time_events));


        // localStorage.setItem('generated-claim', claim);
        // localStorage.setItem('generated-claim-extended', claim_extended);
        // localStorage.setItem('generated-claim-manipulation', claim_manipulation);
        $('#generated-claim').prop('value', claim);
        $('#generated-claim-extended').prop('value',claim_extended);
        $('#generated-claim-manipulation').prop('value', claim_manipulation);
        $('#manipulations').prop('value', manipulation);

        $( "#claim-annotation-challenge-selector").val(challenges);
        $( "#claim-annotation-challenge-selector").selectpicker("refresh");
        $( "#claim-annotation-challenge-selector-extended").val(challenges_ext);
        $( "#claim-annotation-challenge-selector-extended").selectpicker("refresh");
        $( "#claim-annotation-challenge-selector-manipulation").val(challenges_man);
        $( "#claim-annotation-challenge-selector-manipulation").selectpicker("refresh");

        Processor.data_id = data_source; //used for sending off the annotation to server
        Processor.data_selected_id = selected_id;
        Processor.data_url = page
        Processor.is_table = is_table

        $('#claim_url').html('<b>' + page + "</b>");
        $('#manipulations').html("Mutated Claim <b>(" + manipulation + ")</b>:");
        if(multiple_pages == 1){
          $('#multiple-pages').html("Claim beyond highlight <b>(Multiple pages)</b>:");
        }
        else{
          $('#multiple-pages').html("Claim beyond highlight <b>(Same page)</b>:");
        }
        if (veracity == 0){
          $('#claim-highlight').html("Claim using highlight: <b>(False)</b>:");
        }
        else if (veracity==1){
          $('#claim-highlight').html("Claim using highlight: <b>(True)</b>:");
        }

        //$('body html').scrollTo($("p:contains('" + data_table_id + "')").next());
        var jump_url = localStorage.getItem("jump-url");
        if (jump_url == 0){
          //window.location.href = data_url;
          $("#my-wikipedia").prop('src', base_url + '?search=' + page);
          localStorage.setItem("jump-url", 1);
        }

        $("#generated-claim-skip").hide();
        $(document.body).find("#generated-claim-submit").replaceWith('<button id="generated-claim-resubmit" class="fa fa-refresh btn btn-primary"> Resubmit Annotation </button>');


        $('#go-forward').prop('disabled', false);
      }else{
        alert('No previously annotated claims found.');
      }
    }, 'json');
  });

  $(document.body).on('click', '#generated-claim-return', function(event) {
    $("#my-wikipedia").prop('src', base_url + '?search=' + Processor.data_url);
    var order = JSON.parse(localStorage.getItem('order'));
    order.push('Jump to Highlight');
    localStorage.setItem('order', JSON.stringify(order));
  });

  // $(document.body).on('input', '#generated-claim-extended', function(event) {
  // localStorage.setItem('generated-claim-extended', $("#generated-claim-extended").val());
  //   // var times = JSON.parse(localStorage.getItem('times'));
  //   // times.push(new Date().getTime())
  //   // var order = JSON.parse(localStorage.getItem('order'));
  //   //   order.push('write extended: ' + this.value);
  //   // localStorage.setItem('times', JSON.stringify(times));
  //   // localStorage.setItem('order', JSON.stringify(order));
  //
  // });
  //
  //
  // $(document.body).on('input', '#generated-claim-manipulation', function(event) {
  //   localStorage.setItem('generated-claim-manipulation', $("#generated-claim-manipulation").val());
  //   // var times = JSON.parse(localStorage.getItem('times'));
  //   // times.push(new Date().getTime())
  //   // var order = JSON.parse(localStorage.getItem('order'));
  //   //   order.push('write manipulation: ' + this.value);
  //   // localStorage.setItem('times', JSON.stringify(times));
  //   // localStorage.setItem('order', JSON.stringify(order));
  // });
  //
  //
  //
  // $(document.body).on('input', '#generated-claim', function(event) {
  //   localStorage.setItem('generated-claim', $("#generated-claim").val());
  //   // var times = JSON.parse(localStorage.getItem('times'))
  //   // times.push(new Date().getTime());
  //   // var order = JSON.parse(localStorage.getItem('order'));
  //   // order.push('write: ' + this.value);
  //   // localStorage.setItem('times', JSON.stringify(times));
  //   // localStorage.setItem('order', JSON.stringify(order));
  //
  // });


  function prepare_submission(){
    $( "#claim-annotation-challenge-selector").parent().removeClass('border border-danger');
    $( "#claim-annotation-challenge-selector-extended").parent().removeClass('border border-danger');
    $( "#claim-annotation-challenge-selector-manipulation").parent().removeClass('border border-danger');

    // var generated_claim = localStorage.getItem('generated-claim');
    // var generated_claim_extended = localStorage.getItem('generated-claim-extended');
    // var generated_claim_manipulation = localStorage.getItem('generated-claim-manipulation');

    var generated_claim =   $("#generated-claim").val();
    var generated_claim_extended =   $("#generated-claim-extended").val();
    var generated_claim_manipulation =   $("#generated-claim-manipulation").val();

    var order = JSON.parse(localStorage.getItem('order'));
    var search = JSON.stringify(JSON.parse(localStorage.getItem('search')));
    var hyperlinks = JSON.stringify(JSON.parse(localStorage.getItem('hyperlinks')));

    // var main_challenge_claim = $( "#claim-annotation-challenge-selector option:selected").text();
    var challenge = $( "#claim-annotation-challenge-selector option:selected").text();

    // console.log(main_challenge_claim);
    // var challenge = [];
    // for (var i = 0; i < main_challenge_claim.length; i++) {
    //   challenge.push($(main_challenge_claim[i]).text());
    // }
    // challenge = JSON.stringify(challenge);
    // var main_challenge_extended = $( "#claim-annotation-challenge-selector-extended option:selected").text();
    var challenge_extended = $( "#claim-annotation-challenge-selector-extended option:selected").text();

    // var challenge_extended = [];
    // for (var i = 0; i < main_challenge_extended.length; i++) {
    //   challenge_extended.push($(main_challenge_extended[i]).text());
    // }
    // challenge_extended = JSON.stringify(challenge_extended);
    // var main_challenge_manipulation = $( "#claim-annotation-challenge-selector-manipulation option:selected").text();
    var challenge_manipulation = $( "#claim-annotation-challenge-selector-manipulation option:selected").text();

    // var challenge_manipulation = [];
    // for (var i = 0; i < main_challenge_manipulation.length; i++) {
    //   challenge_manipulation.push($(main_challenge_manipulation[i]).text());
    // }
    // challenge_manipulation = JSON.stringify(challenge_manipulation);

    //Also check if claim is from totto or tabfacts
    if (generated_claim == null || generated_claim == ''){
      $( '#generated-claim').attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
    }
    else if (generated_claim_extended == null || generated_claim_extended == ''){
      $( "#generated-claim-extended").attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
    }
    else if (generated_claim_manipulation == null || generated_claim_manipulation == ''){
      $( "#generated-claim-manipulation").attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
    }
    else if (challenge == '[]' || challenge == '[""]' || challenge == 'Select challenge'){
      $( "#claim-annotation-challenge-selector").parent().addClass('border border-danger');
    }
    else if (challenge_extended == '[]' || challenge_extended == '[""]' || challenge_extended == 'Select challenge'){
      $( "#claim-annotation-challenge-selector-extended").parent().addClass('border border-danger');
    }
    else if (challenge_manipulation == '[]' || challenge_manipulation == '[""]' || challenge_manipulation == 'Select challenge'){
      $( "#claim-annotation-challenge-selector-manipulation").parent().addClass('border border-danger');
    }
    else{
      order.push('finish');
      order= JSON.stringify(order);
      var times = JSON.parse(localStorage.getItem('times'));
      times.push(new Date().getTime());
      times = times.map(function(element){
        return ((parseInt(element) - parseInt(times[0])) / 1000).toString();
      });
      var total_time = times[times.length-1];
      times = JSON.stringify(times);

      var submission_dict =   { user_id: Processor.user_id, data_id: Processor.data_id,   claim: generated_claim, claim_extended: generated_claim_extended, search: search, hyperlinks: hyperlinks, order: order, times:times, total_time:total_time, claim_manipulation: generated_claim_manipulation, challenge: challenge, challenge_extended: challenge_extended, challenge_manipulation: challenge_manipulation};
      return submission_dict;
    }
  }

  $(document.body).on('click', '#generated-claim-resubmit', function(event) {
    var submission_dict = prepare_submission();
    if (submission_dict == null){
      return;
    }
    submission_dict.request = 'claim-resubmission'

    $.post('annotation-service/claim_annotation_api.php',submission_dict,
    function(data,status,xhr){
      if(status !='success'){
        alert("Some error while communicating with the server... Please note the associated claim down and the time it occured.")
      }
      if(data == -2){
        log_out();
        location.reload();
      }
      Processor.reset_claim_generation_menu();
      Processor.get_data_for_claim_generation();
      localStorage.setItem('back-counter', 0);
      $(document.body).find("#generated-claim-resubmit").replaceWith('<button id="generated-claim-submit" class="fa fa-check btn btn-success"> Submit Annotation </button>');
    }
    ,'text');
  });

  $(document.body).on('click', '#generated-claim-submit', function(event) {
    var submission_dict = prepare_submission();
    if (submission_dict == null){
      return;
    }
    submission_dict.request = 'claim-submission';
    $.post('annotation-service/claim_annotation_api.php',submission_dict,
    function(data,status,xhr){
      if(data == -2){
        log_out();
        location.reload();
      }
      localStorage.setItem('back-counter', 0);
      Processor.reset_claim_generation_menu();
      Processor.get_data_for_claim_generation();
      //console.log(data); // need to pass auth id of user to retrieve respective claim. To make sure claim is server-bound.
    }
    ,'text');
  });
}


class Processor {

  static init(){
    //Variables loaded from localStorage
    Processor.annotation_type = localStorage.getItem('annotation-type');
    Processor.user_id = localStorage.getItem('user');
    Processor.times = [];

    Processor.data_id = null;
    Processor.data_selected_id = null;
    //Processor.reset_claim_generation_menu();
    localStorage.setItem("jump-url", 0);
    localStorage.setItem('first-load', true);
    localStorage.setItem("order", JSON.stringify(['start']));
    localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
    localStorage.setItem("hyperlinks", JSON.stringify([]));
    localStorage.setItem('search', JSON.stringify([]));
    localStorage.setItem('back-counter', 0);
    $('#go-forward').prop('disabled', true);
    // $('#generated-claim').spellAsYouType();
    // $('#generated-claim').css('display', 'inline-block');
    //   $('#generated-claim').css('position', 'relative');
    // $('#generated-claim').css('top', '0.5em');
    // $('#generated-claim-extended').spellAsYouType();
    // $('#generated-claim-extended').css('display', 'inline-block');
    // $('#generated-claim-extended').css('position', 'relative');
    // $('#generated-claim-extended').css('top', '0.5em');
    // $('#generated-claim-manipulation').spellAsYouType();
    // $('#generated-claim-manipulation').css('display', 'inline-block');
    // $('#generated-claim-manipulation').css('position', 'relative');
    // $('#generated-claim-manipulation').css('top', '0.5em');
    Processor.get_data_for_claim_generation();

    $(window).on('popstate', function() {
      Processor.log_back_button();
      history.back();
    });

  }


  static reload_elements(){
    //var $jqObject = $(iframeDoc).find("body");
    var iframeDoc = $("#my-wikipedia")[0].contentWindow.document;
    Processor.doc = iframeDoc;
    Processor.title = $(Processor.doc).find('#firstHeading').text().replaceAll(' ','-');
    $(Processor.doc).find('#mw-indicator-mw-helplink').remove();
    $(Processor.doc).find('.mw-editsection').remove();
    $(Processor.doc).find('#mw-search-top-table').hide();
    //$(iframeDoc).find('#mw-head').hide();
    $(Processor.doc).find('.mw-search-profile-tabs').remove();
    $(Processor.doc).find('#mw-indicator-mw-helplink').remove();
    $(Processor.doc).find('body').hide(0).show(0);
    Processor.adjust_searchbar();

    localStorage.setItem('last-url', $("#my-wikipedia")[0].contentWindow.location.href);
    setTimeout(function(){$('#my-wikipedia').css('visibility', 'visible');}, 100);
    $(Processor.doc).find('body').hide(0).show(0);
    if(Processor.is_table == 1){
      $(Processor.doc).find("p:contains('" + Processor.data_selected_id.replaceAll('.', '\\.').replaceAll("''", "'").replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").next().css('border-style','solid').css('border-width', 'thick').css('border-color', 'coral');
      var offset = $(Processor.doc).find("p:contains('" + Processor.data_selected_id.replaceAll('.', '\\.').replaceAll("''", "'").replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").next().offset();
    }else{
      var sentences = Processor.data_selected_id.replaceAll("''", "'").split(" [SEP] ");
      var offset = $(Processor.doc).find("p:contains('" + sentences[0].replaceAll('.', '\\.').replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?') + "')").offset();
      for(var i = 0; i < sentences.length; i++){
        $(Processor.doc).find("p").filter(function() {
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
    localStorage.setItem('first-load', 'false');
    localStorage.setItem("jump-url", 0); //Allow jumps again
    Processor.log_updated_page();
    Processor.add_search_listeners();
  }

  static add_search_listeners(){


    if (window.history && window.history.pushState) {
      window.history.pushState('forward', null, './#forward');
    }


    $(Processor.doc).on('click', '.searchButton', function(event){
      var search_text = $(Processor.doc).find('#searchInput').val();
      Processor.log_search(search_text);
      $('#my-wikipedia').css('visibility', 'hidden');
    });

    $(Processor.doc).on('click', '.suggestions-special', function(event){
      var search_text = $(Processor.doc).find('#searchInput').val();
      Processor.log_search('Contains...' + search_text);
      $('#my-wikipedia').css('visibility', 'hidden');
    });

    // $(document.body).on('click', '.gsc-search-button-v2', function(event){
    //   console.log('yao')
    //   // var search_text = $(Processor.doc).find('#searchInput').val();
    //   // Processor.log_search(search_text);
    //   // $('#my-wikipedia').css('visibility', 'hidden');
    // });
    //
    // $(document.body).on('click', 'a', function(event){
    //   var href = $(this).attr("href");
    //   var check = $(this).attr("class");
    //   if(href!= null && check != 'mw-searchSuggest-link'){
    //     var href_text = $(this).text();
    //     Processor.log_hyperlinks(href_text);
    //     //$('#my-wikipedia').css('visibility', 'hidden');
    //   }
    //   $('.gsc-results-wrapper-overlay').fadeOut(0);
    //   $('.gsc-modal-background-image').fadeOut(0);
    //   return false;
    // });


    $(Processor.doc).on('click', '.suggestions-result', function(event){
      var search_text = $(Processor.doc).find('#searchInput').val();
      Processor.log_search(search_text);
      $('#my-wikipedia').css('visibility', 'hidden');
    });



    $(Processor.doc).on('click', 'a', function(event){
      var href = $(this).attr("href");
      var check = $(this).attr("class");
      if(href!= null && check != 'mw-searchSuggest-link'){
        var href_text = $(this).text();
        Processor.log_hyperlinks(href_text);
        //$('#my-wikipedia').css('visibility', 'hidden');
      }
    });

    $(Processor.doc).on('keypress', '.searchButton', (function (e) {
      if (e.which == 13) {
        var search_text = $('#searchInput').val();
        Processor.log_search(search_text);
        $('#my-wikipedia').css('visibility', 'hidden');
      }
    }));
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
    hyperlinks.push(element);
    order.push('hyperlink: ' + element);
    times.push(new Date().getTime());

    localStorage.setItem('times', JSON.stringify(times));
    localStorage.setItem("hyperlinks", JSON.stringify(hyperlinks));
    localStorage.setItem("order", JSON.stringify(order));
  }

  static adjust_searchbar(){
    var ele = $(Processor.doc).find('#p-search');
    ele.prependTo($(Processor.doc).find('body'));
    ele.css("position", "relative");
    ele.css("left", "75%");
    ele.css("top", "15%");

    $(Processor.doc).find('#mw-head').remove();

  }

  static get_data_for_claim_generation(){
    $.get('annotation-service/claim_annotation_api.php', { user_id: Processor.user_id, request: 'next-data'},function(data,status,xhr){
      if (status != 'success'){
        alert('Server problem');
      }else{
        if (data[0] === 'finished-calibration'){
          log_out();
          window.location.replace("after_phase1_claim_annotation.html");
        }else if (data[0] === 'phase2'){
          log_out();
          window.location.replace("after_phase1_claim_annotation.html");
        }
        Processor.data_id = data[0]; //used for sending off the annotation to server
        var data_url = data[1];
        var is_table = data[2];
        var data_selected_id = data[3];
        Processor.data_selected_id = data_selected_id;
        var manipulation = data[4];
        var quick_hyperlinks = data[5];
        var multiple_pages = data[6];
        var veracity = data[7];

        if (data_url === null){
          data_url = 'NO NEW HIGHLIGHT AVAILABLE.'
        }

        Processor.is_table = is_table;
        Processor.data_url = data_url

        $('#claim_url').html('<b>' + data_url + "</b>");
        $('#manipulations').html("Mutated Claim <b>(" + manipulation + ")</b>:");

        if(multiple_pages == 1){
          $('#multiple-pages').html("Claim beyond highlight <b>(Multiple pages)</b>:");
        }
        else{
          $('#multiple-pages').html("Claim beyond highlight <b>(Same page)</b>:");
        }

        if (veracity == 0){
          $('#claim-highlight').html("Claim using highlight: <b>(False)</b>:");
        }
        else if (veracity==1){
          $('#claim-highlight').html("Claim using highlight: <b>(True)</b>:");
        }
        // if (is_table == 1){
        //   $('#selected_id').text('[Table] ' + data_selected_id);
        // }else{
        //   $('#selected_id').text('[Sentence] ' + data_selected_id);
        // }
        //$('body html').scrollTo($("p:contains('" + data_table_id + "')").next());
        var jump_url = localStorage.getItem("jump-url");
        if (jump_url == 0){
          //window.location.href = data_url;
          $("#my-wikipedia").prop('src', base_url + '?search=' + data_url);
          localStorage.setItem("jump-url", 1);
        }

        // localStorage.setItem('generated-claim', '');
        // localStorage.setItem('generated-claim-extended', '');
        // localStorage.setItem('generated-claim-manipulation', '');

        // if (localStorage.getItem('generated-claim') != null){
        //   $('#generated-claim').prop('value',localStorage.getItem('generated-claim'));
        //
        // }
        // if (localStorage.getItem('generated-claim-extended') != null){
        //   $('#generated-claim-extended').prop('value',localStorage.getItem('generated-claim-extended'));
        // }
        // if (localStorage.getItem('generated-claim-manipulation') != null){
        //   $('#generated-claim-manipulation').prop('value',localStorage.getItem('generated-claim-manipulation'));
        // }
      }
    }, 'json');
    //Processor.times.push(new Date().getTime());
    //console.log(Processor.times);
  }

  static reset_claim_generation_menu(){
    // localStorage.setItem('generated-claim', '');
    // localStorage.setItem('generated-claim-extended', '');
    // localStorage.setItem('generated-claim-manipulation', '');
    //localStorage.setItem('order', null);
    //localStorge.setItem('times', null);
    // $('#generated-claim').prop('value',localStorage.getItem('generated-claim'));
    // $('#generated-claim-extended').prop('value',localStorage.getItem('generated-claim-extended'));
    // $('#generated-claim-manipulation').prop('value',localStorage.getItem('generated-claim-manipulation'));


    $('#generated-claim').prop('value','');
    $('#generated-claim-extended').prop('value','');
    $('#generated-claim-manipulation').prop('value','');

    $('#manipulations').prop('value', 'Not specified.');
    $('#manipulations').removeClass('fa fa-exclamation-triangle');

    $( "#claim-annotation-challenge-selector").val('Select challenge');
    $( "#claim-annotation-challenge-selector").selectpicker("refresh");
    $( "#claim-annotation-challenge-selector-extended").val('Select challenge');
    $( "#claim-annotation-challenge-selector-extended").selectpicker("refresh");
    $( "#claim-annotation-challenge-selector-manipulation").val('Select challenge');
    $( "#claim-annotation-challenge-selector-manipulation").selectpicker("refresh");

    $('#claim_url').prop('value', 'No data retrieved.');
    $('.claims-hyperlinks').empty();  // $('.totto-claim').remove();
    localStorage.setItem("jump-url", 0);
    localStorage.setItem("order", JSON.stringify(['start']));
    localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
    localStorage.setItem('first-load', true);
    localStorage.setItem('hyperlinks', null);
    localStorage.setItem('search', null);


    // localStorage.setItem("order", JSON.stringify(['start']));
    // localStorage.setItem('times', JSON.stringify([new Date().getTime()]));
  }


}
