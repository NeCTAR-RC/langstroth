////// Project Details Page for NeCTAR Allocations

//==== Details Table

var headings = {
	"project_name" : "Project name",
	"start_date" : "Start date",
	"end_date" : "End date",
	"use_case" : " Use case",
	"usage_patterns" : "Usage patterns",
	"instance_quota" : "Instance quota",
	"core_quota" : "Core quota",
	"submit_date" : "Submit date",
	"modified_time" : "Last modified time"
};

var toolTip = d3.select("body")
				.append("div")
				.style("position", "absolute")
				.style("z-index", "10")
				.style("visibility", "hidden")
				.style("background-color", "#bbbbbb")
				.style("color", "yellow")
				.style("padding", "2px 4px 2px 4px")
				.style("border-radius", "3px")
				.text("a simple tooltip");


//==== HTML Table For Project Details.
// Popluated on page load. Dynamic update afger page load is not supported.

function tabulateSummary(pageAreaSelector, project_summary) {

	// Define the table with heading.
	var table = d3.select(pageAreaSelector).append("table")
					.attr("class", "details-table");	
	table.append("caption").text("Aggregate Allocation"); 
	tbody = table.append("tbody"); 

	// Add rows with rows (tr), row headings (th) and the detail entries (td).
	var rows = tbody.selectAll("tr")
					.data(function(row) { 
						var keys = [];
						for (key in headings) {
							keys.push(key);
						} 
						return keys; })
					.enter()
					.append("tr");
	
	rows.append("th")
		.text(function(row) { 
				return headings[row]; 
			});
	
	rows.append("td")
		.text(function(row) { 
			return project_summary[row]; 
		});
}

//==== Pie Chart for Instance and Core Quota.

// Pie chart constants.

var PIE_CHART_WIDTH = 100;
var PIE_CHART_HEIGHT = 100;
var PIE_CHART_RADIUS = Math.min(PIE_CHART_WIDTH, PIE_CHART_HEIGHT) / 2;

function graphQuota(pageAreaSelector, quotaKey, usage) {
		
	var color = d3.scale.ordinal()
				// Color for used quota then unused quota.
			    .range(["#5687d1", "#dddddd"]);

	var pie = d3.layout.pie()
				.value(function(d) { 
						return d; 
				});

	var arc = d3.svg.arc()
				.outerRadius(PIE_CHART_RADIUS)
				.innerRadius(PIE_CHART_RADIUS*0.5)
				.startAngle(function(d) { return 2*Math.PI - d.startAngle; })
				.endAngle(function(d) { return 2*Math.PI - d.endAngle; });

	var svg = d3.select(pageAreaSelector).append("svg")
				.attr("PIE_CHART_WIDTH", PIE_CHART_WIDTH)
				.attr("PIE_CHART_HEIGHT", PIE_CHART_HEIGHT)
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

	g.append("text")
				.attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
				.attr("dy", ".35em")
				.style("text-anchor", "middle")
				.text(function(d) { 
					var usageQuota = (usage[0] + usage[1]) + "";
					return d.data == "0" ? "" : d.data + "/" + usageQuota; 
				});
}

//==== Pie Chart to show Field of Research Partitioning for Project.

function graphFieldOfResearch(pageAreaSelector, forUsage, forTranslation) {

	var color = d3.scale.ordinal()
				// for first, second and third FOR's.
				.range(["#ff0000", "#00ff00", "#0000ff"]);

	var pie = d3.layout.pie()
				.value(function(d) { 
					return d.percent; 
				});

	var arc = d3.svg.arc()
				.outerRadius(PIE_CHART_RADIUS)
			    .innerRadius(PIE_CHART_RADIUS*0.5)
			    .startAngle(function(d) { return 2*Math.PI - d.startAngle; })
			    .endAngle(function(d) { return 2*Math.PI - d.endAngle; });

	var svg = d3.select(pageAreaSelector).append("svg")
				.attr("PIE_CHART_WIDTH", PIE_CHART_WIDTH)
				.attr("PIE_CHART_HEIGHT", PIE_CHART_HEIGHT)
				.append("g")
				.attr("transform", "translate(" + PIE_CHART_WIDTH / 2 + "," + PIE_CHART_HEIGHT / 2 + ")");

	var path = svg.datum(forUsage).selectAll("path")
				.data(pie)
				.enter().append("path")
				.attr("fill", function(d, i) { return color(i); })
				.attr("d", arc)
				.each(function(d) { 
					this._current = d; 
				}); // store the initial angles

	var g = svg.selectAll(".arc")
				.data(pie(forUsage))
				.enter().append("g")
				.attr("class", "arc");

	var text = g.append("text")
				.attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
				.attr("dy", ".35em")
				.style("text-anchor", "middle")
				.on("mouseover", showRelatedLabels)
				.on("mousemove", moveRelatedLabels)
				.on("mouseout", hideRelatedLabels)
				.text(function(d) { 
					return d.data.code; 
				});

	//---- Popup showing details.
		
	function showFor(d) {
		var markup = "<div class='for-container'>" 
					+ forTranslation[d.data.code]
					+ "</div>";
		toolTip.html(markup);
	}

	function showRelatedLabels(d, i) { 
		showFor(d);
		toolTip.style("visibility", "visible");
	}

	function moveRelatedLabels(d, i) { 
		var top = (d3.event.pageY - 10) + "px";
		var left = (d3.event.pageX + 10) + "px";
		toolTip.style("top", top).style("left", left);
	}

	function hideRelatedLabels(d, i) { 
		toolTip.style("visibility", "hidden");
	}
}

//==== Project Allocation: Assembling the Pieces.
// Table and 3 pie charts.

function projectDetails() {
	d3.json("/nacc/rest/for_codes", function(error, forTranslation) {
		d3.json("/nacc/rest/allocations/" + allocationId + "/project/summary", function(error, project_summary) {
			tabulateSummary("#project-summary", project_summary);
			var forUsage = [
                {'code': project_summary.field_of_research_1, 'percent': project_summary.for_percentage_1}, 
                {'code': project_summary.field_of_research_2, 'percent': project_summary.for_percentage_2}, 
                {'code': project_summary.field_of_research_3, 'percent': project_summary.for_percentage_3}];
			graphFieldOfResearch("#research-pie-chart", forUsage, forTranslation);
			var coreUsage = [project_summary.cores, project_summary.core_quota - project_summary.cores];
			graphQuota("#core-pie-chart","cores", coreUsage);
			instanceUsage = [project_summary.instances, project_summary.instance_quota - project_summary.instances];
			graphQuota("#instance-pie-chart","instances", instanceUsage);
		});
	});
}

projectDetails();
