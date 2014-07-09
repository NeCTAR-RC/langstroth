////// Project Details Page for NeCTAR Allocations

//==== Details Table

var projectId = document.URL;

function projectInfo(to) {
	d3.text("projectJSON.php?d=projectInfo&id=<?= $projectID ?>", "text/plain", function(error, data) {
		d3.select(to).html(data);
	});
}
