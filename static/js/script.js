jQuery(function ($) {

    'use strict';

    (function () {
        var today = new Date();

        var launch = new Date("April 01, 2018");
        var msPerDay = 24 * 60 * 60 * 1000;
        var timeLeft = (launch.getTime() - today.getTime());

        var e_daysLeft = timeLeft / msPerDay;
        var daysLeft = Math.floor(e_daysLeft);

        $('.calendar .left').text(daysLeft);
    })();

    (function () {
        $.getJSON("/static/json/data.json", function (data) {
            var raised = data.raised;
            var desktopProgress = (raised / 500000) * 100;
            var serverProgress = (raised / 5500000) * 100;

            // Desktop
            $('#preorder .target span').text("$" + raised.toLocaleString());
            if (desktopProgress >= 100) {
                $('#preorder .progress .progress-bar').width("100%");
                $('#preorder .expected span').text("100%");
            } else {
                $('#preorder .progress .progress-bar').width(desktopProgress + "%");
                $('#preorder .expected span').text(desktopProgress.toFixed(0) + "%");
            }

            // Server
            $('#section-next .target span').text(serverProgress.toFixed(0) + "%");
            if (serverProgress >= 100) {
                $('#section-next .progress .progress-bar').width("100%");
            } else {
                $('#section-next .progress .progress-bar').width(serverProgress + "%");
            }
        });
    })();
}); // JQuery end
