showAdv = function(data) {
  $('#advs').html(data.adv);
  if (data.adv != "") {
    $('#advs').show();
  } else { $('#advs').hide(); }
}

showTimes = function(data) {
  $('#err').hide();
  $('h1').html(data.station);
  $('h2').html(data.dest);
  $.each(data.trains, function(i, train) {
    $('span.train span.time').get(i).innerHTML = '' + train[0];
    $('span.train span.cars').get(i).innerHTML = '' + train[1] + ' cars';
  });
  $.ajax({ type: "POST", url: '/adv', data: 'stn=' + data.abbr,
    dataType: 'json', success: showAdv});
};

showError = function(data) {
  $('h1').html("ERROR");
  $('#err #msg').html(data.responseText);
  $('#err').css('display', 'block');
}

sendLocation = function(location) {
  /* Send lat/long to server */
  $.ajax({
   type: "POST",
   url: '/loc',
   data: "lat=" + location.coords.latitude + "&lon=" + location.coords.longitude,
   dataType: 'json',
   success: showTimes,
   error: showError
  });
};

getTimes = function() {
  $('h1').html('Fetching..');
  navigator.geolocation.getCurrentPosition(sendLocation);
};

jQuery(document).ready(function($) {
  getTimes();
  document.addEventListener('pageshow', getTimes);
  document.addEventListener('reset', getTimes);
  $(document).on('pageshow', getTimes);
  $('*').click(getTimes);
})
