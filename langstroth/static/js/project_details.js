////// Project Details Page for NeCTAR Allocations

// Depends on code in breadcrumbs.js
var breadcrumbs = new Breadcrumbs();
var allocations = new Allocations();

var forTitleMap = {};

//==== Details Table

var headings = {
  "start_date" : "Start date",
  "end_date" : "End date",
  "for_distribution" : "FOR distribution",
  "submit_date" : "Submit date",
  "modified_time" : "Modified time"
};

var toolTip = d3.select("body")
      .append("div")
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden")
      .style("background-color", "rgba(255,255,255,0.75)")
      .style("padding", "2px 4px 2px 4px")
      .style("border-radius", "3px")
      .text("a simple tooltip");


//==== HTML Table For Project Details.
// Populated on page load. Dynamic update after page load is not supported.

function tabulateSummary(pageAreaSelector, projectSummary, forTranslation) {

  // Define the table with heading.
  var table = d3.select(pageAreaSelector).append("table")
        .attr("class", "table table-striped table-bordered table-condensed");
  tbody = table.append("tbody");

  // Add rows with rows (tr), row headings (th) and the detail entries (td).
  var rows = tbody.selectAll("tr")
        .data(function(row) {
          var keys = [];
          for (var key in headings) {
            keys.push(key);
          }
          return keys; })
        .enter()
        .append("tr");

  rows.append("th")
    .style("max-width", "170px")
    .style("min-width", "130px")
    .style("width", "130px")
    .text(function(row) {
      return headings[row];
    });

  rows.append("td")
    .html(function(row) {
      if (row == "for_distribution") {
        var forDistributionTable = "";
        if (projectSummary.field_of_research_1) {
          var for1 = projectSummary.field_of_research_1;
          forDistributionTable += "<div>" +
            "<span style='min-width: 20em'>" + forTranslation[for1] + "&nbsp;(" + for1 + ")&nbsp;</span>" +
            "<span style='max-width: 4em'>" + projectSummary.for_percentage_1 + "&nbsp;%&nbsp;</span>" +
            "</div>";
        }
        if (projectSummary.field_of_research_2) {
          var for2 = projectSummary.field_of_research_2;
          forDistributionTable += "<div>" +
            "<span style='min-width: 20em'>" + forTranslation[for2] + "&nbsp;(" + for2 + ")&nbsp;</span>" +
            "<span style='max-width: 4em'>" + projectSummary.for_percentage_2 + "&nbsp;%&nbsp;</span>" +
            "</div>";
        }
        if (projectSummary.field_of_research_3) {
          var for3 = projectSummary.field_of_research_3;
          forDistributionTable += "<div>" +
            "<span style='min-width: 20em'>" + forTranslation[for3] + "&nbsp;(" + for3 + ")&nbsp;</span>" +
            "<span style='max-width: 4em'>" + projectSummary.for_percentage_3 + "&nbsp;%&nbsp;</span>" +
            "</div>";
        }
        return forDistributionTable;
      }
      return projectSummary[row];
    });
}

function tabulateQuotas(pageAreaSelector, projectSummary) {
  // Define the table with heading.
  var table = d3.select(pageAreaSelector).append("table")
        .attr("class", "table table-striped table-bordered table-condensed");
  tbody = table.append("tbody");

  var quotas = projectSummary.quotas;

  // create a row for each object in the data
  var rows = tbody.selectAll('tr')
    .data(quotas)
    .enter()
    .append('tr');

  rows.append("th")
    .style("max-width", "270px")
    .style("min-width", "230px")
    .style("width", "130px")
    .text(function(row) {
      label = row.resource + " (" + row.zone + ")";
      return label;
  });

  rows.append("td")
    .text(function(row) {
      return row.quota;
  });
}

//==== Pie Chart for Quotas.

// Pie chart constants.

var PIE_CHART_WIDTH = 92;
var PIE_CHART_HEIGHT = 92;
var PIE_CHART_RADIUS = Math.min(PIE_CHART_WIDTH, PIE_CHART_HEIGHT) / 2;
var PIE_CHART_INNER_RADIUS = PIE_CHART_RADIUS*0.0;

function graphQuota(pageAreaSelector, quotaKey, usage) {

  var color = d3.scale.ordinal()
  // Color for used quota then unused quota.
        .domain("0", "1")
        .range(["#006ccf", "#f2f2f2"]);

  var pie = d3.layout.pie();

  var arc = d3.svg.arc()
        .outerRadius(PIE_CHART_RADIUS)
        .innerRadius(PIE_CHART_INNER_RADIUS)
        .startAngle(function(d) { return 2*Math.PI - d.startAngle; })
        .endAngle(function(d) { return 2*Math.PI - d.endAngle; });

  var svg = d3.select(pageAreaSelector).append("svg")
        .attr("width", PIE_CHART_WIDTH)
        .attr("height", PIE_CHART_HEIGHT)
        .append("g")
        .attr("transform", "translate(" + PIE_CHART_WIDTH / 2 + "," + PIE_CHART_HEIGHT / 2 + ")");

  var g = svg.selectAll(".arc")
        .data(pie(usage))
        .enter().append("g")
        .attr("class", "arc");

  g.append("path")
    .attr("d", arc)
    .style("fill", function(d, i) {
      return color(i);
    });
}

//==== Project Allocation: Assembling the Pieces.
// Table and 2 pie charts.

function getQuota(projectSummary, resource) {
  for (var q in projectSummary.quotas) {
    quota = projectSummary.quotas[q];
    if (quota.resource == "compute.instances") {
      return quota.quota;
    } else {
      return "Unknown";
    }
  }
}

function projectDetails() {
  var suffix = forcodeSeries == "" ? "" : "-" + forcodeSeries;
  d3.json(
    allocationURL + "/for-codes" + suffix + "/",
    function(error, forTranslation) {
      d3.json(allocationURL + "/allocations/" + allocationId + "/",
        function(error, projectSummary) {
          tabulateSummary("#project-summary", projectSummary, forTranslation);
          tabulateQuotas("#project-quota", projectSummary);
          /*
            forTitleMap = forTranslation;
            var pathExtension = window.location.hash;
            if (pathExtension) {
              var route = allocations.parseForPath(pathExtension);
              route.unshift(projectDescription);
              breadcrumbs.setRoute(route);
              breadcrumbs.navigate(function(route, i) {
                var urlExtension = "";
                if (route.length > 0) {
                    var forCode = route[0];
                    var padding = ZERO_PADDING[i - forCode.length / 2];
                    urlExtension = '#/FOR/' + forCode + padding;
                }
                var destinationUrl = '/allocations/applications/approved/visualisation' + urlExtension;
                window.location.href = destinationUrl;
              });
          }
          */
      });
  });
}

projectDetails();
