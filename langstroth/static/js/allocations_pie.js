////// Hierarchical Pie Plot of NeCTAR Allocations

// Depends on code in breadcrumbs.js, colour_palette.js
// and allocations.js
var breadcrumbs = new Breadcrumbs();
var colourPalette = new ColourPalette();
var allocations = new Allocations();

//==== Data manipulation

var forTitleMap = {};

//==== String utilities

// String abbreviate to set length
// and signify abbreviation by adding ellipsis.
String.prototype.abbreviate = function(charCount) {
  var labelStr = this;
  if (this.length > charCount) {
    labelStr = this.substring(0, charCount - 3) + "...";
  }
  return labelStr;
};

// String remove underscores so long string will wrap.
String.prototype.makeWrappable = function() {
  var labelStr = this;
  var regex = new RegExp("_", "g");
  labelStr = labelStr.replace(regex, " ");
  return labelStr;
};

//==== Data visualisation

//---- Visualisation Constants

// Chart dimensions
var WIDTH = 500,
    HEIGHT = 500,
    PIE_WIDTH = 500,
    PIE_HEIGHT = 500,
    RADIUS = Math.min(PIE_WIDTH, PIE_HEIGHT) / 2;

var ZOOM_OUT_MESSAGE = "Click to zoom out!";

var INNER_RADIUS = RADIUS - 120;
var OUTER_RADIUS = RADIUS - 20;

// Animation speed - duration in msec.
var DURATION = 750;
var DURATION_FAST = 400;

var enterClockwise = {
  startAngle: 0,
  endAngle: 0
};

var enterAntiClockwise = {
  startAngle: Math.PI * 2,
  endAngle: Math.PI * 2
};

var x = d3.scale.linear().range([0, 2 * Math.PI]);

var TEXT_HEIGHT_ALLOWANCE = 0.1;

var LABEL_MAX_LENGTH = 10;

var HILITE_SEGMENT_COLOUR = "blue";
var HILITE_TEXT_COLOUR = "white";
var UNHILITE_SEGMENT_COLOUR = "white";
var UNHILITE_TEXT_COLOUR = "";
var HILITE_SEGMENT_WIDTH = "2";
var UNHILITE_SEGMENT_WIDTH = "1";
var UNHILITE_CELL_COLOUR = "";

//---- Popup on mouseover for sectors and table rows.

var toolTip = d3.select("body")
      .append("div")
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden")
      .text("a simple tooltip");

//---- Chart area on web page.

// A div with id="plot-area" is located on the web page
// and then populated with these chart elements.

var plotGroup = d3.select("#plot-area").append("svg")
      .attr("width", WIDTH)
      .attr("height", HEIGHT)
      .append("g")
      .attr("transform", "translate(" + WIDTH / 2 + "," + HEIGHT / 2 + ")");

//---- Define the plot layout and plotting algorithm - a pie chart.

var pie = d3.layout.pie()
      .startAngle(-Math.PI / 2)
      .endAngle(2 * Math.PI - Math.PI / 2)
      .value(function(d) { return d.value; });

var arc = d3.svg.arc()
      .innerRadius(INNER_RADIUS)
      .outerRadius(OUTER_RADIUS);

// Pie slices showing sub-totals.
// Set the start and end angles to 0 so we can transition
// clockwise to the actual values later.
var slices = plotGroup.selectAll("g.slice")
      .data(pie([]))
      .enter()
      .append('g')
      .attr('class', 'slice');

slices.transition()   // update
  .duration(DURATION)
  .attrTween("d", arcTween);

var zoomOutButton = plotGroup.append("g")
      .on("click", zoomOut)
      .datum({}); // Avoid "undefined" error on clicking.
zoomOutButton.append("circle")
  .attr("id", "inner-circle")
  .attr("r", INNER_RADIUS)
  .style("fill", "white");
zoomOutButton.append("text")
  .attr("class", "click-message")
  .attr("text-anchor", "middle")
  .attr("dy", "0.3em")
  .text(ZOOM_OUT_MESSAGE);

// Text for showing totals.
var statisticsArea = d3.select("#statistics-area");
var totalText = statisticsArea.append("text")
      .attr("class", "total")
      .attr("dy", ".40em")
      .style("text-anchor", "middle");

function zoomIn(data) {
  if (breadcrumbs.isForCodeLevel()) {
    var forCode = data.target;
    var route = breadcrumbs.routeIn(forCode);
    var resource = {};
    var dataset = processResponse(route, resource);
    colourPalette.push(data.colourIndex, dataset.length);
    visualise(dataset, resource.total);
    var isCoreQuota = selectedCoreQuota();
    tabulateAllocations(table, dataset, resource.total, isCoreQuota);
  } else {
    // Instead of zooming the plot, navigate to another page.
    window.location.href = '/allocations/applications/' +
      data.id + '/approved';
  }
}

function zoomInPie(p, i) {
  var data = p.data;
  var segment = null;
  if (this.nodeName == "text") {
    segment = d3.select("#segment-" + i);
  } else {
    segment = d3.select(this);
  }
  _hideRelatedLabels(segment, data);
  zoomIn(data);
}

function zoomOut(p) {
  if (!breadcrumbs.isHome()) {
    var route = breadcrumbs.routeOut();
    var resource = {};
    var dataset = processResponse(route, resource);
    colourPalette.pop();
    // Display pie chart and table.
    visualise(dataset, resource.total);
    var isCoreQuota = selectedCoreQuota();
    tabulateAllocations(table, dataset, resource.total, isCoreQuota);
  }
}

function isCramped(d) {
  return d.endAngle - d.startAngle > TEXT_HEIGHT_ALLOWANCE;
}

function calculateOpacity(d) {
  return isCramped(d) ? 1.0 : 0.1 ;
}

function calculateOpacity0(d) {
  return isCramped(d) ? 1.0 : 0.0 ;
}

function showRelatedLabels(d, i) {
  var segment = null;
  if (this.nodeName == "text") {
    segment = d3.select("#segment-" + i);
  } else {
    segment = d3.select(this);
  }
  segment
    .style("stroke", HILITE_SEGMENT_COLOUR)
    .style("stroke-width", HILITE_SEGMENT_WIDTH);
  var bisectorAngle = (d.endAngle + d.startAngle) / 2.0 + -Math.PI / 2;
  var deltaX = 5 * Math.cos(bisectorAngle);
  var deltaY = 5 * Math.sin(bisectorAngle);
  segment.attr("transform", "translate(" + deltaX + "," + deltaY + ")");
  table.selectAll("td.col0").each(function(row) {
    if (row.colourIndex == d.data.colourIndex) {
      var otherColumns = $(this).siblings();
      otherColumns.css('background-color', HILITE_SEGMENT_COLOUR);
      otherColumns.css('color', HILITE_TEXT_COLOUR);
    }
  });
  if (breadcrumbs.isForCodeLevel()) {
    showFORDescription(d);
  } else {
    showProjectSummary(d.data);
  }
  toolTip.style("visibility", "visible");
}

function moveRelatedLabels(d, i) {
  var top = (d3.event.pageY - 10) + "px";
  var left = (d3.event.pageX + 10) + "px";
  toolTip.style("top", top).style("left", left);
}

function _hideRelatedLabels(segment, data) {
  segment
    .style("stroke", UNHILITE_SEGMENT_COLOUR)
    .style("stroke-width", UNHILITE_SEGMENT_WIDTH)
    .attr("transform", "translate(0, 0)");
  table.selectAll("td.col0").each(function(row) {
    if (row.colourIndex == data.colourIndex) {
      $(this).siblings().css('background-color', UNHILITE_CELL_COLOUR);
      $(this).siblings().css('color', UNHILITE_TEXT_COLOUR);
    }
  });
  toolTip.style("visibility", "hidden");
}

function hideRelatedLabels(d, i) {
  var segment = null;
  if (this.nodeName == "text") {
    segment = d3.select("#segment-" + i);
  } else {
    segment = d3.select(this);
  }
  _hideRelatedLabels(segment, d.data);
}

//---- Popup showing project summary.

var projectMarkup = "<div class='details-container centred-container'>" +
      "<table class='table-striped table-condensed'>" +
      "<tr><th>Project: </th><td>{{projectName}}</td></tr>" +
      "<tr><th>Institution: </th><td>{{institutionName}}</td></tr>" +
      "<tr><th>Core quota: </th><td>{{coreQuota}}</td></tr>" +
      "<tr><th>Instance quota: </th><td>{{instanceQuota}}</td></tr>" +
      "</table>" +
      "</div>";

Mustache.parse(projectMarkup);

function showProjectSummary(data) {
  var view = {
    projectName: data.projectName.makeWrappable(),
    institutionName: data.institutionName,
    coreQuota: data.coreQuota.toFixed(0),
    instanceQuota: data.instanceQuota.toFixed(0)
  };
  var rendered = Mustache.render(projectMarkup, view);
  toolTip.html(rendered);
}


//---- Popup showing full field-of-research name.
var forMarkup = "<div class='details-container centred-container'>" +
      "<table class='table-condensed'>" +
      "<tr>" +
      "<th>{{forCode}}:&nbsp;</th>" +
      "<td style='text-transform: capitalize;'>{{forName}}</td>" +
      "</tr>" +
      "</table>" +
      "</div>";

function showFORDescription(d) {
  var forCode = d.data.target;
  var view = {
    forCode: forCode,
    forName: forTitleMap[forCode].toLowerCase()
  };
  var rendered = Mustache.render(forMarkup, view);
  toolTip.html(rendered);
}

//----- Visualise Data

function visualise( dataset, totalResource ) {

  var countLabelPrefix = selectedCoreQuota() ? "Core count: "
      : "Instance count: ";
  totalText.text(function(d) {
    return countLabelPrefix + totalResource.toFixed(0); });

  // Build the node list, attaching the new data.
  var nodes = pie(dataset);

  slices = plotGroup.selectAll("g.slice").data(nodes);

  slices.select('path')
    .attr("fill", function (d, i) {
      return colourPalette.getColour(d.data.colourIndex);
    })
    .transition()
    .duration(DURATION)
    .attrTween("d", arcTween);

  // Display new data items:

  // -- slices first.

  var newSlices = slices.enter()
        .append('g')
        .attr('class', 'slice');

  newSlices.append("path")
    .attr("class", 'plot-slice')
    .attr("id", function(d, i) { return 'segment-' + i; })
    .attr("fill", function (d, i) {
      return colourPalette.getColour(d.data.colourIndex);
    })
    .style('stroke', UNHILITE_SEGMENT_COLOUR)
    .style('stroke-width', UNHILITE_SEGMENT_WIDTH)
    .attr('d', arc(enterClockwise))
    .each(function (d) {
      this._current = {
        data: d.data,
        value: d.value,
        startAngle: enterAntiClockwise.startAngle,
        endAngle: enterAntiClockwise.endAngle
      };
    })
    .on("click", zoomInPie)
    .on("mouseover", showRelatedLabels)
    .on("mousemove", moveRelatedLabels)
    .on("mouseout", hideRelatedLabels)
    .transition()
    .duration(DURATION)
    .attrTween("d", arcTween)
  ;


  // Begin text annotation.
  slices.selectAll('text').remove();

  // Annotate slices with virtual CPU count for corresponding domain.
  slices
    .append("text")
    .attr("dy", ".35em")
    .attr("text-anchor", "middle")
    .attr("transform", function(d) {
      d.outerRadius = OUTER_RADIUS;
      d.innerRadius = OUTER_RADIUS/2;
      return "translate(" + arc.centroid(d) + ")rotate(" + angle(d) + ")";
    })
    .style("fill", "White")
    .style("font", "bold 12px Arial")
    .text(function(d) {
      var label = null;
      if (breadcrumbs.isForCodeLevel()) {
        var forCode = d.data.target;
        label = forCode;
      } else {
        label = d.data.target.abbreviate(LABEL_MAX_LENGTH + 5);
      }
      return label;
    })
    .style("opacity", 0)
    .on("click", zoomInPie)
    .on("mouseover", showRelatedLabels)
    .on("mousemove", moveRelatedLabels)
    .on("mouseout", hideRelatedLabels)
    .transition()
    .duration(DURATION_FAST)
    .style("opacity", calculateOpacity0);

  // -- Text annotations third, virtual CPU count for corresponding domain.

  newSlices
    .append("text")
    .attr("id", function(d, i) { return 'value-plot-label-' + i; })
    .attr("class", 'value-plot-label')
    .attr("dy", ".35em")
    .attr("text-anchor", "middle")
    .attr("transform", function(d) {
      d.outerRadius = OUTER_RADIUS;
      d.innerRadius = OUTER_RADIUS/2;
      return "translate(" + arc.centroid(d) + ")rotate(" + angle(d) + ")";
    })
    .style("fill", "White")
    .style("font", "bold 12px Arial")
    .text(function(d) {
      var label = null;
      if (breadcrumbs.isForCodeLevel()) {
        var forCode = d.data.target;
        label = forCode;
      } else {
        label = d.data.target.abbreviate(LABEL_MAX_LENGTH + 5);
      }
      return label;
    })
    .style("opacity", 0)
    .on("click", zoomInPie)
    .on("mouseover", showRelatedLabels)
    .on("mousemove", moveRelatedLabels)
    .on("mouseout", hideRelatedLabels)
    .transition()
    .duration(DURATION_FAST)
    .style("opacity", calculateOpacity0)
  ;

  // Remove old elements:

  // -- remove old annotations
  slices.exit().select('text')
    .transition()
    .duration(DURATION_FAST)
    .style("opacity", 0)
    .remove();

  // -- remove old slices
  slices.exit().select('fill')
    .transition()
    .duration(DURATION)
    .attrTween('d', arcTweenOut)
    .remove();
  slices.exit().transition().remove();

  //----- Build and display breadcrumbs

  breadcrumbs.navigate(function(route, i) {
      // Restore original palette.
      colourPalette.popToLevel(i + 1);
      refreshPlotAndTable(route);
  });
}

//---- Plotting and Animation Utilities

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
  var i = d3.interpolate(
      this._current,
      {startAngle: Math.PI * 2, endAngle: Math.PI * 2, value: 0});
  this._current = i(0);
  return function (t) {
    return arc(i(t));
  };
}

//---- Main Function: Process the data and visualise it.

function selectedCoreQuota() {
  var activeButton = $('button#cores.active').text();
  var isCoreQuota = activeButton == "Cores";
  return isCoreQuota;
}

function processResponse(route, resource) {
  var isCoreQuota = selectedCoreQuota();
  var dataset = allocations.dataset(route, isCoreQuota);
  var sum = d3.sum(dataset, function (d) {
    return d.value;
  });
  resource.total = sum;
  return dataset;
}

function refreshPlotAndTable(route) {
  var resource = {};
  var dataset = processResponse(route, resource);
  visualise(dataset, resource.total);
  var isCoreQuota = selectedCoreQuota();
  tabulateAllocations(table, dataset, resource.total, isCoreQuota);
}

function populatePalette(route) {
  colourPalette.reset();
  if (route.length > 0) {
    var isCoreQuota = selectedCoreQuota();
    var reversedPath = [];
    var forPath = route.concat();
    var partialPath = [];
    var levelCount = route.length;
    for(var levelIndex = 0; levelIndex < levelCount; levelIndex++) {
      var forCode = forPath.pop();
      var dataset = allocations.dataset(partialPath, isCoreQuota);
      var dataCount = dataset.length;
      var foundColourIndex = -1;
      for (var dataIndex = 0; dataIndex < dataCount; dataIndex++) {
        var data = dataset[dataIndex];
        if (data.target == forCode) {
          foundColourIndex = dataIndex;
          break;
         }
      }
      colourPalette.push(foundColourIndex, dataCount);
      reversedPath.push(forCode);
      partialPath = reversedPath.concat().reverse();
    }
  }
}

//---- Data Loading.

function load() {
  d3.json("/allocations/rest/for_codes", function(error, forObjects) {
    d3.json(
        "/allocations/rest/applications/approved/tree",
        function(error, allocationObjects) {
        forTitleMap = forObjects;
        allocations = new Allocations(allocationObjects.children);
        var route = null;
        var pathExtension = window.location.hash;
        if (pathExtension) {
          route = allocations.parseForPath(pathExtension);
          breadcrumbs.setRoute(route);
          populatePalette(route);
        }
        refreshPlotAndTable(route);
    });
  });
}

load();

//---- Additional User Interactions.

function change() {
  $('#graph-buttons button').removeClass('active');
  $(this).addClass('active');
  refreshPlotAndTable(breadcrumbs.route());
}

d3.selectAll("button").on("click", change);

$(document).ready(function(){
    $("#plot-area")
        .affix({
            offset: {
                top: function () {
                    return $("#plot-area").parent().offset().top;
                }
            }
        })
        .on('affix.bs.affix affix-top.bs.affix affix-bottom.bs.affix',
            function(evt){
                if ($("#table-area").height() < $("#plot-area").height()){
                    evt.preventDefault();
                    $("#plot-area").removeClass("affix affix-top affix-bottom");
                }
            });
});
