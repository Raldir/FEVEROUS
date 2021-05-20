$( document ).ready(function() {
   var base_url = 'http://mediawiki.feverous.co.uk/index.php';
 $(document.body).on('click', '#login-button', function(){
   localStorage.clear();
   var login_id = $("#login-id").val();
   var login_pw = $("#login-pw").val();
   var login_pw_md5 = $.md5(login_pw);
   $.get('annotation-service/login.php', { id: login_id, pw: login_pw_md5},function(data,status,xhr){
     var success = data[0];
     var annotation_type = data[1];
     var finished_calibration = data[2];
   if (success == 0){
   $('.login-input').attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
   msg = "Invalid username and password!";
   $("#message").html(msg);
   }
   else{
     localStorage.setItem("annotation-type", annotation_type);
     localStorage.setItem("user", login_id);
     localStorage.setItem('last-url', base_url + '?search=');
     localStorage.setItem('first-load', 'true');
     localStorage.setItem('finished-calibration', finished_calibration);
   location.reload();
 }
 }, 'json');
})

$("#login-pw").on('keypress', function(e){
   if (e.which == 13) {
  localStorage.clear();
  var login_id = $("#login-id").val();
  var login_pw = $("#login-pw").val();
  var login_pw_md5 = $.md5(login_pw);
  $.get('annotation-service/login.php', { id: login_id, pw: login_pw_md5},function(data,status,xhr){
    success = data[0];
    annotation_type = data[1];
  if (success == 0){
  $('.login-input').attr('style', "border-radius: 5px; border:#FF0000 1px solid;");
  msg = "Invalid username and password!";
  $("#message").html(msg);
  }else{
    localStorage.setItem("annotation-type", annotation_type);
    localStorage.setItem("user", login_id);
    localStorage.setItem('last-url', base_url + '?search=');
    localStorage.setItem('first-load', 'true');
  location.reload();
}
}, 'json');
}
})
});
