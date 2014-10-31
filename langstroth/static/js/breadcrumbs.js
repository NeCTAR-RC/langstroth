// Breadcrumbs - keep track of the current hierarchy level.

var MAX_FOR_CODE_LEVEL = 4;

function Breadcrumbs() {
  // Made up of an array of FOR codes.
  this.breadCrumbs = ['*'];
}

// Set the breadcrumbs to home only.
Breadcrumbs.prototype.clear = function () {
  this.breadCrumbs = ['*'];
};

// The current FOR code. Zero padded to 6 digits.
Breadcrumbs.prototype.getZeroPaddedForCode = function () {
  var forCode = null;
  if (this.breadCrumbs.length <= MAX_FOR_CODE_LEVEL) {
    forCode = this.breadCrumbs[this.breadCrumbs.length - 1];
    var padding = ['', '00', '0000', '000000'];
    forCode += padding[3 - forCode.length / 2]
  }
  return forCode;
};

//Is this the level for FOR codes or projects.
Breadcrumbs.prototype.isForCodeLevel = function () {
  return this.breadCrumbs.length < MAX_FOR_CODE_LEVEL;
};

Breadcrumbs.prototype.setRoute = function(route) {
  this.breadCrumbs = route.concat(['*']).reverse();
};

Breadcrumbs.prototype.route = function() {
  return this.breadCrumbs.slice(1).reverse();
};

Breadcrumbs.prototype.routeIn = function (forCode) {
  this.breadCrumbs.push(forCode);
  return this.route();
};

Breadcrumbs.prototype.routeOut = function() {
  this.breadCrumbs.pop();
  return this.route();
};

Breadcrumbs.prototype.isHome = function() {
  return this.breadCrumbs.length == 1;
};

Breadcrumbs.prototype.title = function(forCode, i) {
  return 0 < i && i < MAX_FOR_CODE_LEVEL ? forTitleMap[forCode].toLowerCase()
		  : forCode;
};

Breadcrumbs.prototype.navigate = function(adjustPage) {
  var self = this;
  var breadcrumb = d3.select("#chart-navigator-1").select('.breadcrumb');
  breadcrumb.selectAll('li').remove();
  breadcrumb.selectAll('li')
    .data(self.breadCrumbs)
    .enter()
    .append("li")
    .attr("class", function(d, i) {
          return i == self.breadCrumbs.length - 1 ? "active" : "";
    })
    .html(function(d, i) {
      var forCode = d;
      var markup = forCode == '*' ?
          '<span class="glyphicon glyphicon-home"></span>'
            : '<span style="text-transform: capitalize">' +
            self.title(forCode, i) +
            '</span>';
      if (i < self.breadCrumbs.length - 1) {
        markup = '<a href="#">' + markup + '</a>';
      }
      return markup;
    })
    .on("click", function(d, i) {
      if (self.breadCrumbs.length > 1 && i < self.breadCrumbs.length - 1) {
        self.breadCrumbs = self.breadCrumbs.slice(0, i + 1);
        if (adjustPage) {
            adjustPage(self.route(), i);
        }
      }
    });
};
