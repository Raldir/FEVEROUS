/* Any JavaScript here will be loaded for all users on every page load. */

$( document ).ready(function() {
var elements = $('.new');
for (var i = 0; i < elements.length; i++) {
$(elements[i]).replaceWith($(elements[i]).text());
}

//.replaceWith($(this).text());//contents().unwrap();​​
});
