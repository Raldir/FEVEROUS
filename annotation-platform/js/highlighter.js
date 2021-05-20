//$(document).on('click', 'p', function() {alert("rect clicked");})
//var annotations = [];
// if (annotations.length != details.length){
//   console.log("Wot");
// }

class Highlighter {
  constructor(){}

  static init(){

    Highlighter.doc = $("#my-wikipedia")[0].contentWindow.document;
    Highlighter.title = $(Highlighter.doc).find('#firstHeading').text()//.replaceAll(' ','-')//.replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('.', '\\.');
    if(Highlighter.title != 'Search-results' &&  Highlighter.title != 'Search'){
      $(Highlighter.doc).find('#firstHeading').append('<span style="visibility: hidden;font-size:1px">' + Highlighter.title + '_title</span>');
    }

    $('.evidence-set').removeClass('btn-outline-danger');
    $('body').find('button').filter(function() {
      var id = $(this).attr('id');
      if(id != null && id.slice(-1) == Highlighter.get_active_annotation_set()){
        $(this).addClass('btn-outline-danger');
      }
    });

    // Highlighter.apply_to_all_elements(Highlighter.highlight);
    // Highlighter.apply_to_all_elements(Highlighter.mouseover_highlight_in);
    // Highlighter.apply_to_all_elements(Highlighter.mouseover_highlight_out);
    // Highlighter.apply_to_all_elements(Highlighter.redraw_annotations);


    Highlighter.identifier = ['_title', '_sentence_', '_cell_', '_item_', '_section_', 'table_caption'];
    Highlighter.elements = 'h1, h2, h3, h4, h5, p, li, caption, td, th';
    Highlighter.init_parents();
    // Highlighter.elements_list = ['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li', 'caption', 'td', 'th'];
    // Highlighter.identifier_list = ['_title', '_section_', '_section_','_section_','_section_', '_sentence_', '_item_',  'table_caption', '_cell_', '_sentence_in_table_', '_item_in_table_'];


    Highlighter.apply_to_all_elements(Highlighter.redraw_annotations);
    Highlighter.apply_to_hoverable_elements(Highlighter.mouseover_highlight_in)
    Highlighter.apply_to_hoverable_elements(Highlighter.mouseover_highlight_out)
    Highlighter.apply_to_clickable_elements(Highlighter.highlight)
  }

  static init_parents(){
    Highlighter.anno_elements = JSON.parse(localStorage.getItem('anno_elements'));
    if(Highlighter.anno_elements == null){
      Highlighter.anno_elements = {1: {}, 2:{}, 3:{}};
    }
    Highlighter.anno_parents = JSON.parse(localStorage.getItem('anno_parents'));
    if(Highlighter.anno_parents == null){
      Highlighter.anno_parents = {1: {}, 2:{}, 3:{}};
    }
  }


  static apply_to_all_elements(func){
    func('h1', '_title');
    func('p', '_sentence_');
    func('td', '_cell_');
    func('th', '_cell_');
    func('li', '_item_');
    func('dt', '_item_');
    func('h2', '_section_');
    func('h3', '_section_');
    func('h4', '_section_');
    func('h5', '_section_');
    func('caption', 'table_caption');
  }

  static apply_to_clickable_elements(func){
    func('p', '_sentence_');
    func('p', '_cell_');
    func('td', '_cell_');
    func('th', '_cell_');
    func('li', '_item_');
    func('dt', '_item_');
    func('caption', 'table_caption');
  }

  static apply_to_hoverable_elements(func){
    func('p', '_sentence_');
    func('td', '_cell_');
    func('th', '_cell_');
    func('li', '_item_');
    func('dt', '_item_');
    func('caption', 'table_caption');
  }

  static undraw_all_annotations(){
    Highlighter.apply_to_all_elements(Highlighter.undraw_annotations);
  }

  static unbind_element(element){
    $(element).unbind();
  }

  static redraw_annotations(type, identifier){
    var annotations, details = [];
    [annotations, details] = Highlighter.get_annotations();
    if (annotations != null){
      for (var i = 0; i < annotations.length; i++) {
        $(Highlighter.doc).find(type).filter(function() {
          var raw_id= $(this).find("span").text();
          if(identifier.includes('_section_')){
            var is_right = Highlighter.title + '_section_' +  raw_id.substring(raw_id.lastIndexOf("_") + 1,  raw_id.length) === annotations[i];
          }
          else{
            var is_right = raw_id === annotations[i];
          }
          if (is_right){
            if(['_title', '_section_'].includes(identifier) || !(raw_id in Highlighter.anno_parents[Highlighter.get_active_annotation_set()])){
              $(this).css( "background-color", 'rgba(240, 255, 0, 0.3)').css('outline', '2px solid black');
            }else{
              $(this).css( "background-color", 'yellow').css('outline', '2px solid black');
            }//css('border', '2px solid black');
          }
          //.find("span").text());//.css( "background-color", 'yellow').css('border', '2px solid black');
        });
      }// $(type).filter(function() { return $(this).find("span").text() === annotations[i];}).css( "background-color", 'yellow');
    }
  }//

  static undraw_annotations(type, identifier){
    var annotations, details = [];
    [annotations, details] = Highlighter.get_annotations();
    if (annotations != null){
      for (var i = 0; i < annotations.length; i++) {
        $(Highlighter.doc).find(type).filter(function() {
          var raw_id= $(this).find("span").text();
          if(identifier.includes('_section_')){
            var is_right = Highlighter.title + '_section_' +  raw_id.substring(raw_id.lastIndexOf("_") + 1,  raw_id.length) === annotations[i];
          }
          else{
            var is_right = raw_id === annotations[i];
          }
          if (is_right){
            $(this).css( "background-color", '').css('outline', 'none');//.css('border', '');
          }
          //.find("span").text());//.css( "background-color", 'yellow').css('border', '2px solid black');
        });
      }// $(type).filter(function() { return $(this).find("span").text() === annotations[i];}).css( "background-color", 'yellow');
    }
  }//


  static substring_in_list(list, string){
    length = list.length;
    while(length--) {
      if (string.indexOf(list[length])!=-1) {
        return true;
        // one of the substrings is in yourstring
      }
    }
    return false;
  }


      // if($(this).get(0).tagName == 'P'){
      //   identifier = '_sentence_';
      // }else if($(this).get(0).tagName == 'LI' || $(this).get(0).tagName == 'DT'){
      //   identifier = '_item_';
      // }
      // else if($(this).get(0).tagName == 'TD' || $(this).get(0).tagName == 'TH'){
      //   identifier = '_cell_';
      // }
      // Highlighter.highlight_piece(id_span, identifier, 0, 0);
      // Highlighter.highlight_trace(this, id_span, identifier);

  static remove_highlight(id){
    $(Highlighter.doc).find(Highlighter.elements).filter(function() {
      var raw_id= $(this).find("span").text();
      if(id.includes('_section_')){
        var is_right = Highlighter.title + '_section_' +  raw_id.substring(raw_id.lastIndexOf("_") + 1,  raw_id.length) === id;
      }else{
        is_right = raw_id === id;
      }
      if (is_right){
        var id_span =$(this).find("span");
        $(id_span.parent()).css( "background-color", '').css('outline', 'none');

        if($(id_span.parent().parent()).get(0).tagName == 'TD' || $(id_span.parent().parent()).get(0).tagName == 'TH'){
          $(id_span.parent().parent()).css( "background-color", '').css('outline', 'none');
        }
  }
});
}
  static evidence_highlighter_delete(id){
    var annotations, details = [];
    [annotations, details] = Highlighter.get_annotations();
    Highlighter.remove_highlight(id);
    for (var i = 0; i < Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id].length; i++) {
      var curr_ele =  Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id][i];
      if (curr_ele in Highlighter.anno_elements[Highlighter.get_active_annotation_set()]){
        Highlighter.anno_elements[Highlighter.get_active_annotation_set()][curr_ele] -=1;
      }else{
        Highlighter.anno_elements[Highlighter.get_active_annotation_set()][curr_ele] =0;
      }
      if(Highlighter.anno_elements[Highlighter.get_active_annotation_set()][curr_ele] == 0){
        const index = annotations.indexOf(curr_ele);
        annotations.splice(index, 1);
        details.splice(index, 1);
        Highlighter.remove_highlight(curr_ele);
      }
    }
    const index = annotations.indexOf(id);
    annotations.splice(index, 1);
    details.splice(index, 1);
    if (id in Highlighter.anno_elements[Highlighter.get_active_annotation_set()]){
      Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] -=1;
    }else{
      Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] =0;
    }
    var element_trans =  id.replaceAll('.', '\\.').replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?');
    if (id.indexOf('\\') >=0){
      $("[id='" + id +  "'].evidence-element").remove()
    }else{
      // console.log(element_trans);
      $("[id='" + element_trans +  "'].evidence-element").remove()
    }
    delete Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id];
    Highlighter.set_annotations(annotations, details)
    localStorage.setItem('anno_parents',JSON.stringify(Highlighter.anno_parents));
    localStorage.setItem('anno_elements',JSON.stringify(Highlighter.anno_elements));
  }

  static reset_annotations(){
    localStorage.setItem("annotations", null);
    localStorage.setItem("details", null);
    localStorage.setItem("anno_elements",  JSON.stringify({1: {}, 2:{}, 3:{}}));
    localStorage.setItem("anno_parents",  JSON.stringify({1: {}, 2:{}, 3:{}}));
    return [[], []];
  }

  static get_active_annotation_set(){
    var ann = localStorage.getItem('active_annotation_set');
    if (ann == null){
      localStorage.setItem('active_annotation_set', 1);
      ann = 1;
    }
    return ann;
  }

  static get_annotations(){
    var annotations = JSON.parse(localStorage.getItem('annotations'))
    var details = JSON.parse(localStorage.getItem('details'))
    if(annotations != null){
      annotations =  annotations[localStorage.getItem('active_annotation_set')];
      details = details[localStorage.getItem('active_annotation_set')];
    }
    return [annotations, details];
  }


  static get_selected_final_annotations(index){
    var annotations = JSON.parse(localStorage.getItem('annotations'))
    var details = JSON.parse(localStorage.getItem('details'))
    if(annotations != null){
      annotations =  annotations[index];
      details = details[index];
    }
    var stringfied_evidence = [];
    for (var key in Highlighter.anno_parents[index]){
      if(Highlighter.anno_parents[index][key].length == 0){
        continue;
      }
      var temp = [key];
      stringfied_evidence.push(temp.concat(Highlighter.anno_parents[index][key].join(' [CON] ')).join(' [CON] '));
    }
    var stringfied_details = [];
    for (var i = 0; i < annotations.length; i++) {
      stringfied_details.push(annotations[i] + ' [CON] ' + details[i]);
    }
    console.log(JSON.stringify(stringfied_evidence.join( ' [SEP] ')));
    console.log(JSON.stringify(stringfied_details.join( ' [SEP] ')));
    return [stringfied_evidence, stringfied_details];
  }
  static get_selected_annotations(index){
    var annotations = JSON.parse(localStorage.getItem('annotations'))
    var details = JSON.parse(localStorage.getItem('details'))
    if(annotations != null){
      annotations =  annotations[index];
      details = details[index];
    }
    return [annotations, details];
  }


  static set_annotations(annotations, details){
    var index = Highlighter.get_active_annotation_set();
    var annotations_full = JSON.parse(localStorage.getItem('annotations'));
    var details_full = JSON.parse(localStorage.getItem('details'));
    if (annotations_full == null){
      annotations_full = {1: [], 2:[], 3:[]};
      details_full = {1:[], 2:[], 3:[]};
    }
    annotations_full[index] = annotations;
    details_full[index] = details;
    localStorage.setItem("annotations", JSON.stringify(annotations_full));
    localStorage.setItem("details", JSON.stringify(details_full));

    // console.log(annotations_full[1].join(" [SEP] "));
    // console.log(details_full[1].join(" [SEP] "));
  }

  static countOccurences(string, word) {
    return string.split(word).length - 1;
  }


  static highlight_section(element, id_span, section_type, prev_head, not_remove){
    var last_ele = element;
    while($(last_ele).length >0 && ![section_type].includes($(last_ele).get(0).tagName)){
      if($(last_ele).prev().length == 0){
        last_ele =  $(last_ele).parent();
      }
      else if (prev_head.includes($(last_ele).prev().get(0).tagName)) {
        return;
      }else{
        last_ele = $(last_ele).prev();
      }
    }
    var section_span= $(last_ele).find("span");
    if(typeof section_span.find('span') != "undefined" && section_span.find('span').text() != ''){
      Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id_span.text()].push(section_span.find('span').text());
    }
    Highlighter.highlight_piece(section_span, '_section_', not_remove, id_span.text());
    return section_span.find('span');
  }


  static get_colspan(element, type){
    var index_list = [];
    var curr_index = 0;
    $(element).find(type).each(function() {
      index_list.push(this.colSpan + curr_index);
      curr_index += this.colSpan;
    });
    return index_list;
  }

static correct_wrongly_highlighted(id){
  if (id in Highlighter.anno_parents[Highlighter.get_active_annotation_set()]){
      Highlighter.evidence_highlighter_delete(id);
    }
}
  static get_cell_index(ele){
    var td = $(ele).closest("td,th");
    var col = 0;
    td.prevAll().each(function () { col += $(this).prop('colspan'); });
    var row_pos = td.closest("tr");
    var row = row_pos.index();
    var rowspans = row_pos.prevAll().find("td[rowspan],th[rowspan]");
    // var tbody = td.closest('thead,tbody,tfoot');
    // var rowspans = tbody.find("td[rowspan],th[rowspan]");
    rowspans.each(function () {
      var rs = $(this);
      var rsIndex = rs.closest("tr").index();
      // if(rsIndex > $(ele).closest("tr").index()){
      //   return;
      // }
      var rsQuantity = rs.prop("rowspan");
      if (row > rsIndex && row <= rsIndex + rsQuantity - 1) {
        var rsCol = 0;
        rs.prevAll().each(function () { rsCol += $(this).prop('colspan'); });
        if (rsCol <= col) col += rs.prop('colspan');
      }
    });
    if($(ele).prop("rowspan") > 1){
      var row_max = row + $(ele).prop("rowspan") - 1;
    }
    if($(ele).prop("colspan") > 1){
      var col_max = col + $(ele).prop("colspan") - 1;
    }
    return  { row: row, col: col, row_max: row_max, col_max:col_max};
  }

  static highlight_trace(element, id_span, identifier){
    var id = id_span.text();
    if (id.includes("_section_")){ //breaks down section since include edit text
      id = Highlighter.title+ '_section_' +  id.substring(id.lastIndexOf("_") + 1,  id.length);
    }
    if (id.includes(identifier)){
      var annotations, details = [];
      [annotations, details] = Highlighter.get_annotations();
      if(id in Highlighter.anno_parents[Highlighter.get_active_annotation_set()] && Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id].length > 0){
        var reset_parents = 1;
      }else{
        var reset_parents = 0;
      }
      Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id] = [];
      var not_remove = 0;
      if(Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] >= 1){
        var not_remove = 1;
      }
      $(Highlighter.doc).find('h1').filter(function() {
        var title_span = $(this).find("span");
        var title_id = title_span.text();
        Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id].push(title_id);
        Highlighter.highlight_piece(title_span, '_title', not_remove, id);
      });

      var sectionh2 = Highlighter.highlight_section(element, id_span, 'H2', [], not_remove);
      var sectionh3 = Highlighter.highlight_section(element, id_span, 'H3', ['H2'], not_remove);
      var sectionh4 = Highlighter.highlight_section(element, id_span, 'H4', ['H2', 'H3'], not_remove);
      var sectionh5 = Highlighter.highlight_section(element, id_span, 'H5', ['H2', 'H3', 'H4'], not_remove);
      var sectionh6 = Highlighter.highlight_section(element, id_span, 'H6', ['H2', 'H3', 'H4', 'H5'], not_remove);


      if($(element).get(0).tagName == 'TD' || $(element).parent().get(0).tagName == 'TD' ){
        var element_index = Highlighter.get_cell_index(element);
        var tbody = $(element).closest('thead,tbody,tfoot');
        var all_th = tbody.find('th');
        var header_closest_col = [];
        var header_closest_row = [];
        var header_closest_col_eles = [];
        var header_closest_row_eles = [];
        var min_dist_row = 1000;
        var min_dist_col = 1000;
        for (var i = 0; i < all_th.length; i++) {
          var header_index = Highlighter.get_cell_index(all_th[i]);
          var dist_ele_row = Math.abs(header_index.row - element_index.row);
          var dist_ele_col = Math.abs(header_index.col - element_index.col);
          if ((header_index.col == element_index.col ||(header_index.col_max >= element_index.col && header_index.col < element_index.col)) && header_index.row < element_index.row && dist_ele_row < min_dist_row){
            header_closest_row.push(header_index);
            header_closest_row_eles.push(all_th[i]);
            min_dist_row = dist_ele_row;
          }
          else if ((header_index.row == element_index.row || (header_index.row_max >= element_index.row && header_index.row < element_index.row)) && header_index.col < element_index.col && dist_ele_col < min_dist_col){
            header_closest_col.push(header_index);
            header_closest_col_eles.push(all_th[i]);
            min_dist_col = dist_ele_col;
          }
        }
        var header_closest_col_final = [];
        var header_closest_row_final = [];

        for (var i = header_closest_col.length -1; i >=0; i--){
          if(Math.abs(header_closest_col[i].col - element_index.col) > min_dist_col && header_closest_col[i+1].col != header_closest_col[i].col -1){
            break;
          }
          else{
            header_closest_col_final.push(header_closest_col_eles[i]);
          }
        }
        for (var i = header_closest_row.length -1; i >=0; i--){
          if(Math.abs(header_closest_row[i].row - element_index.row) > min_dist_row && header_closest_row[i+1].row -1 != header_closest_row[i].row){
            break;
          }
          else{
            header_closest_row_final.push(header_closest_row_eles[i]);
          }
        }


        for (var i = 0; i < header_closest_col_final.length; i++) {
          Highlighter.correct_wrongly_highlighted($(header_closest_col_final[i]).find("span").text());
          Highlighter.highlight_piece($(header_closest_col_final[i]).find("span"), '_header_cell_', not_remove, id);
          Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id].push($(header_closest_col_final[i]).find("span").text());
        }
        for (var i = 0; i < header_closest_row_final.length; i++) {
          Highlighter.correct_wrongly_highlighted($(header_closest_row_final[i]).find("span").text());
          Highlighter.highlight_piece($(header_closest_row_final[i]).find("span"), '_header_cell_', not_remove, id);
          Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id].push($(header_closest_row_final[i]).find("span").text());
        }
      }

      if(reset_parents == 1){
        delete Highlighter.anno_parents[Highlighter.get_active_annotation_set()][id]; //Resets all parents if has been clicked before because this means that it is now declicked.
      }
      localStorage.setItem('anno_parents',JSON.stringify(Highlighter.anno_parents));
    }
  }

  static in_parent(id){
    for (var key in Highlighter.anno_parents[Highlighter.get_active_annotation_set()]){
      if(Highlighter.anno_parents[Highlighter.get_active_annotation_set()][key].includes(id)){
        return 1;
      }
    }
    return 0;
  }
  static highlight(type, identifier){
    $(Highlighter.doc).on('click', type, function(event) {
      event.stopPropagation();
      if(!$(event.target).closest('a').length){ // Skips annotation if clicked on href
        var id_span =$(this).find("span");
        if(!Highlighter.in_parent(id_span.text())){
          Highlighter.highlight_piece(id_span, identifier, 0, 0);
          Highlighter.highlight_trace(this, id_span, identifier);
          Highlighter.apply_to_all_elements(Highlighter.redraw_annotations);
        }
      }
    });
  }

  static highlight_piece(id_span, identifier, not_remove, main_id){
    var id = id_span.text();
    if (id.includes("_section_")){ //breaks down section since include edit text
      id = Highlighter.title+ '_section_' +  id.substring(id.lastIndexOf("_") + 1,  id.length);
    }
    if (id.includes(identifier)){ //check whether the identifier is included in id
      //if (Highlighter.substring_in_list(Highlighter.identifier,id)){ //check whether the identifier is included in id
      var annotations, details = [];
      [annotations, details] = Highlighter.get_annotations();
      if (annotations === null){
        [annotations, details] = Highlighter.reset_annotations();
      }
      if (!annotations.includes(id)){
        if (id.includes("_section_")){
          var detail = id_span.text();
          var comb = (id + id);
          detail = detail.substring(0, detail.indexOf(id + id));
        }
        else if (id.includes("_header_cell_")){
          // var detail = id_span.parent().text(); //TODO ADD LIST ID TO LISTS IN TABLES!!!!
          var detail = id_span.closest('th').text(); //TODO ADD LIST ID TO LISTS IN TABLES!!!!
          detail = detail.substring(0, detail.indexOf(id));
        }
        else if (id.includes("_cell_")){
          // var detail = id_span.parent().text(); //TODO ADD LIST ID TO LISTS IN TABLES!!!!
          var detail= id_span.closest('td').text(); //TODO ADD LIST ID TO LISTS IN TABLES!!!!
          detail = detail.substring(0, detail.indexOf(id));
        }
        else{
          var detail = id_span.parent().text(); //TODO ADD LIST ID TO LISTS IN TABLES!!!!
          detail = detail.substring(0, detail.indexOf(id));
        }
        if( Highlighter.countOccurences(id, 'sentence') > 1 || Highlighter.countOccurences(detail,'_sentence_') > 0){
          detail = 'Tokenization error in the highlighted sentence: ' + id;
        }
        annotations.push(id);
        details.push(detail);
        if((!['_title', '_section_'].includes(identifier)) && !(main_id in Highlighter.anno_parents[Highlighter.get_active_annotation_set()])) {
          add_evidence_to_interface(id, detail); // The calling process is weird. change..
        }
        var times = JSON.parse(localStorage.getItem('times'));
        var order = JSON.parse(localStorage.getItem('order'));
        order.push('Highlighting: ' + id);
        times.push(new Date().getTime());
        localStorage.setItem('times', JSON.stringify(times));
        localStorage.setItem("order", JSON.stringify(order));
        if (id in Highlighter.anno_elements[Highlighter.get_active_annotation_set()]){
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] +=1;
        }else{
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] =1;
        }
      }
      else if (Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] ==1 && not_remove == 0){
        const index = annotations.indexOf(id);
        annotations.splice(index, 1);
        details.splice(index, 1);
        var element_trans =  id.replaceAll('.', '\\.').replaceAll('(', '\\(').replaceAll(')', '\\)').replaceAll("'", "\\'").replaceAll('&', '\\&').replaceAll('!', '\\!').replaceAll('?', '\\?');
        if (id.indexOf('\\') >=0){
          $("[id='" + id +  "'].evidence-element").remove()
        }else{
          $("[id='" + element_trans +  "'].evidence-element").remove()
        }
        $(id_span.parent()).css( "background-color", '').css('outline', 'none');

        if($(id_span.parent().parent()).get(0).tagName == 'TD' || $(id_span.parent().parent()).get(0).tagName == 'TH'){
          $(id_span.parent().parent()).css( "background-color", '').css('outline', 'none');
        }
        if (id in Highlighter.anno_elements[Highlighter.get_active_annotation_set()]){
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] -=1;
        }else{
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] =0;
        }
        var times = JSON.parse(localStorage.getItem('times'));
        var order = JSON.parse(localStorage.getItem('order'));
        order.push('Highlighting deleted: ' + id);
        times.push(new Date().getTime());
        localStorage.setItem('times', JSON.stringify(times));
        localStorage.setItem("order", JSON.stringify(order));
      }
      else if (not_remove == 0){
        Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] -=1;
      }
      else{
        if (id in Highlighter.anno_elements[Highlighter.get_active_annotation_set()]){
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] +=1;
        }else{
          Highlighter.anno_elements[Highlighter.get_active_annotation_set()][id] =1;
        }
      }
      Highlighter.set_annotations(annotations, details)
      localStorage.setItem('anno_elements',JSON.stringify(Highlighter.anno_elements));
    }
  }

  static mouseover_highlight_in(type, identifier){
    $(Highlighter.doc).on('mouseover',  type, function(event) {
      //console.log('hi')
      var id = $(this).find("span").text();
      if (id.includes(identifier)){
        //if (Highlighter.substring_in_list(Highlighter.identifier,id)){
        //$(this).css('border', '2px solid black');
        $(this).css('outline', '2px solid black');
        //$(this).addClass('highlight-candidate');
      }
    })
  }

  static mouseover_highlight_out(type, identifier){
    $(Highlighter.doc).on('mouseout',  type, function(event) {
      var id = $(this).find("span").text();
      //alert($(this).css("background-color"))
      if (id.includes(identifier) && $(this).css("background-color") != 'rgb(255, 255, 0)'){ //yellow
        // $(this).css('border','none');
        $(this).css('outline', 'none');
      }
    })
  }

}
