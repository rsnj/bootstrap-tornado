;(function ($, window, undefined) {
    'use strict';
    $(document).ready(function() {
        $('#login-btn').click(function() {
            FB.login(function(response) {
                if (response.authResponse) {
                    // connected
                    window.location = "/";
                } else {
                    // cancelled

                }
            });
        });
        $('#logout-btn').click(function() {
            FB.logout(function(response) {

                // user is now logged out
                // redirect the user back to the homepage
                window.location = "/";
            });
        });
    });
})(jQuery, this);
