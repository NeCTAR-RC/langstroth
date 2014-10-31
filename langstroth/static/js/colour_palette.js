// Colour palette management for hierarchical pie chart.
// Used by allocations_pi.js and for_table.js
// Depends on the d3.js library.

// ColourPalette management class.

function ColourPalette() {
  this.basePalette = this.fill(d3.scale.category20(), 22);
  this.paletteStack = [this.basePalette];
}

ColourPalette.prototype.fill = function (colourScale, colourCount) {
  var colourLookup = [];
  for (var colourIndex = 0; colourIndex < colourCount; colourIndex++) {
    var colour = colourScale(colourIndex);
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
  var newPalette = this.fill(d3.scale.linear()
          .domain([0, datasetLength + 10])
          .range([currentColour, "white"]), datasetLength);
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
