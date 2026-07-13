
// for profile drop-down 
document.addEventListener("DOMContentLoaded", function () {
    const profileIcon = document.getElementById("profile-icon");
    const dropdown = document.getElementById("dropdown-menu");
    if (!profileIcon || !dropdown) return;

    profileIcon.addEventListener("click", function (event) {
        dropdown.classList.toggle("show"); // Toggle class to show/hide
        event.stopPropagation(); // Prevent immediate closing
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
        if (!profileIcon.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.remove("show"); // Hide dropdown
        }
    });
});


// for image transition 
document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelector(".slides");
    if (!slides) return;
    const images = slides.querySelectorAll("img");
    const totalImages = images.length;
    
    // Clone first few images for infinite effect
    images.forEach((img) => {
        let clone = img.cloneNode(true);
        slides.appendChild(clone);
    });

    let index = 0;
    const slideWidth = images[0].clientWidth;
    
    function moveSlide() {
        index++;
        slides.style.transition = "transform 1.0s linear"; // Smooth transition
        slides.style.transform = `translateX(-${index * slideWidth}px)`;

        // When reaching the cloned images, reset instantly
        if (index === totalImages) {
            setTimeout(() => {
                slides.style.transition = "none"; // Remove transition
                slides.style.transform = "translateX(0)";
                index = 0;
            }, 1000); // Wait for transition to end
        }
    }

    // Auto move every 2 seconds
    setInterval(moveSlide, 2000);
});


// for report date range
// document.getElementById("start-date").addEventListener("change", function () {
//     let startDate = this.value;
//     document.getElementById("end-date").min = startDate;
// });

// for report date range
const startDateInput = document.getElementById("start-date");
if (startDateInput) {
    startDateInput.addEventListener("change", function () {
        let startDate = this.value;
        const endDateInput = document.getElementById("end-date");
        if (endDateInput) {
            endDateInput.min = startDate;
        }
    });
}


// for password eye icon 
function togglePassword() {
    let passwordInput = document.getElementById("password");
    let toggleEye = document.getElementById("toggleEye");

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        toggleEye.classList.remove("fa-eye");
        toggleEye.classList.add("fa-eye-slash");
        // toggleEye.setAttribute("data-tooltip", "Hide Password");
    } else {
        passwordInput.type = "password";
        toggleEye.classList.remove("fa-eye-slash");
        toggleEye.classList.add("fa-eye");
        // toggleEye.setAttribute("data-tooltip", "Show Password");
    }
}


// for history page 
function filterExpenses(type) {
    const rows = document.querySelectorAll("#expenseTable tbody tr");
    const tabs = document.querySelectorAll(".tab");

    // Highlight active tab
    tabs.forEach(tab => tab.classList.remove("active"));
    [...tabs].find(tab => tab.innerText === type).classList.add("active");

    rows.forEach(row => {
        const rowType = row.getAttribute("data-type");
        if (type === "All" || rowType === type) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}


// for messages 
document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);

    if (params.has("login")) {
        const status = params.get("login");

        if (status === "success") {
            alert("Successfully Logged In!");
        } else if (status === "failed") {
            alert("Invalid username or password.");
        }
    }

    if (params.has("register") && params.get("register") === "success") {
        alert("Successfully Registered!");
        removeQueryParam("register");
    }

    if (params.has("logout") && params.get("logout") === "true") {
        alert("You have been logged out!");
        removeQueryParam("logout");
    }

    if (params.has("auth") && params.get("auth") === "required") {
        alert("You must login first!");
        removeQueryParam("auth");
    }

    if (params.has("submitted") && params.get("submitted") === "true") {
        alert("Expense submitted successfully!");
        removeQueryParam("submitted");
    }

    if (params.has("budget_saved")) {
        if (params.get("budget_saved") === "true") {
            alert("Monthly budget saved!");
        } else {
            alert("Please enter a valid budget amount.");
        }
        removeQueryParam("budget_saved");
    }

    if (params.has("recurring_added") && params.get("recurring_added") === "true") {
        alert("Recurring transaction added to your history!");
        removeQueryParam("recurring_added");
    }

    if (params.has("saved") && params.get("saved") === "true") {
        alert("Recurring rule saved!");
        removeQueryParam("saved");
    }

    if (params.has("deleted_rule") && params.get("deleted_rule") === "true") {
        alert("Recurring rule deleted.");
        removeQueryParam("deleted_rule");
    }

    if (params.has("updated") && params.get("updated") === "true") {
        alert("Transaction updated!");
        removeQueryParam("updated");
    }

    if (params.has("deleted") && params.get("deleted") === "true") {
        alert("Transaction deleted!");
        removeQueryParam("deleted");
    }

    if (params.has("reset")) {
        if (params.get("reset") === "success") {
            alert("Password reset successfully! Please log in.");
        } else if (params.get("reset") === "failed") {
            alert("Username or security key is incorrect.");
        }
        removeQueryParam("reset");
    }

    if (params.has("register") && params.get("register") === "failed") {
        alert("Registration failed. Username or email may already exist.");
        removeQueryParam("register");
    }

    function removeQueryParam(param) {
        const url = new URL(window.location.href);
        url.searchParams.delete(param);
        window.history.replaceState({}, document.title, url.pathname + url.search);
    }
});


const checkBalanceBtn = document.getElementById("check-balance-btn");
if (checkBalanceBtn) {
    checkBalanceBtn.addEventListener("click", function () {
        window.location.href = "/balance";
    });
}
