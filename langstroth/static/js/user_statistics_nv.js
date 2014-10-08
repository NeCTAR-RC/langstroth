var registrationFrequency = [];
var isCumulative = true;

var shortDateFormat = d3.time.format("%Y-%m");
var dateFormat = d3.time.format("%Y-%m-%d");
var parseDate = dateFormat.parse;
var frequencyFormat = d3.format(',.0f');

var xTicks = [];
var xTickIncrement = 3;

var CUMULATIVE_LABEL = 'User Registrations';
var FREQUENCY_LABEL = 'User Registrations Per Month';

// Date utilities.

// Date of first day of next month.
Date.prototype.nextMonth = function() {
    return  new Date(this.getFullYear(), this.getMonth() + 1, 1, 0, 0, 0, 0);
}

// Date of last day of this month.
Date.prototype.lastDateOfMonth = function() {
    return  new Date(this.getFullYear(), this.getMonth() + 1, 0, 0, 0, 0, 0);
}

// Build area chart

var areaChart = nv.models.stackedAreaChart()
    .margin({right: 100})
    .x(function(d) { 
          return d[0].getTime(); 
          })   
    .y(function(d) { 
          return d[1]; 
          })  
    .useInteractiveGuideline(true) 
    .rightAlignYAxis(true) 
    .transitionDuration(500)
    .showControls(false)
    .clipEdge(true);
    
    areaChart.xAxis.tickFormat(function(d) {
    return shortDateFormat(new Date(d)) ;
    });

    areaChart.yAxis.tickFormat(frequencyFormat);
    
// Build histogram chart
    
    var histoChart = nv.models.historicalBarChart()
        .x(function(d, i) { 
            return d[0].getTime(); 
        })   
        .y(function(d) { 
            return d[1]; 
        })  
        .rightAlignYAxis(true) 
        .transitionDuration(500)
        .clipEdge(false);

        histoChart.xAxis.tickFormat(function(d) {
            return shortDateFormat(new Date(d)) ;
        });
        histoChart.xAxis.tickValues(xTicks);

        histoChart.yAxis.tickFormat(frequencyFormat);
        histoChart.showLegend(true);
        

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

function processResponse(registrationFrequency, legendKey) {
    var trend = [];
    var sum = 0;
    registrationFrequency.forEach(function(record) {
        var item = [];
        item[0] = parseDate(record.date);
        if (isCumulative) {
            sum += +record.count;
            item[1] = sum;
        } else {
            item[1] = +record.count;
        }
        trend.push(item);
      });

    var wrappedTrend = {};
    wrappedTrend['key'] = legendKey;
    wrappedTrend['values'] = trend;
    return [wrappedTrend];
}

function expandXDomain(trend) {
    var xExtent = d3.extent(trend[0].values, function(d) {
        return d[0];
    });
    var lastDate = xExtent[1];
    lastDate.setMonth(lastDate.getMonth() + 1);
    xExtent[1] = lastDate.getTime();
    histoChart.xDomain(xExtent);
}

function defineXTicks(trend) {
    var xExtent = d3.extent(trend[0].values, function(d) {
        return d[0];
    });
    var lastTime = xExtent[1];
    var firstTime = xExtent[0];
    var tickDate = new Date(firstTime);
    tickDate = tickDate.nextMonth().lastDateOfMonth();
    xTicks.push(tickDate.getTime());
    var tickCount = 0;
    while (tickDate.getTime() < lastTime) {
        tickDate = tickDate.nextMonth().lastDateOfMonth();
        if (tickCount == xTickIncrement) {
            xTicks.push(tickDate.getTime());
            tickCount = 0;
        } else {
            tickCount++;
        }
    }
    tickDate = tickDate.nextMonth().lastDateOfMonth();
    xTicks.push(tickDate.getTime());
}

function load() {
    d3.json("/user_statistics/rest/registrations/frequency", function(error, responseData) {
        registrationFrequency = responseData;
        var legendKey = CUMULATIVE_LABEL;
        var trend = processResponse(registrationFrequency, legendKey);
        expandXDomain(trend);
        defineXTicks(trend);
        visualise(trend, areaChart);
    });
}

load();

// Flick between the 2 kinds of chart/data.

function change() {
    $('#graph-buttons button').removeClass('active');
    $(this).addClass('active');
    isCumulative = this.id == 'cumulative';
    var legendKey = isCumulative ? CUMULATIVE_LABEL : FREQUENCY_LABEL;
    var trend = processResponse(registrationFrequency, legendKey);
    var chart = isCumulative ? areaChart : histoChart;
    visualise(trend, chart);
}

d3.selectAll("button").on("click", change);
