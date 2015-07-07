growth_text = 'Over the last ';

var colors = d3.scale.category20();
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
        var tmp = {x: value[1], y: value[0]};
        value = tmp;
        return value;
      });

    delete series.datapoints;
    series.key = series.target;
    delete series.target;
    console.log(series);
    return series;
  });};

var charts = {};

["capacity_768", "capacity_2048", "capacity_4096", "capacity_6144", "capacity_8192", "capacity_12288", "capacity_16384", "capacity_32768", "capacity_49152", "capacity_65536"].map(
  function (graph_name) {

    var chart = nv.models.lineChart()
      .margin({right: 100})
      .useInteractiveGuideline(true)
      .transitionDuration(500);

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

graphduration('#1day', '5mins', '-1day', 'day.');
graphduration('#1week', '30mins', '-7days', 'week.');
graphduration('#1month', '1hour', '-1month', 'month.');
graphduration('#6months','12hours', '-6months', '6 months.');

$('.chart').each(function (index, graph) {
  url = $(graph).data('url');

  d3.json(url + '?format=json&summarise=' + '5mins' + '&from=' + '-1day', function(data) {
    nv.addGraph(function() {
      data = format_data(data);
      d3.select(graph)
        .datum(data)
        .call(charts[graph.id]);

      nv.utils.windowResize(charts[graph.id].update);
    });
  });
});
