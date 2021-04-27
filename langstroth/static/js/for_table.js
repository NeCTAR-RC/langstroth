/* -*- Mode: js; tab-width: 2; indent-tabs-mode: nil; js-indent-level: 2; -*- */
////// FOR Table for NeCTAR Allocations

// Dependent on breadcrumbs object created in allocations_pi.js

//==== FOR/Project Table

var forHeadings = {
  "caption" : "Fields Of Research",
  "code" : "Code",
  "name" : "Name",
  "percent" : "%",
  "count" : "Count"
};

var projectHeadings = {
  "caption" : "Projects",
  "code" : "Project",
  "name" : "Institution",
  "percent" : "%",
  "count" : "Count"
};

//==== HTML Table For Allocations for FOR Codes.
// Populated on page load. Dynamic update after page load is not supported.

// Get either black or white text to contrast against a given colour
function getTextColour(colour) {
  var dark = d3.lab(colour).l < 70;
  return dark ? "#fff" : "#000";
}

function inflateChartSegment(d, i) {
  var segment = d3.selectAll("path").filter(function(row) {
    return (row.data.colourIndex == d.colourIndex);
  });
  segment.style("stroke", HILITE_SEGMENT_COLOUR)
    .style("stroke-width", HILITE_SEGMENT_WIDTH)
    .attr("transform", function(row) {
      var bisectorAngle =
        (row.endAngle + row.startAngle) / 2.0 + -Math.PI / 2;
      var deltaX = 5 * Math.cos(bisectorAngle);
      var deltaY = 5 * Math.sin(bisectorAngle);
      return "translate(" + deltaX + "," + deltaY + ")";
    });

  if (breadcrumbs.isForCodeLevel()) {
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
  var tableClass = "for-projects table-striped table-bordered " +
    "table-condensed table-hover";
  var table = d3.select(pageAreaSelector).append("table")
        .attr("class", tableClass);
  var thead = table.append("thead");
  table.append("tbody");

  // The row headers
  var headerRow = thead.append("tr");
  headerRow.append("th")
    .attr("class", "col0")
    .style("min-width", "20px")
    .text(forHeadings.code);
  headerRow.append("th")
    .attr("class", "col1")
    .style("min-width", "20px")
    .text(forHeadings.name);
  headerRow.append("th")
    .attr("class", "col2")
    .style("min-width", "20px")
    .text(forHeadings.percent);
  headerRow.append("th")
    .attr("class", "col3")
    .style("min-width", "20px")
    .text(isCoreQuota ? "Cores" : "Instances");

  return table;
}

function tabulateAllocations(table, dataset, total, isCoreQuota) {

  var thead = table.select("thead");

  thead.select("th.col0")
    .text(function(row) {
      return breadcrumbs.isForCodeLevel() ? forHeadings.code
          : projectHeadings.code;
    });

  thead.select("th.col1")
    .text(function(row) {
      return breadcrumbs.isForCodeLevel() ? forHeadings.name
          : projectHeadings.name;
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
      return colourPalette.getColour(d.colourIndex);
    })
    .style("color", function (d, i) {
      var colour =  colourPalette.getColour(d.colourIndex);
      return getTextColour(colour);
    })
    .text(function(row) {
      return breadcrumbs.isForCodeLevel() ? row.target
          : row.projectDescription.makeWrappable();
    });

  rows.select("td.col1")
    .style("text-transform", breadcrumbs.isForCodeLevel()
        ? "capitalize" : "")
    .text(function(row) {
      if (breadcrumbs.isForCodeLevel()) {
        var forCode = row.target;
        return forTitleMap[forCode].toLowerCase();
      } else {
        return row.institutionName;
      }
    });

  rows.select("td.col2")
    .text(function(row) {
      var percent = row.value * 100.00 / total;
      return percent.toFixed(0);
    });

  rows.select("td.col3")
    .text(function(row) {
      // Round up.
      var value = row.value;
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
      return colourPalette.getColour(d.colourIndex);
    })
    .style("color", function (d, i) {
      var colour =  colourPalette.getColour(d.colourIndex);
      return getTextColour(colour);
    })
    .text(function(row) {
      return breadcrumbs.isForCodeLevel() ? row.target
          : row.projectDescription.makeWrappable() ;
    });

  newRows.append("td")
    .attr("class", "col1")
    .style("min-width", "20px")
    .style("text-align", "left")
    .style("text-transform", breadcrumbs.isForCodeLevel()
        ? "capitalize" : "")
    .text(function(row) {
      if (breadcrumbs.isForCodeLevel()) {
        var forCode = row.target;
        return forTitleMap[forCode].toLowerCase();
      } else {
        return row.institutionName;
      }
    });

  newRows.append("td")
    .attr("class", "col2")
    .style("min-width", "20px")
    .style("text-align", "right")
    .text(function(row) {
      var percent = row.value * 100.00 / total;
      return percent.toFixed(0);
    });

  newRows.append("td")
    .attr("class", "col3")
    .style("min-width", "20px")
    .style("text-align", "right")
    .text(function(row) {
      // Round up.
      var value = row.value;
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
}

var table = buildTable("#table-area");
