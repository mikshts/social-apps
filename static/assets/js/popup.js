// Show the popup after a delay (e.g., 5 seconds)
window.addEventListener("load", () => {
  setTimeout(() => {
    document.getElementById("popup").style.display = "flex";
  }, 5000); // 5000 ms = 5 seconds
});

// Close the popup
document.getElementById("close-popup").addEventListener("click", () => {
  document.getElementById("popup").style.display = "none";
});

// Handle subscription button click
document.getElementById("subscribe-button").addEventListener("click", () => {
  const selectedPlan = document.querySelector(
    'input[name="subscription_plan"]:checked'
  ).value;

  console.log("Subscribed to:", selectedPlan); // Optional log

  document.getElementById("subscription-options").style.display = "none";
  document.getElementById("subscribe-button").style.display = "none";
  document.getElementById("subscription-confirmation").style.display = "block";
});
