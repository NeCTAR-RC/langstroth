function getQueryVariable(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i = 0; i < vars.length; i++) {
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
    $("#graph-buttons").find("li").each(function () {
      var id = $(this).attr('id');
      if (start === id) {
        $(this).find("a").addClass('active');
      } else {
        $(this).find("a").removeClass('active');
      }
    });
  }
}

$(function () {
  setActiveButtons();
});
