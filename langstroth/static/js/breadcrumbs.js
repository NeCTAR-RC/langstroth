// Breadcrumbs - keep track of the current hierarchy level.


function Breadcrumbs() {
  // Made up of an array of FOR codes.
  this.breadCrumbs = ['*'];
}

// Is this the level for FOR codes or projects.
Breadcrumbs.prototype.isForCodeLevel = function () {
  return this.breadCrumbs.length < 4;
}

Breadcrumbs.prototype.route = function() {
  return this.breadCrumbs.slice(1).reverse();
}

Breadcrumbs.prototype.routeIn = function (forCode) {
  this.breadCrumbs.push(forCode);
  return this.route();
}

Breadcrumbs.prototype.routeOut = function() {
  this.breadCrumbs.pop();
  return this.route();
}

Breadcrumbs.prototype.home = function() {
  this.breadCrumbs.length == 1
}

Breadcrumbs.prototype.navigate = function(adjustPage) {
  var self = this;
  var breadcrumb = d3.select("#chart-navigator-1").select('.breadcrumb');
  breadcrumb.selectAll('li').remove();
  breadcrumb.selectAll('li')
    .data(this.breadCrumbs)
    .enter()
    .append("li")
    .attr("class", function(d, i) { return i == self.breadCrumbs.length - 1 ?
        "active" : ""; })
    .html(function(d, i) {
      var forCode = d;
      var markup = forCode == '*' ?
          '<span class="glyphicon glyphicon-home"></span>'
            : '<span style="text-transform: capitalize">' +
            forTitleMap[forCode].toLowerCase() +
            '</span>';
      if (i < self.breadCrumbs.length - 1) {
        markup = '<a href="#">' + markup + '</a>';
      }
      return markup;
    })
    .on("click", function(d, i) {
      if (self.breadCrumbs.length > 1 && i < self.breadCrumbs.length - 1) {
        self.breadCrumbs = self.breadCrumbs.slice(0, i + 1);
        adjustPage(self.route(), i);
      }
    });
}


