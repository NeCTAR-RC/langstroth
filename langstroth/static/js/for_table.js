////// FOR Table for NeCTAR Allocations

//==== FOR/Project Table

var forHeadings = {
	"caption" : "Fields Of Research",
	"code" : "Code",
	"name" : "Name",
	"percent" : "%",
	"count" : "Count",
};

var projectHeadings = {
	"caption" : "Projects",
	"code" : "Project",
	"name" : "Institution",
	"percent" : "%",
	"count" : "Count",
};

//==== HTML Table For Allocations for FOR Codes.
// Populated on page load. Dynamic update after page load is not supported.

function inflateChartSegment(d, i) { 
    var segment = d3.selectAll("path").filter(function(row) { 
			return (row.data.colourIndex == d.colourIndex);
    	});
		segment.style("stroke", HILITE_SEGMENT_COLOUR)
		.style("stroke-width", HILITE_SEGMENT_WIDTH)
		.attr("transform", function(row) {
		    var bisectorAngle = (row.endAngle + row.startAngle) / 2.0 + -Math.PI / 2;
		    var deltaX = 5 * Math.cos(bisectorAngle);
		    var deltaY = 5 * Math.sin(bisectorAngle);
			return "translate(" + deltaX + "," + deltaY + ")";
		});
		
		if (isForCodeLevel()) {
			// Do nothing
		} else {
			showProjectSummary(d);
			toolTip.style("visibility", "visible");
		}
}

function deflateChartSegment(d) { 
    var segment = d3.selectAll("path").filter(function(row) { 
		return (row.data.colourIndex == d.colourIndex);
	});
	segment.style("stroke", UNHILITE_SEGMENT_COLOUR)
		.style("stroke-width", UNHILITE_SEGMENT_WIDTH)
		.attr("transform", "translate(0, 0)");
	
	toolTip.style("visibility", "hidden");
}

function zoomInTable(d) {
	deflateChartSegment(d);
	zoomIn(d);
 }

function buildTable(pageAreaSelector, isCoreQuota) {
	// Define the table with heading.
	var table = d3.select(pageAreaSelector).append("table")
					.attr("class", "for-projects table-striped table-bordered table-condensed table-hover");	
	var caption = table.append("caption").text(forHeadings["caption"]);
	var thead = table.append("thead");
	var tbody = table.append("tbody");
	
	// The row headers
	var headerRow = thead.append("tr");
	headerRow.append("th")
		.attr("class", "col0")
		.style("min-width", "20px")
		.text(forHeadings["code"]);
	headerRow.append("th")
		.attr("class", "col1")
		.style("min-width", "20px")
		.text(forHeadings["name"]);
	headerRow.append("th")
		.attr("class", "col2")
		.style("min-width", "20px")
		.text(forHeadings["percent"]);
	headerRow.append("th")
		.attr("class", "col3")
		.style("min-width", "20px")
		.text(isCoreQuota ? "Cores" : "Instances");
	
	return table;
}

function tabulateAllocations(table, dataset, total, isCoreQuota) {
	
	// Adjust the header
	
	var caption = table.select("caption")
		.text(function(row) { 
			return isForCodeLevel() ? forHeadings["caption"] : projectHeadings["caption"]; 
		});
	
	var thead = table.select("thead");
	
	thead.select("th.col0")
		.text(function(row) { 
				return isForCodeLevel() ? forHeadings["code"] : projectHeadings["code"]; 
			});
	
	thead.select("th.col1")
		.text(function(row) { 
				return isForCodeLevel() ? forHeadings["name"] : projectHeadings["name"]; 
			});
	
	thead.select("th.col2")
		.text(function(row) { 
				return "%"; 
			});
	
	thead.select("th.col3")
		.text(function(row) { 
				return isCoreQuota ? "Cores" : "Instances"; 
			});

	// Attach the data
	
	var tbody = table.select("tbody");
	var rows = tbody.selectAll("tr").data(dataset);

	// Update the existing data records

	rows.select("td.col0")
		.style("background-color", function (d, i) {
				return paletteStack.tos()(d.colourIndex);
		})
		.text(function(row) { 
				return isForCodeLevel() ? row["target"] : row["projectName"].makeWrappable() ; 
			});
	
	rows.select("td.col1")
		.style("text-transform", isForCodeLevel() ? "capitalize" : "")
		.text(function(row) { 
				if (isForCodeLevel()) {
					var forCode = row["target"];
					return forTitleMap[forCode].toLowerCase(); 
				} else {
					return row["institutionName"];
				}
			});
	
	rows.select("td.col2")
		.text(function(row) { 
				var percent = row["value"] * 100.00 / total;
				return percent.toFixed(0); 
			});
	
	rows.select("td.col3")
		.text(function(row) { 
			// Round up.
				var value = row["value"];
				var roundedValue = Math.round(value);
				if ((value - roundedValue) > 0) {
					roundedValue += 1;
				}
				return roundedValue; 
			});		

	// Add new data records

	var newRows = rows.enter()
		.append("tr")
		.attr('data-row',function(d,i){return i; })
		.attr('class', "row-click")
		.on("click", zoomInTable)
		.on("mouseover", inflateChartSegment)
		.on("mousemove", moveRelatedLabels)
		.on("mouseout", deflateChartSegment);

	newRows.append("td")
		.attr("class", "col0")
		.style("min-width", "20px")
		.style("background-color", function (d, i) {
				return paletteStack.tos()(d.colourIndex);
		})
		.style("color", "white")
		.text(function(row) { 
				return isForCodeLevel() ? row["target"] : row["projectName"].makeWrappable() ; 
			});
	
	newRows.append("td")
		.attr("class", "col1")
		.style("min-width", "20px")
		.style("text-align", "left")
		.style("text-transform", isForCodeLevel() ? "capitalize" : "")
		.text(function(row) { 
			if (isForCodeLevel()) {
				var forCode = row["target"];
				return forTitleMap[forCode].toLowerCase(); 
			} else {
				return row["institutionName"];
			}
			});
	
	newRows.append("td")
		.attr("class", "col2")
		.style("min-width", "20px")
		.style("text-align", "right")
		.text(function(row) { 
				var percent = row["value"] * 100.00 / total;
				return percent.toFixed(0); 
			});

	newRows.append("td")
		.attr("class", "col3")
		.style("min-width", "20px")
		.style("text-align", "right")
		.text(function(row) { 
			// Round up.
				var value = row["value"];
				var roundedValue = Math.round(value);
				if ((value - roundedValue) > 0) {
					roundedValue += 1;
				}
				return roundedValue; 
			});		

	// Remove old records.
	
	var oldRows = rows.exit();
	var oldCells = oldRows.selectAll("td");
	oldCells.remove();
	oldRows.remove();
	
	var containerHeight = $("#table-area").height() + RADIUS * 2;
	$("#inner-plot-container, #outer-plot-container").height(containerHeight);
	$(document.body).trigger("sticky_kit:recalc");
}

var table = buildTable("#table-area");



