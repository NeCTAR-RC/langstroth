/* -*- Mode: js; tab-width: 2; indent-tabs-mode: nil; js-indent-level: 2; -*- */
////// Shared helpers for the Chart.js pages (growth, user statistics).

// Match the site typography (Figtree, loaded in main.scss).
Chart.defaults.font.family = "'Figtree', sans-serif";
Chart.defaults.font.size = 13;

// The d3 category10 palette the nvd3 charts used, assigned to series
// names in first-seen order so a series keeps its colour across the
// charts on a page.
var CHART_COLOURS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                     '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];

var assignedChartColours = {};
var nextChartColourIndex = 0;

function chartColour(key) {
  if (!(key in assignedChartColours)) {
    assignedChartColours[key] =
      CHART_COLOURS[nextChartColourIndex % CHART_COLOURS.length];
    nextChartColourIndex++;
  }
  return assignedChartColours[key];
}

function formatCount(value) {
  return Number(value).toLocaleString();
}

// Convert one Graphite-shape series' datapoints ([[value, unix_seconds],
// ...], value possibly null) to Chart.js {x: milliseconds, y} points.
function chartPoints(datapoints) {
  return datapoints.map(function(point) {
    return {x: point[1] * 1000, y: point[0] || 0};
  });
}

// Vertical guide line through the hovered points, the equivalent of the
// nvd3 interactive guideline.
var crosshairPlugin = {
  id: 'crosshair',
  afterDatasetsDraw: function(chart) {
    var active = chart.tooltip && chart.tooltip.getActiveElements();
    if (!active || !active.length) {
      return;
    }
    var ctx = chart.ctx;
    var area = chart.chartArea;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(active[0].element.x, area.top);
    ctx.lineTo(active[0].element.x, area.bottom);
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
    ctx.stroke();
    ctx.restore();
  }
};

function getQueryVariable(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i = 0; i < vars.length; i++) {
    var pair = vars[i].split("=");
    if (pair[0] == variable) {
      return pair[1];
    }
  }
  return false;
}
