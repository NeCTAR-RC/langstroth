/* -*- Mode: js; tab-width: 4; indent-tabs-mode: nil; js-indent-level: 4;-*- */

var registrationFrequency = [];
var isCumulative = true;

unixTimestamp = function(timestamp) {
    return new Date(timestamp * 1000);
};

formatData = function(data) {
    return data.map(function(series) {
        series.values = series.datapoints;
        series.values = series.values.map(function(value) {
            if (!value[0]) {
                value[0] = 0;
            }
            return value;
        });

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
    .rightAlignYAxis(true)
    .transitionDuration(500)
    .showControls(false)
    .showLegend(false)
    .clipEdge(true);

areaChart.xAxis.tickFormat(function(d) {
    return shortDateFormat(new Date(d)) ;
});

areaChart.xAxis.ticks(d3.time.month, 3);
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
    .transitionDuration(500)
    .clipEdge(false);

histoChart.xAxis.tickFormat(function(d) {
    return shortDateFormat(new Date(d)) ;
});
histoChart.xScale(d3.time.scale());
histoChart.yAxis.tickFormat(frequencyFormat);

// Render the chart

var svg = null;

function visualise(trend, chart) {

    // Clean up the internal graph array.
    while(nv.graphs.length > 0) {
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

function load() {
    d3.json(
        "/growth/users/rest/registrations/frequency",
        function(responseData) {
            compositeDataSeries = formatData(responseData);
            cumulativeTrend = compositeDataSeries[0];
            visualise([cumulativeTrend], areaChart);
        });
}

load();

// Flick between the 2 kinds of chart/data.

function change() {
    $('#graph-buttons button').removeClass('active');
    $(this).addClass('active');
    isCumulative = this.id == 'cumulative';
    var trendSelector = isCumulative ? 0 : 1;
    var trend = compositeDataSeries[trendSelector];
    var chart = isCumulative ? areaChart : histoChart;
    visualise([trend], chart);
}

d3.selectAll("button").on("click", change);
