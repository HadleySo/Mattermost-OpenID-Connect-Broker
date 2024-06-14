// This removes the JavaScript error message and allows the page content to render
// If JavaScript is disabled, the JavaScript error message is not removed.

document.querySelector("#JS_error_message").innerHTML = "Loading. . .";

// This removes the IFE icon loading page and allows the page content to be visible
// Waits for everything to load, including images.
function clearIcon() {
    // Waits 300ms
    setTimeout(function() {
        document.querySelector("#loading-icon").style.display = "none"; // Hides icon
        document.querySelector("#post-js-check").style.display = "block"; // Display the main body section
    }, 300)
}

// Calls clearIcon() after everything is loaded
window.onload = clearIcon;