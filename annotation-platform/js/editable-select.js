$(function() {
  var content = "<input type='text'class='bss-input' data-toggle='tooltip' title='Add item by either clicking the button or pressing enter.' onKeyDown='event.stopPropagation();' onKeyPress='addSelectInpKeyPress(this,event)' onClick='event.stopPropagation()' placeholder='Add item to list'> <span class='fa fa-lg fa-plus additemspan' onClick='addSelectItem(this,event,1);'></span>";

  var divider = $('<option/>')
          .addClass('dropdown-divider')
          .data('divider', true);


    $(function () {
      $('[data-toggle="tooltip"]').tooltip()
    })

  var addoption = $('<option/>', {class: 'addItem', disabled: 'true'})
          .data('content', content)

  $('.selectpicker')
          //.append(divider)
          .prepend(addoption)
          .selectpicker();

});

function appendInput(){
  var content = "<input type='text' class='bss-input' onKeyDown='event.stopPropagation();' onKeyPress='addSelectInpKeyPress(this,event)' onClick='event.stopPropagation()' placeholder='Add item'> <span class='bx bx-plus addnewicon' onClick='addSelectItem(this,event,1);'></span>";
  var inputEle = $('.addItem.dropdown-item span.text');
  $('.addItem.dropdown-item span.text').each(function(index, el) {
    if ($(this).text() == '') {
    }
  });
}

$('body').on('click', '.dropdown-toggle', function(event) {
  event.preventDefault();
  / Act on the event /
  appendInput();
});

function addSelectItem(t,ev)
{
   ev.stopPropagation();

   var bs = $(t).closest('.bootstrap-select')
   var txt=bs.find('.bss-input').val().replace(/[|]/g,"");
   var txt=$(t).prev().val().replace(/[|]/g,"");
   if ($.trim(txt)=='') return;

   // Changed from previous version to cater to new
   // layout used by bootstrap-select.
   var p=bs.find('select');
   var o=$('option', p).eq(-2);
   o.before( $("<option>", { "selected": true, "text": txt}) );
   p.selectpicker('refresh');
	appendInput();
}

function addSelectInpKeyPress(t,ev)
{
   ev.stopPropagation();

   // do not allow pipe character
   if (ev.which==124) ev.preventDefault();

   // enter character adds the option
   if (ev.which==13)
   {
      ev.preventDefault();
      addSelectItem($(t).next(),ev);
   }
}
