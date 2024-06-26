// Custom functions
function scrollToId(elId) {
  document.getElementById(elId).scrollIntoView({
    behavior: 'smooth'
  });
}

function submitFilterFormOnChange(formId) {
  const form = document.getElementById(formId);
  let selects = form.getElementsByTagName("select");
  let inputs = form.getElementsByTagName("input");

  for(const selectEl of selects) {
    selectEl.addEventListener("change", function() {
      form.submit();
    });
  }

  for(const inputEl of inputs) {
    inputEl.addEventListener("change", function() {
      form.submit();
    });
  }
}

// Bootstrap components
var alertMessageList = [].slice.call(document.querySelectorAll('.toast'));
var alertMessages = alertMessageList.map(function (toastEl) {
  return new bootstrap.Toast(toastEl, {
    delay: 5000
  });
});

var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl);
});

// Window ready event
window.onload = function() {
  // if(window.location.hash) { scrollToId(window.location.hash) };
  
  if(document.getElementById('filter-form')) {
    submitFilterFormOnChange('filter-form');
  }

  // Is the home page status banner displayed?
  if(document.getElementById('status-banner')) {
    // Stop css animations after 1 minute
    setTimeout(function() {
      // pause cloud animations
      for(const cloud of document.getElementsByClassName("clouds")) {
        cloud.classList.add('paused');
      }
    }, 60000);
  }
};

// removes the focus state on from the buttons that were clicked to launch a modal
document.querySelectorAll(".modal").forEach(function(modal) {
  var modalButton = {};
  modal.addEventListener("shown.bs.modal", function(e) {
    modalButton = e.relatedTarget;
    modal.addEventListener("hidden.bs.modal", function(e) {
      modalButton.blur(); // Defocus the button that triggered the modal
    });
  });
});
