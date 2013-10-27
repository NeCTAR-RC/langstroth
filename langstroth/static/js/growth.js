graphduration = 
  function (selector, from) {
    button = $(selector);
    button.click(
      function () {
        $('#graph-buttons button').removeClass('active');
        $(selector).addClass('active');

        var graphs = $('.graphite');
        /* Set the default path to the resource */
        if (!graphs.data('default-url'))
        {
          graphs.each(function () {
            $(this).data('default-url', $(this).attr('src'));
          });
        }

        graphs.each(function () {
          $(this).attr('src', $(this).data('default-url') + '?from=' + from);
        });
      });

  };

graphduration('#1month', '-1months');
graphduration('#6months', '-6months');
graphduration('#1year', '-1years');
graphduration('#2years', '-2years');
