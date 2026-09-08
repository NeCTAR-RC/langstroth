/* -*- Mode: js; tab-width: 2; indent-tabs-mode: nil; js-indent-level: 2; -*- */
////// Growth charts: total instances and used VCPUs.

// Depends on chart_common.js. Each canvas.chart element carries a
// data-url attribute naming a /growth/ endpoint that returns
// Graphite-shape JSON: [{target: name, datapoints: [[value,
// unix_seconds], ...]}, ...]. The series are drawn as a stacked area
// chart with an all-series tooltip totalled in the footer.

var charts = {};

function toDatasets(data) {
  return data.map(function(series) {
    var colour = chartColour(series.target);
    return {
      label: series.target,
      data: chartPoints(series.datapoints),
      borderColor: colour,
      backgroundColor: colour + 'b3',
      fill: true,
      pointRadius: 0,
      borderWidth: 1
    };
  });
}

function tooltipLabel(item) {
  return item.dataset.label + ': ' + formatCount(item.parsed.y);
}

function tooltipTotal(items) {
  if (items.length < 2) {
    return '';
  }
  var total = 0;
  items.forEach(function(item) {
    total += item.parsed.y;
  });
  return 'TOTAL: ' + formatCount(total);
}

function makeChart(canvas) {
  return new Chart(canvas, {
    type: 'line',
    data: {datasets: []},
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {duration: 500},
      interaction: {mode: 'index', intersect: false},
      scales: {
        x: {
          type: 'time',
          time: {tooltipFormat: 'yyyy-MM-dd HH:mm'}
        },
        y: {
          stacked: true,
          position: 'right',
          ticks: {callback: formatCount}
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: tooltipLabel,
            footer: tooltipTotal
          }
        }
      }
    },
    plugins: [crosshairPlugin]
  });
}

function loadChart(canvas, summarise, from, until) {
  var url = $(canvas).data('url') + '?format=json&summarise=' + summarise +
      '&from=' + from + '&until=' + until;
  fetch(url)
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      var chart = charts[canvas.id];
      chart.data.datasets = toDatasets(data);
      chart.update();
    });
}

function graphduration(selector, summarise, from, durationText) {
  $(selector).click(function() {
    $('#graph-buttons li a').removeClass('active');
    $(selector + " a").addClass('active');
    $('small.lead').text(durationText);

    var until = '';
    if (selector == "#alltime") {
      if (getQueryVariable('from')) {
        from = getQueryVariable('from');
      }
      if (getQueryVariable('until')) {
        until = getQueryVariable('until');
      }
    }
    $('.chart').each(function(index, canvas) {
      loadChart(canvas, summarise, from, until);
    });
  });
}

graphduration('#1month', '1hour', '-1months', 'Over the last month.');
graphduration('#6months', '12hours', '-6months', 'Over the last 6 months.');
graphduration('#1year', '1days', '-1years', 'Over the last year.');
graphduration('#3years', '3days', '-3years', 'Over the last 3 years.');
graphduration('#5years', '5days', '-5years', 'Over the last 5 years.');
graphduration('#alltime', '10days', '20120101', 'Since January 2012.');

$('.chart').each(function(index, canvas) {
  charts[canvas.id] = makeChart(canvas);
  loadChart(canvas, '12hours', '-6months', '');
});
