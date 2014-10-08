var registrationFrequency = [];
var isCumulative = true;

var dateFormat = d3.time.format("%Y-%m-%d");
var parseDate = dateFormat.parse;

var MARGIN = {TOP: 20, RIGHT: 20, BOTTOM: 30, LEFT: 50},
WIDTH = 960 - MARGIN.LEFT - MARGIN.RIGHT,
HEIGHT = 500 - MARGIN.TOP - MARGIN.BOTTOM;

var x = d3.time.scale()
    .range([0, WIDTH]);

var y = d3.scale.linear()
    .range([HEIGHT, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom")
    .innerTickSize([-HEIGHT])
    .outerTickSize([-HEIGHT])
    .tickPadding([8])
    .tickFormat(function(d, i) {
            return dateFormat(d);
    });

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left")
    .innerTickSize([-WIDTH])
    .outerTickSize([-WIDTH])
    .tickPadding([8]);

var svg = d3.select("#plot-area").append("svg")
    .attr("width", WIDTH + MARGIN.LEFT + MARGIN.RIGHT)
    .attr("height", HEIGHT + MARGIN.TOP + MARGIN.BOTTOM)
  .append("g")
    .attr("transform", "translate(" + MARGIN.LEFT + "," + MARGIN.TOP + ")");

var area = d3.svg.area()
    .x(function(d) { return x(d.date); })
    .y0(HEIGHT)
    .y1(function(d) { return y(d.count); });

//---- The render function

function visualise(trend) {

    x.domain(d3.extent(trend, function(d) { 
        return d.date; 
    }));
    y.domain([0, d3.max(trend, function(d) { 
        return d.count;
    })]);
  
    var path = svg.selectAll("path").data([trend]); 
    path.attr("class", "area").attr("d", area);
    path.enter().append("path").attr("class", "area").attr("d", area);
    path.exit().remove();
  
    var xAxisG = svg.selectAll("g.x");
    xAxisG.remove();
    
      svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + HEIGHT + ")")
          .call(xAxis);
      
        var yAxisG = svg.selectAll("g.y");
        yAxisG.remove();

        svg.append("g")
          .attr("class", "y axis")
          .call(yAxis)
          ;
}

function processResponse(registrationFrequency) {
    var trend = [];
    var sum = 0;
    registrationFrequency.forEach(function(record) {
        var item = {};
        item.date = parseDate(record.date);
        if (isCumulative) {
            sum += +record.count;
            item.count = sum;
        } else {
            item.count = +record.count;
        }
        trend.push(item);
      });
    return trend;
}

function load() {
    d3.json("/user_statistics/rest/registrations/frequency", function(error, responseData) {
        registrationFrequency = responseData;
        var trend = processResponse(registrationFrequency);
        visualise(trend);
    });
}

load();

function change() {
    $('#graph-buttons button').removeClass('active');
    $(this).addClass('active');
    isCumulative = this.id == 'cumulative';
    var trend = processResponse(registrationFrequency);
    visualise(trend);
}

d3.selectAll("button").on("click", change);
