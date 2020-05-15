/* -*- Mode: js; tab-width: 4; indent-tabs-mode: nil; js-indent-level: 4;-*- */

var registrationFrequency = [];
var isCumulative = true;

unixTimestamp = function(timestamp) {
    return new Date(timestamp * 1000);
};

formatData = function(data) {
    return data.map(function(series) {
        series.values = series.datapoints;
        delete series.datapoints;
        series.key = series.target;
        return series;
    });
};

var shortDateFormat = d3.time.format("%Y-%m");
var frequencyFormat = d3.format(',.0f');

// Build area chart

var areaChart = nv.models.stackedAreaChart()
    .margin({right: 100})
    .x(function(d) {
        return new Date(unixTimestamp(d[1]));
    })
    .y(function(d) {
        return d[0];
    })
    .useInteractiveGuideline(true)
    .showTotalInTooltip(true)
    .rightAlignYAxis(true)
    .duration(500)
    .showControls(false)
    .showLegend(false)
    .clipEdge(true);

areaChart.xAxis.tickFormat(function(d) {
    return shortDateFormat(new Date(d)) ;
});

areaChart.xAxis.ticks(d3.time.year);
areaChart.xScale(d3.time.scale());
areaChart.yAxis.tickFormat(frequencyFormat);

// Build histogram chart

var histoChart = nv.models.historicalBarChart()
    .x(function(d, i) {
        return new Date(unixTimestamp(d[1]));
    })
    .y(function(d) {
        return d[0];
    })
    .rightAlignYAxis(true)
    .duration(500);

histoChart.xAxis.tickFormat(function(d) {
    return shortDateFormat(new Date(d)) ;
});
histoChart.xScale(d3.time.scale());
histoChart.yAxis.tickFormat(frequencyFormat);

// Render the chart

var svg = null;

function visualise(trend, chart) {

    // Clean up the internal graph array.
    while(undefined !== nv.graphs && nv.graphs.length > 0) {
        nv.graphs.pop();
    }

    // Freshen dom elements.
    if (svg) {
        svg.remove();
    }
    svg = d3.select("#plot-area").append("svg");

    // Add the chosen graph
    nv.addGraph(function() {
        svg.datum(trend).call(chart);
        nv.utils.windowResize(chart.update);
        return chart;
    });
}

function sumByMonth (values) {
  var byMonth = d3.nest()
    .key(function (d) {
      var date = new Date(unixTimestamp(d[1]));
      return new Date(date.getFullYear(), date.getMonth());
    })
    .rollup(function (a) {
      return d3.sum(a, function (d) { return d[0]; });
    })
    .entries(values);
  return byMonth.map(function (d) {
    return [d.values, new Date(d.key).getTime()/1000];
  });
}

function load() {
    d3.json(
        "/growth/users/rest/registrations/frequency",
        function(responseData) {
            compositeDataSeries = formatData(responseData);
            compositeDataSeries[1].values = sumByMonth(compositeDataSeries[1].values);
            cumulativeTrend = compositeDataSeries[0];
            visualise([cumulativeTrend], areaChart);
        });
}

load();

// Flick between the 2 kinds of chart/data.

function changeGraph() {
    $('#graph-buttons li').removeClass('active');
    $(this).addClass('active');
    isCumulative = this.id == 'cumulative';
    var trendSelector = isCumulative ? 0 : 1;
    var trend = compositeDataSeries[trendSelector];
    var chart = isCumulative ? areaChart : histoChart;
    visualise([trend], chart);
}

d3.selectAll("#graph-buttons li").on("click", changeGraph);
