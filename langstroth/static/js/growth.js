function getQueryVariable(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if(pair[0] == variable){return pair[1];}
  }
  return(false);
}

var colors = d3.scale.category10();
keyColor = function(d, i) {return colors(d.target);};

unix_timestamp = function(timestamp){
  return new Date(timestamp * 1000);
};

format_data = function(data) {
  return data.map(function(series) {
    series.values = series.datapoints;
    series.values = series.values.map(
      function (value) {
        if (!value[0]) {
          value[0] = 0;
        }
        return value;
      });

    delete series.datapoints;
    series.key = series.target;
    return series;
  });};

var charts = {};

["instance_count", "vcpu_used"].map(
  function (graph_name) {

    var chart = nv.models.stackedAreaChart();
    chart.margin({right: 100})
      .x(function(d) { return d[1];})
      .y(function(d) { return d[0];})
      .useInteractiveGuideline(true)
      .showTotalInTooltip(true)
      .rightAlignYAxis(true)
      .duration(500)
      .showControls(true)
      .clipEdge(true);

    //Format x-axis labels with custom function.
    chart.xAxis
      .tickFormat(function(d) {
        return d3.time.format("%Y-%m-%d")(unix_timestamp(d));
      });

    chart.yAxis
      .tickFormat(d3.format(',.0f'));

    charts[graph_name] = chart;
  });

graphduration =
  function (selector, summarise, from, duration_text) {
    button = $(selector);
    button.click(
      function () {
        $('#graph-buttons li').removeClass('active');

        $(selector).addClass('active');
        $('small.lead').text(duration_text);

        var graphs = $('.chart');
        /* Set the default path to the resource */

        var until = '';
        graphs.each(function (index, graph) {
          url = $(graph).data('url');
          if (selector == "#alltime") {
            if (getQueryVariable('from')) {
                from = getQueryVariable('from');
            }
            if (getQueryVariable('until')) {
                until = getQueryVariable('until');
            }
          }
          d3.json(url + '?format=json&summarise=' + summarise + '&from=' + from + '&until=' + until, function(data) {
            data = format_data(data);
            d3.select(graph)
              .datum(data)
              .transition().duration(500)
              .call(charts[graph.id]);
          });
        });
      });

  };

graphduration('#1day', '1hour', '-1day', 'Over the last day.');
graphduration('#1week', '1hour', '-7days', 'Over the last week.');
graphduration('#1month', '1hour', '-1months', 'Over the last month.');
graphduration('#6months','12hours', '-6months', 'Over the last 6 months.');
graphduration('#1year', '1days', '-1years', 'Over the last year.');
graphduration('#3years', '3days', '-3years', 'Over the last 3 years.');
graphduration('#5years', '5days', '-5years', 'Over the last 5 years.');
graphduration('#alltime', '10days', '20120101', 'Since January 2012.');

$('.chart').each(function (index, graph) {
  url = $(graph).data('url');

  d3.json(url + '?format=json&summarise=' + '12hours' + '&from=' + '-6months', function(data) {
    nv.addGraph(function() {
      data = format_data(data);

      d3.select(graph)
        .datum(data)
        .call(charts[graph.id]);

      nv.utils.windowResize(charts[graph.id].update);
    });
  });
});
