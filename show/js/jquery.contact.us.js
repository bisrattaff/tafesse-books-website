// Contact form handler — submits to Formspree.
// SETUP REQUIRED: Sign up at formspree.io, create a form, then replace
// YOUR_CONTACT_FORM_ID below with the ID from your Formspree dashboard (e.g. "xpzvwkne").
var CONTACT_FORM_URL = "https://formspree.io/f/meedbgov";

function submitToContactUsAPI(e) {
   e.preventDefault();

   var Namere = /[A-Za-z]{1}[A-Za-z]/;
   if (!Namere.test($("#name-input").val())) {
      alert("Name is too short. Please provide your name so we can address you properly.");
      return;
   }
   var mobilere = /[0-9]{10}/;
   if (!mobilere.test($("#phone-input").val())) {
      alert("Please provide a valid 10-digit phone number.");
      return;
   }
   if ($("#email-input").val() === "") {
      alert("Please provide your email address so we can follow up with you if needed.");
      return;
   }
   var emailre = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,6})?$/;
   if (!emailre.test($("#email-input").val())) {
      alert("Please enter a valid email address.");
      return;
   }

   var data = {
      name: $("#name-input").val(),
      phone: $("#phone-input").val(),
      email: $("#email-input").val(),
      message: $("#description-input").val()
   };

   $.ajax({
      type: "POST",
      url: CONTACT_FORM_URL,
      dataType: "json",
      contentType: "application/json; charset=utf-8",
      data: JSON.stringify(data),
      success: function () {
         alert("Thank you for contacting us! Your message has been sent to Tafesse Muluneh. If a follow-up is needed, we will get back to you.");
         document.getElementById("contact-form").reset();
      },
      error: function () {
         alert("Sorry, there was a problem sending your message. Please try again, or email Tafesse directly at muluneh@aol.com.");
      }
   });
}
