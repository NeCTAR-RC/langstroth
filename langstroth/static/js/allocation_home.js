var dataset = [];

function zero(array) {
  for (var i in array) {
    array[i].value = 0;
  }
}

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

var tooltip = d3.select('#viz')
      .append('div')
      .attr('class', 'chart-tooltip');

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

d3.selectAll("#graph-buttons li a").on("click", change);


// Perform an in-place update of the data
function update(dest, source) {
  hash_map = {};
  for (var i in source) {
    hash_map[source[i].target] = source[i];
  }

  for (var j in dest) {
    var key = dest[i].target;
    if (source[key]) {
      dest[i].value = source[key].value;
    }
  }

  for (var k in hash_map) {
    if (hash_map.hasOwnProperty(k)) {
      dest.push(hash_map[k]);
    }
  }
}


function change() {
  $('#graph-buttons li a').removeClass('active');
  $(this).find("a").addClass('active');

  $.get( "/allocation_home/cores_per_allocation_home", {'az': this.id}, function( data ) {
    zero(dataset);
    update(dataset, data);
    // clearTimeout(timeout);
    var new_path = svg.selectAll("g.slice").data(pie(dataset));

    var total_vcpu = d3.sum(dataset, function (d) {
      return d.value;
    });


    // update elements
    svg.select("text.total")
      .attr("dy", ".40em")
      .style("text-anchor", "middle")
      .text(function(d) { return "VCPU Used: " + total_vcpu; });

    new_path.select('path')
      .transition()
      .duration(750)
      .attrTween("d", arcTween);

    new_path.selectAll('text').remove();

    new_path
      .filter(function(d) { return d.endAngle - d.startAngle > 0.1; })
      .append("text")
      .text(function(d) {
        return d.data.target;
      })
      .attr("transform", function(d) {
        return "translate(" + offset_label(d, this.getComputedTextLength()) + ") rotate(" + angle(d) + ")";
      })
      .style("opacity", 0)
      .transition()
      .duration(400)
      .style("opacity", 1);

    new_path.filter(function(d) { return d.endAngle - d.startAngle > 0.1; })
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
      .text(function(d) { return d.data.value; })
      .style("opacity", 0)
      .transition()
      .duration(400)
      .style("opacity", 1);

    // new elements
    var g = new_path.enter()
          .append('g')
          .attr('class', 'slice');

    g.append("path")
      .attr("fill", function (d, i) {
        return color(i);
      })
      .attr('d', arc(enterClockwise))
      .each(function (d) {
        this._current = {
          data: d.data,
          value: d.value,
          startAngle: enterAntiClockwise.startAngle,
          endAngle: enterAntiClockwise.endAngle
        };
      })
      .transition()
      .duration(750)
      .attrTween("d", arcTween);

    new_path.on("mousemove", function(d){
      tooltip.style("left", d3.event.pageX+10+"px");
      tooltip.style("top", d3.event.pageY-30+"px");
      tooltip.style("display", "inline-block");
      tooltip.html("<b>"+d.data.target+"</b><br>"+(d.data.value)+" VCPUs");
    });
    new_path.on("mouseout", function(d){
      tooltip.style("display", "none");
    });

    g.filter(function(d) { return d.endAngle - d.startAngle > 0.1; })
      .append("text")
      .text(function(d) {
        return d.data.target;
      })
      .attr("transform", function(d) {
        return "translate(" + offset_label(d, this.getComputedTextLength()) + ") rotate(" + angle(d) + ")";
      }).style("opacity", 0)
      .transition()
      .duration(400)
      .style("opacity", 1);

    g.filter(function(d) { return d.endAngle - d.startAngle > 0.1; }).append("svg:text")
      .attr("dy", ".35em")
      .attr("text-anchor", "middle")
      .attr("transform", function(d) {
        d.outerRadius = outerRadius;
        d.innerRadius = outerRadius/2;
        return "translate(" + arc.centroid(d) + ")rotate(" + angle(d) + ")";
      })
      .style("fill", "White")
      .style("font", "bold 12px Arial")
      .text(function(d) { return d.data.value; })
      .style("opacity", 0)
      .transition()
      .duration(400)
      .style("opacity", 1);



    // remove old elements
    new_path.exit().select('text')
      .transition()
      .duration(400)
      .style("opacity", 0)
      .remove();

    new_path.exit().select('fill')
      .transition()
      .duration(750)
      .attrTween('d', arcTweenOut)
      .remove();

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

function arcTween(a) {
  var i = d3.interpolate(this._current, a);
  this._current = i(0);
  return function(t) {
    return arc(i(t));
  };
}

function arcTweenOut(a) {
  var i = d3.interpolate(this._current, {startAngle: Math.PI * 2, endAngle: Math.PI * 2, value: 0});
  this._current = i(0);
  return function (t) {
    return arc(i(t));
  };
}

$("#filter-all a").click();
