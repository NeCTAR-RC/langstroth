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
  var forCodes = route;
  return this.nextLevel(forCodes, children);
}

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
}

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
}

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
}

Allocations.prototype.dataset = function(route, isCoreQuota) {
  var tree = route ? this.traverse(route) : this.allocationTree;
  return this.restructureAllocations(tree, isCoreQuota);
}

