/* -*- Mode: js; tab-width: 2; indent-tabs-mode: nil; js-indent-level: 2; -*- */
////// User registrations chart: cumulative area or monthly frequency bars.

// Depends on chart_common.js. The REST endpoint returns two
// Graphite-shape series: [0] the daily cumulative user count, [1] the
// per-day registration count, which is aggregated to calendar months
// here before charting.

var chart = null;
var trends = null;

function sumByMonth(datapoints) {
  var totals = {};
  datapoints.forEach(function(point) {
    if (point[0] === null) {
      return;
    }
    var date = new Date(point[1] * 1000);
    var month = new Date(date.getFullYear(), date.getMonth()).getTime();
    totals[month] = (totals[month] || 0) + point[0];
  });
  return Object.keys(totals)
    .map(function(month) {
      return {x: Number(month), y: totals[month]};
    })
    .sort(function(a, b) {
      return a.x - b.x;
    });
}

function baseOptions(tooltipFormat) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: {duration: 500},
    interaction: {mode: 'index', intersect: false},
    scales: {
      x: {
        type: 'time',
        time: {tooltipFormat: tooltipFormat}
      },
      y: {
        position: 'right',
        ticks: {callback: formatCount}
      }
    },
    plugins: {
      legend: {display: false},
      tooltip: {
        callbacks: {
          label: function(item) {
            return item.dataset.label + ': ' + formatCount(item.parsed.y);
          }
        }
      }
    }
  };
}

function areaConfig(points) {
  var colour = chartColour('registrations');
  return {
    type: 'line',
    data: {
      datasets: [{
        label: 'Registered users',
        data: points,
        borderColor: colour,
        backgroundColor: colour + '4d',
        fill: 'origin',
        pointRadius: 0,
        borderWidth: 1.5
      }]
    },
    options: baseOptions('yyyy-MM-dd'),
    plugins: [crosshairPlugin]
  };
}

function barConfig(points) {
  var colour = chartColour('registrations');
  return {
    type: 'bar',
    data: {
      datasets: [{
        label: 'New users',
        data: points,
        backgroundColor: colour,
        barThickness: 'flex'
      }]
    },
    options: baseOptions('yyyy-MM'),
    plugins: [crosshairPlugin]
  };
}

function visualise(config) {
  if (chart) {
    chart.destroy();
  }
  chart = new Chart(document.getElementById('plot-chart'), config);
}

function load() {
  var url = '/growth/users/rest/registrations/frequency';
  var from = getQueryVariable('from') || '';
  var until = getQueryVariable('until') || '';
  fetch(url + '?from=' + from + '&until=' + until)
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      trends = {
        cumulative: chartPoints(data[0].datapoints),
        frequency: sumByMonth(data[1].datapoints)
      };
      visualise(areaConfig(trends.cumulative));
    });
}

load();

// Flick between the 2 kinds of chart/data.

$('#graph-buttons a').on('click', function() {
  $('#graph-buttons li a').removeClass('active');
  $(this).addClass('active');
  visualise(this.id == 'cumulative' ? areaConfig(trends.cumulative)
                                    : barConfig(trends.frequency));
});
