// Colour palette management for hierarchical pie chart.
// Used by allocations_pi.js and for_table.js
// Depends on the d3.js library.

// Array return top-of-stack method.

Array.prototype.tos = function() {
  return this[this.length - 1];
};

// ColourPalette management class.

function ColourPalette() {
	var colorPalette = d3.scale.category20();
	this.paletteStack = [colorPalette];
}

//The palette that is relevant to this FOR tree level.

ColourPalette.prototype.current = function () {
  return this.paletteStack.tos();
};

// A new d3 colour palette for the next inner level is added
// to the palette stack.
// colour index addresses the colour in the current palette
// and then uses that colour to generate a new palette.

ColourPalette.prototype.nextIn = function (colourIndex, datasetLength) {
    var currentPalette = this.current();
    var currentColour = currentPalette(colourIndex);
    var newPalette = d3.scale.linear()
          .domain([0, datasetLength + 10])
          .range([currentColour, "white"]);
    this.paletteStack.push(newPalette);
};

// A previous palette to be used for the next outer level is exposed
// on the top of the palette stack.

ColourPalette.prototype.nextOut = function (colourIndex, datasetLength) {
    // Restore next outer palette.
	this.paletteStack.pop();
};

// Go to target level.
// home = level 1.
// one in from home = level 2 etc..
ColourPalette.prototype.manyOut = function (targetLevel) {
    this.paletteStack = this.paletteStack.slice(0, targetLevel);
};
