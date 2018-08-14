$(function () {
    var $dropdown = $('#comment_dropdown');
   $dropdown.on('click',function (e) {
       var $target = $(e.target)
       $target.is('a') && $('#comment_btn').text($target.text())

   })
});