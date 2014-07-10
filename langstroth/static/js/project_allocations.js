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
	"modified_time" : "Modified time"
};


function projectDetails(elementId) {
	d3.json("/allocations/" + allocationId + "/project_summary", function(error, allocations) {
		var allocation = null;
		var allocationCount = allocations.length
		for (var allocationIndex = 0; allocationIndex < allocationCount; allocationIndex++) {			
			allocation = allocations[allocationIndex];
			
			var table = d3.select(elementId)
							.append("table")
							.attr("class", "details-table");
			
			var caption = table.append("caption")
							.text("Allocation: " + allocationIndex); 
			var thead = table.append("thead"); // Not used.			
			var tbody = table.append("tbody")
			
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
					return allocation[row]; 
				});
		}
	});
}

projectDetails("#project-details");
