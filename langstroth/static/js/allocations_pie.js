////// Hierarchical Pie Plot of NeCTAR Allocations

//==== Data manipulation

// Breadcrumbs - keep track of the current hierarchy level.
// Made up of an array of FOR codes.
var breadCrumbs = ['*'];
var colorPalette = d3.scale.category20();
var paletteStack = [colorPalette];
var allocationTree = {};
var forTitleMap = {};


// Is this the level for FOR codes or projects.
function isForCodeLevel() {
	return breadCrumbs.length < 4;
}  

// Recursive code to return allocation tree branch (children) addressed by FOR code.
// The forCode is the FOR2, FOR4 or FOR6 code.
// The allocationObjects is the allocationTree object being passed in.
function traverseHierarchy(route, allocationTree) {
	var children = allocationTree;
	var forCodes = route;
	return nextLevel(forCodes, children);
}

// Recurse the allocation tree to return a branch.
function nextLevel(forCodes, children) {
	var forCode = forCodes.pop();
	if (forCode) {
		var childCount = children.length;
		for (var childIndex = 0; childIndex < childCount; childIndex++) {
			var child = children[childIndex];
			var name = child.name;
			if (name == forCode) {
				return nextLevel(forCodes, child.children);
			} 
		}
	}
	return children;
}

// Restructure allocation tree into a single level array of objects.
// The tree is flattened by taking the sum of all allocations on the branch.
function restructureAllocations(allocationTree, isCoreQuota) {
	var colourIndex = 0;
    var dataset = [];
    var allocationCount = allocationTree.length;
    for (var allocationIndex = 0; allocationIndex < allocationCount; allocationIndex++) {
    	var sum = 0.0;
    	var child = allocationTree[allocationIndex];
    	var name = child.name;
    	var allocationItem = {};
    	if (child.children) {
    		//add the branch value.
			sum = nextLevelSum(child.children, isCoreQuota);
    	} else {
    		// add the leaf value.
			//RR 
    		allocationItem.id = child.id;
			allocationItem.projectName = child.name;
			allocationItem.institutionName = child.institution;
			allocationItem.coreQuota = child.coreQuota;
			allocationItem.instanceQuota = child.instanceQuota;
			allocationItem.useCase = child.useCase.abbreviate(128);			
			allocationItem.usagePattern = child.usagePattern;			
			sum = isCoreQuota ? child.coreQuota : child.instanceQuota;
    	}
    	allocationItem.target = name;
    	allocationItem.value = sum;
    	dataset.push(allocationItem);
    }
	dataset.sort(function(a, b){return b.value - a.value; });
    var recordCount = dataset.length;
    for (var recordIndex = 0; recordIndex < recordCount; recordIndex++) {
    	dataset[recordIndex].colourIndex = colourIndex++;
    }
    return dataset;
}
    
// Recurse the allocation tree to return a sum.
function nextLevelSum(children, isCoreQuota) {
    var sum = 0.0;
	var childCount = children.length;
	for (var childIndex = 0; childIndex < childCount; childIndex++) {
		var child = children[childIndex];
		if (child.children) {
			sum += nextLevelSum(child.children, isCoreQuota);
		} else {
			sum += isCoreQuota ? child.coreQuota : child.instanceQuota;
		}
	}
	return sum;
}


//==== String utilities

// String abbreviate to set length and signify abbreviation by adding ellipsis.
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

// Array return top-of-stack method.
Array.prototype.tos = function() {
	return this[this.length - 1];
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

var x = d3.scale.linear()
      .range([0, 2 * Math.PI]);

var TEXT_HEIGHT_ALLOWANCE = .1;

var LABEL_MAX_LENGTH = 10;

var ROTATION_OFFSET = 0;

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

// TODO RR: remove chart rotation. Failed experiment.
var plotGroup = d3.select("#plot-area").append("svg")
      .attr("width", WIDTH)
      .attr("height", HEIGHT)
      .append("g")
      .attr("transform", "translate(" + WIDTH / 2 + "," + HEIGHT / 2 + ") rotate(" + -ROTATION_OFFSET + ")");

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

slices.transition()  // update
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
	.attr("transform", "rotate(" + ROTATION_OFFSET + ")")
	.text(ZOOM_OUT_MESSAGE);

// Text for showing totals.
var statisticsArea = d3.select("#statistics-area");
var totalText = statisticsArea.append("text")
	.attr("class", "total")
	.attr("dy", ".40em")
	.style("text-anchor", "middle");


	function zoomIn(data) {
		if (isForCodeLevel()) {
			var forCode = data.target;
			breadCrumbs.push(forCode);
			var route = breadCrumbs.slice(1).reverse();
			var children = traverseHierarchy(route, allocationTree);
			var isCoreQuota = selectedCoreQuota();
			var dataset = restructureAllocations(children, isCoreQuota);
			var totalResource = d3.sum(dataset, function (d) {
			  return d.value;
			});
			var currentPalette = paletteStack.tos();
			var currentColour = currentPalette(data.colourIndex);
			var newPalette = d3.scale.linear()
								.domain([0, dataset.length + 10])
								.range([currentColour, "white"]);
			paletteStack.push(newPalette);
			visualise(dataset, totalResource);
			tabulateAllocations(table, dataset, totalResource, isCoreQuota);
		} else {
			// Instead of zooming plot navigate to another page.
			window.location.href = '/nacc/allocations/' + data.id + '/project';
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
	 	if (breadCrumbs.length > 1) {
	 		breadCrumbs.pop();
	 		var route = breadCrumbs.slice(1).reverse(); 		
			var children = traverseHierarchy(route, allocationTree);
			var isCoreQuota = selectedCoreQuota();
			var dataset = restructureAllocations(children, isCoreQuota);
			var totalResource = d3.sum(dataset, function (d) {
			  return d.value;
			});
			// Restore original palette.
			paletteStack.pop();
			// Display pie chart and table.
			visualise(dataset, totalResource);
			tabulateAllocations(table, dataset, totalResource, isCoreQuota);
	 	}
	}
	
	function isCramped(d) { 
		var isCramped = d.endAngle - d.startAngle > TEXT_HEIGHT_ALLOWANCE;
		return isCramped ; 
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
				}; 
			});
		if (isForCodeLevel()) {
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
			}; 
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
		  	
	function showProjectSummary(data) {
	 	var markup = "<div class='details-container centred-container'>" 
 			+ "<table class='table-striped table-condensed'>" 
 			+ "<tr>"
 			+ "<th>"
 			+ "Project: " 
 			+ "</th>"
 			+ "<td>"
 			+ data.projectName.makeWrappable()
 			+ "</td>"
 			+ "</tr>"
 			+ "<th>"
 			+ "Institution: " 
 			+ "</th>"
 			+ "<td>"
 			+ data.institutionName
 			+ "</td>"
 			+ "</tr>"
 			+ "<tr>"
 			+ "<th>"
 			+ "Core quota: " 
 			+ "</th>"
 			+ "<td>"
 			+ data.coreQuota
 			+ "</td>"
 			+ "</tr>"
 			+ "<tr>"
 			+ "<th>"
 			+ "Instance quota: " 
 			+ "</th>"
 			+ "<td>"
 			+ data.instanceQuota
 			+ "</td>"
 			+ "</tr>"
 			+ "<tr>"
 			+ "<th>"
 			+ "Use case: " 
 			+ "</th>"
 			+ "<td>"
 			+ data.useCase 
 			+ "</td>"
 			+ "</tr>"
 			+ "</table>"
 			+ "</div>";
		toolTip.html(markup);
	}

	//---- Popup showing full field-of-reserarch name.
		  	
	function showFORDescription(d) {
		var forCode = d.data.target;
  		var forName = forTitleMap[forCode].toLowerCase();
	 	var markup = "<div class='details-container centred-container'>" 
 			+ "<table class='table-condensed'>" 
 			+ "<tr>"
 			+ "<th>"
 			+ forCode + ":&nbsp;"
 			+ "</th>"
 			+ "<td style='text-transform: capitalize;'>"
 			+  forName     		
 			+ "</td>"
 			+ "</tr>"
 			+ "</table>"
 			+ "</div>";
	 	toolTip.html(markup);
	}

	//----- Visualise Data

function visualise( dataset, totalResource ) {

	var countLabelPrefix = selectedCoreQuota() ? "Core count: " : "Instance count: "; 
    totalText.text(function(d) { return countLabelPrefix + totalResource.toFixed(0); });

	// Build the node list, attaching the new data.
	var nodes = pie(dataset);
	
    slices = plotGroup.selectAll("g.slice").data(nodes);
    
    slices.select('path')
      .attr("fill", function (d, i) {
        return paletteStack.tos()(d.data.colourIndex);
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
        return paletteStack.tos()(d.data.colourIndex);
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
      	if (isForCodeLevel()) {
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
      	if (isForCodeLevel()) {
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

    navigate();
  }

function navigate() {
    var breadcrumb = d3.select("#chart-navigator-1").select('.breadcrumb');
    breadcrumb.selectAll('li').remove();
    breadcrumb.selectAll('li')
      .data(breadCrumbs)
      .enter()
        .append("li")
        .attr("class", function(d, i) { return i == breadCrumbs.length - 1 ? "active" : ""; })
        .html(function(d, i) {
        	var forCode = d;
        	var markup = forCode == '*' 
        		? '<span class="glyphicon glyphicon-home"></span>' 
        		: '<span style="text-transform: capitalize">' 
        			+ forTitleMap[forCode].toLowerCase() 
        			+ '</span>';
        	if (i < breadCrumbs.length - 1) {
        		markup = '<a href="#">' + markup + '</a>';
        	}
			return markup;
        })
        .on("click", function(d, i) {
			if (breadCrumbs.length > 1 && i < breadCrumbs.length - 1) {
				breadCrumbs = breadCrumbs.slice(0, i + 1);
				var route = breadCrumbs.slice(1).reverse(); 		
				var children = traverseHierarchy(route, allocationTree);
				var isCoreQuota = selectedCoreQuota();
				var dataset = restructureAllocations(children, isCoreQuota);
				var totalResource = d3.sum(dataset, function (d) {
				  return d.value;
				});
				// Restore original palette.
				paletteStack = paletteStack.slice(0, i + 1);
				visualise(dataset, totalResource);
				tabulateAllocations(table, dataset, totalResource, isCoreQuota);

			}	
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
  var i = d3.interpolate(this._current, {startAngle: Math.PI * 2, endAngle: Math.PI * 2, value: 0});
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

function processResponse(allocationTree, resource) {
	var isCoreQuota = selectedCoreQuota();
	var dataset = restructureAllocations(allocationTree, isCoreQuota);
	var sum = d3.sum(dataset, function (d) {
      return d.value;
    });
    resource.total = sum;
    return dataset;
}

//---- Data Loading.

function load() {
	d3.json("/nacc/rest/for_codes", function(error, forObjects) {
		d3.json("/nacc/rest/allocation_tree", function(error, allocationObjects) {
			breadCrumbs = ['*'];
			forTitleMap = forObjects;
			allocationTree = allocationObjects.children;
			var isCoreQuota = selectedCoreQuota();
			var resource = {};
			var dataset = processResponse(allocationTree, resource);
			visualise(dataset, resource.total);	
			tabulateAllocations(table, dataset, resource.total, isCoreQuota);
		});
	});
}

load();

//---- Additional User Interactions.

function change() {
	$('#graph-buttons button').removeClass('active');
	$(this).addClass('active');
	var route = breadCrumbs.slice(1).reverse();
	var children = traverseHierarchy(route, allocationTree);
	var isCoreQuota = selectedCoreQuota();
	var resource = {};
	var dataset = processResponse(children, resource);
	visualise(dataset, resource.total);	
	tabulateAllocations(table, dataset, resource.total, isCoreQuota);
}

d3.selectAll("button").on("click", change);

var plotArea = $("#plot-area");
plotArea.stick_in_parent({parent: "#inner-plot-container", inner_scrolling: true, offset_top:0});
