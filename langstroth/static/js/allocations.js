// Allocations data Management

function Allocations(allocationTree) {
    this.allocationTree = allocationTree ? allocationTree : {};
}

// Recursive code to return allocation tree branch (children)
// addressed by FOR code.
// The forCode is the FOR2, FOR4 or FOR6 code.
// The allocationObjects is the allocationTree object being passed in.
Allocations.prototype.traverse = function(route) {
  var children = this.allocationTree;
  var forCodes = route.concat();
  return this.nextLevel(forCodes, children);
};

// Recurse the allocation tree to return a branch.
Allocations.prototype.nextLevel = function(forCodes, children) {
  var forCode = forCodes.pop();
  if (forCode) {
    var childCount = children.length;
    for (var childIndex = 0; childIndex < childCount; childIndex++) {
      var child = children[childIndex];
      var name = child.name;
      if (name == forCode) {
        return this.nextLevel(forCodes, child.children);
      }
    }
  }
  return children;
};

// Restructure allocation tree into a single level array of objects.
// The tree is flattened by taking the sum of all allocations on the branch.
Allocations.prototype.restructureAllocations =
                              function (subTree, isCoreQuota) {
  var colourIndex = 0;
  var dataset = [];
  var allocationCount = subTree.length;
  for (var allocationIndex = 0;
    allocationIndex < allocationCount;
    allocationIndex++) {
    var sum = 0.0;
    var child = subTree[allocationIndex];
    var name = child.name;
    var allocationItem = {};
    if (child.children) {
      // add the branch value.
      sum = this.nextLevelSum(child.children, isCoreQuota);
    } else {
      // add the leaf value.
      allocationItem.id = child.id;
      allocationItem.projectName = child.name;
      allocationItem.institutionName = child.institution;
      allocationItem.coreQuota = child.coreQuota;
      allocationItem.instanceQuota = child.instanceQuota;
      sum = isCoreQuota ? child.coreQuota : child.instanceQuota;
    }
    allocationItem.target = name;
    allocationItem.value = sum;
    dataset.push(allocationItem);
  }
  dataset.sort(function(a, b){return b.value - a.value; });
  var recordCount = dataset.length;
  for (var recordIndex = 0; recordIndex < recordCount; recordIndex++) {
    dataset[recordIndex].colourIndex = colourIndex++;
  }
  return dataset;
};

// Recurse the allocation tree to return a sum.
Allocations.prototype.nextLevelSum = function(children, isCoreQuota) {
  var sum = 0.0;
  var childCount = children.length;
  for (var childIndex = 0; childIndex < childCount; childIndex++) {
    var child = children[childIndex];
    if (child.children) {
      sum += this.nextLevelSum(child.children, isCoreQuota);
    } else {
      sum += isCoreQuota ? child.coreQuota : child.instanceQuota;
    }
  }
  return sum;
};

Allocations.prototype.dataset = function(route, isCoreQuota) {
  var tree = route ? this.traverse(route) : this.allocationTree;
  return this.restructureAllocations(tree, isCoreQuota);
};

Allocations.prototype.assemblePath = function(forCodeComponents, codeCount) {
	var forCodePath = [];
	var isZeroPadding = false;
	var forCode = forCodeComponents[0];
	forCodePath.push(forCode);
	for (var codeIndex = 1; codeIndex < codeCount; codeIndex++) {
		forCode = forCodePath[codeIndex - 1];
		var forCodeComponent = forCodeComponents[codeIndex];
		isZeroPadding = isZeroPadding || forCodeComponent == "00";
		if (!isZeroPadding) {
			forCode += forCodeComponent;
		}
		forCodePath.push(forCode);
	}
	return forCodePath;
};

// FOR code parameter strings are interpreted as a 1,2 or 3 element path.
// 00 components cause path extensions.
// E.g. 053725 becomes /05/0537/053725
// E.g. 050000 becomes /05/05/05
// E.g. 053700 becomes /05/0537/0537
// E.g. 0345 becomes /03/0345
Allocations.prototype.parseForPath = function(pathExtension) {
	var forCodePath = [];
	var command = pathExtension.substring(1);
	var FOR_COMMAND = "/FOR/";
	if (command && command.indexOf(FOR_COMMAND) === 0) {
		var forTarget = command.substring(FOR_COMMAND.length);
		var codeCount = forTarget.length / 2;
		if (codeCount == 1 || codeCount == 2 || codeCount == 3) {
	    	var forCodeComponents = [];
	    	for (var codeIndex = 0; codeIndex < codeCount; codeIndex++) {
	    		var firstIndex = codeIndex * 2;
	    		var forCodeComponent = forTarget.substr(firstIndex, 2);
	    		forCodeComponents.push(forCodeComponent);
	    	}
			forCodePath = this.assemblePath(forCodeComponents, codeCount);
		}
	}
	return forCodePath.reverse();
};


