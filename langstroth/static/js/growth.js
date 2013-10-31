growth_text = 'Cloud growth over the last ';

graphduration =
  function (selector, from, duration_text) {
    button = $(selector);
    button.click(
      function () {
        $('#graph-buttons button').removeClass('active');

        $(selector).addClass('active');
        $('p.lead').text(growth_text + duration_text);

        var graphs = $('.graphite');
        /* Set the default path to the resource */
        if (!graphs.data('default-url'))
        {
          graphs.each(function () {
            $(this).data('default-url', $(this).attr('src'));
          });
        }

        graphs.each(function () {
          $(this).attr('src', '');
          $(this).attr('src', $(this).data('default-url') + '?from=' + from);
        });
      });

  };

graphduration('#1month', '-1months', 'month.');
graphduration('#6months', '-6months', '6 months.');
graphduration('#1year', '-1years', 'year.');
graphduration('#2years', '-2years', '2 years.');
