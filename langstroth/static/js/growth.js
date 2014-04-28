growth_text = 'Cloud growth over the last ';

var colors = d3.scale.category20();
keyColor = function(d, i) {return colors(d.target);};

unix_timestamp = function(timestamp){
  return new Date(timestamp * 1000);
};

format_data = function(data) {
  return data.map(function(series) {
    series.values = series.datapoints;
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
      .rightAlignYAxis(true)
      .transitionDuration(500)
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
        $('#graph-buttons button').removeClass('active');

        $(selector).addClass('active');
        $('small.lead').text(growth_text + duration_text);

        var graphs = $('.chart');
        /* Set the default path to the resource */

        graphs.each(function (index, graph) {
          url = $(graph).data('url');
          d3.json(url + '?format=json&summarise=' + summarise + '&from=' + from, function(data) {
            data = format_data(data);
            d3.select(graph)
              .datum(data)
              .transition().duration(500)
              .call(charts[graph.id]);
          });
        });
      });

  };

graphduration('#1month', '1hour', '-1months', 'month.');
graphduration('#6months','12hours', '-6months', '6 months.');
graphduration('#1year', '1days', '-1years', 'year.');
graphduration('#3years', '3days', '-3years', '3 years.');

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
