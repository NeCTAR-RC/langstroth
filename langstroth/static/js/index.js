function getQueryVariable(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if(pair[0] == variable){return pair[1];}
  }
  return(false);
}

function setActiveButtons() {
  var start = getQueryVariable('start');
  if (start) {
    if (start[0] == '-') {
      start = start.substring(1);
    }
    $("#graph-buttons").find("a").each(function () {
      var id = $(this).attr('id');
      if (start === id) {
        $(this).addClass('active');
      } else {
        $(this).removeClass('active');
      }
    });
  }
}

$(function () {
  setActiveButtons();
});
