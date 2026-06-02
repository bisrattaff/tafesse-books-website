// Subscription form handler — submits to Formspree.
// SETUP REQUIRED: Sign up at formspree.io, create a form, then replace
// YOUR_SUBSCRIBE_FORM_ID below with the ID from your Formspree dashboard (e.g. "mrgvwkne").
var SUBSCRIBE_FORM_URL = "https://formspree.io/f/mpqngdwe";

function submitToSubscriptionAPI(e) {
   e.preventDefault();

   var Namere = /[A-Za-z]{1}[A-Za-z]/;
   if (!Namere.test($("#subscriber-name").val())) {
      alert("Name is too short. Please provide your name so we can address you properly.");
      return;
   }
   if ($("#subscriber-email").val() === "") {
      alert("Please provide your email address.");
      return;
   }
   var emailre = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,6})?$/;
   if (!emailre.test($("#subscriber-email").val())) {
      alert("Please enter a valid email address.");
      return;
   }

   var data = {
      name: $("#subscriber-name").val(),
      email: $("#subscriber-email").val()
   };

   $.ajax({
      type: "POST",
      url: SUBSCRIBE_FORM_URL,
      dataType: "json",
      data: data,
      success: function () {
         alert("Thank you for subscribing! You will be notified by email when there are updates to this site.");
         document.getElementById("subscribe-form").reset();
      },
      error: function () {
         alert("Sorry, there was a problem adding your email. Please try again, or contact the site admin at bisrattaff@gmail.com.");
      }
   });
}
