// Colour palette management for hierarchical pie chart.
// Used by allocations_pi.js and for_table.js
// Depends on the d3.js library.

// ColourPalette management class.

function ColourPalette() {

  var colours = ['#4169e1', '#dc143c', '#ff4500', '#ffd700', '#008000',
                 '#00bfff', '#008b8b', '#9400d3', '#0000ff', '#db7093',
                 '#c26200', '#00fa9a', '#8b4513', '#00ffff', '#556b2f',
                 '#ffa07a', '#7cfc00', '#7f007f', '#9acd32', '#ee82ee',
                 '#ff1493', '#d8bfd8'];
 
  // d3.schemeCategory20
  this.basePalette = this.fill(colours, 22);
  this.paletteStack = [this.basePalette];
}

ColourPalette.prototype.fill = function (colourScale, colourCount) {
  var colourLookup = [];
  for (var colourIndex = 0; colourIndex < colourCount; colourIndex++) {
    var colour = colourScale[colourIndex];
    colourLookup.push(colour);
  }
  return colourLookup;
};

ColourPalette.prototype.reset = function () {
  this.paletteStack = [this.basePalette];
};

//The palette that is relevant to this FOR tree level.

ColourPalette.prototype.current = function () {
  return this.paletteStack[this.paletteStack.length - 1];
};

ColourPalette.prototype.getColour = function (colourIndex) {
  var currentPalette = this.current();
  colourIndex = Math.min(colourIndex, currentPalette.length - 1);
  return currentPalette[colourIndex];
};

// A new d3 colour palette for the next inner level is added
// to the palette stack.
// colour index addresses the colour in the current palette
// and then uses that colour to generate a new palette.

ColourPalette.prototype.push = function (colourIndex, datasetLength) {
  var currentColour = this.getColour(colourIndex);
  var paletteRange = d3.scaleLinear()
      .domain([0, datasetLength + 5])
      .range([currentColour, "#fff"]);
  var paletteArr = [];
  for (var i = 0; i < n; ++i) {
    paletteArr.push(paletteRange(i));
  }
  var newPalette = this.fill(paletteArr, datasetLength);
  this.paletteStack.push(newPalette);
};

// A previous palette to be used for the next outer level is exposed
// on the top of the palette stack.

ColourPalette.prototype.pop = function () {
  // Restore next outer palette.
  this.paletteStack.pop();
};

// Go to target level.
// home = level 1.
// one in from home = level 2 etc..
ColourPalette.prototype.popToLevel = function (targetLevel) {
  this.paletteStack = this.paletteStack.slice(0, targetLevel);
};
