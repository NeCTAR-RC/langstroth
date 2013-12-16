
var dataset = [];


var width = 960,
    height = 700,
    pie_width = 960,
    pie_height = 500,
    radius = Math.min(pie_width, pie_height) / 2;

var outerRadius = radius - 20;

var enterClockwise = {
  startAngle: 0,
  endAngle: 0
};

var enterAntiClockwise = {
  startAngle: Math.PI * 2,
  endAngle: Math.PI * 2
};


var x = d3.scale.linear()
      .range([0, 2 * Math.PI]);

var color = d3.scale.category20();

var pie = d3.layout.pie()
      .value(function(d) { return d.value; });

var arc = d3.svg.arc()
      .innerRadius(radius - 120)
      .outerRadius(outerRadius);

var svg = d3.select("#viz").append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

svg.append("text").attr("class", "total");

// set the start and end angles to 0 so we can transition
// clockwise to the actual values later
var path = svg.selectAll("g.slice")
      .data(pie([]))
      .enter()
      .append('g')
      .attr('class', 'slice');

path.transition()  // update
  .duration(750)
  .attrTween("d", arcTween);

d3.selectAll("button").on("click", change);

// var timeout = setTimeout(function() {
//   $("button").click();
// }, 2000);

function change() {
  $.get( "/domain/cores_per_domain", {'az': this.id}, function( data ) {
    // clearTimeout(timeout);
    var new_path = svg.selectAll("g.slice").data(pie(data));

    var total_vcpu = d3.sum(data, function (d) {
      return d.value;
    });

    // update elements
    svg.select("text.total")
      .attr("dy", ".40em")
      .style("text-anchor", "middle")
      .text(function(d) { return "VCPU Used: " + total_vcpu; });
    new_path.select('path').attr('d', arc);
    new_path.selectAll('text').remove();
    new_path
      .filter(function(d) { return d.endAngle - d.startAngle > .1; })
      .append("text")
      .text(function(d) {
        return d.data.target;
      })
      .attr("transform", function(d) {
        return "translate(" + offset_label(d, this.getComputedTextLength()) + ") rotate(" + angle(d) + ")";
      });

    new_path.filter(function(d) { return d.endAngle - d.startAngle > .1; })
      .append("text")
      .attr("dy", ".35em")
      .attr("text-anchor", "middle")
      .attr("transform", function(d) {
        d.outerRadius = outerRadius;
        d.innerRadius = outerRadius/2;
        return "translate(" + arc.centroid(d) + ")rotate(" + angle(d) + ")";
      })
      .style("fill", "White")
      .style("font", "bold 12px Arial")
      .text(function(d) { return d.data.value; });



    // new elements
    var g = new_path.enter()
          .append('g')
          .attr('class', 'slice');

    g.append("path")
      .attr("fill", function (d, i) {
        return color(i);
      })
      .attr('d', arc);

    g.filter(function(d) { return d.endAngle - d.startAngle > .1; })
      .append("text")
      .text(function(d) {
        return d.data.target;
      })
      .attr("transform", function(d) {
        return "translate(" + offset_label(d, this.getComputedTextLength()) + ") rotate(" + angle(d) + ")";
      });

    g.filter(function(d) { return d.endAngle - d.startAngle > .1; }).append("svg:text")
      .attr("dy", ".35em")
      .attr("text-anchor", "middle")
      .attr("transform", function(d) {
        d.outerRadius = outerRadius;
        d.innerRadius = outerRadius/2;
        return "translate(" + arc.centroid(d) + ")rotate(" + angle(d) + ")";
      })
      .style("fill", "White")
      .style("font", "bold 12px Arial")
      .text(function(d) { return d.data.value; });


    // remove old elements
    new_path.exit().transition().remove();

  });
}

function offset_label(d, length) {
  //we have to make sure to set these before calling arc.centroid
  d.outerRadius = outerRadius; // Set Outer Coordinate
  d.innerRadius = outerRadius/2; // Set Inner Coordinate
  var center = arc.centroid(d), // gives you the center point of the slice
      x = center[0],
      y = center[1],
      h = Math.sqrt(x*x + y*y),
      blx = x/h * 250,
      bly = y/h * 250,
      lx = x/h * (250 + length),
      ly = y/h * (250 + length);
  var a = (d.startAngle + d.endAngle) * 90 / Math.PI - 90;
  if (a > 90) {
    return lx + "," + ly;
  } else  {
    return blx + "," + bly;
  }
}
// Computes the angle of an arc, converting from radians to degrees.
function angle(d) {
  var a = (d.startAngle + d.endAngle) * 90 / Math.PI - 90;
  return a > 90 ? a - 180 : a;
}

// Store the displayed angles in _current.
// Then, interpolate from _current to the new angles.
// During the transition, _current is updated in-place by d3.interpolate.
function arcTween(a) {

  var i = d3.interpolate({data: a.data, value: a.data.value, startAngle: enterAntiClockwise.startAngle, endAngle: enterAntiClockwise.endAngle
                         }, a);
  return function(t) {
    return arc(i(t));
  };
}
function arcTweenOut(a) {
  var i = d3.interpolate({data: a.data, value: a.data.value, startAngle: enterAntiClockwise.startAngle, endAngle: enterAntiClockwise.endAngle},
                         {startAngle: Math.PI * 2, endAngle: Math.PI * 2, value: 0});
  return function (t) {
    return arc(i(t));
  };
}

$("#all").click();
