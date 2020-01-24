$(document).on('click', '#direct-option', function () {
    $('#movie-search').hide();
    $('#tv-search').hide();
    $('#direct-search').show();
});
$(document).on('click', '#movie-option', function () {
    $('#movie-search').show();
    $('#tv-search').hide();
    $('#direct-search').hide();
});

$(document).on('click', '#tv-option', function () {
    $('#movie-search').hide();
    $('#tv-search').show();
    $('#direct-search').hide();
});