let dateOfBirth = null;
$(document).ready(function () {
  $('#user-dob').datepicker({
    format: 'yyyy-mm-dd',
  });
  $('#user-dob').on('input', function () {
    dateOfBirth = $(this).val();
  });
  $('#user-dob').on('change', function () {
    dateOfBirth = $(this).val();
  });
});

function uploadPicture() {
  // Implement the logic to handle picture upload here
  alert('Implement picture upload logic');
}

async function submitForm() {
  var forms = document.querySelectorAll('.needs-validation');
  console.log(forms);
  if (!dateOfBirth) {
    alert('Please enter your date of birth');
    return;
  }
  const formResults = {
    user_info: {
      email_address: $('#user-email').val(),
      username: $('#username').val(),
      password: $('#password').val(),
      dob: dateOfBirth,
      phone: $('#user-phone').val(),
    },
  };
  console.log(formResults);
  console.log(JSON.stringify(formResults));
  const res = await fetch(`${user_api_endpoint}/`, {
    method: 'POST',
    body: JSON.stringify(formResults.user_info),
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
    },
  });
  if (res.ok) {
    // Redirect to home page on successful form submit + API call.
    window.location.replace('/');
  } else {
    alert('There was an error while registering. Please try again.');
  }
}