
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

    if (params.has("report") && params.get("report") === "failed") {
        alert("Please pick both start and end dates for a custom report.");
        removeQueryParam("report");
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

// ================= Keyword auto-categorization (v2.0) =================
// Type "zomato" as payee -> category becomes Food automatically.
const CATEGORY_KEYWORDS = {
    "Food": ["zomato", "swiggy", "dominos", "pizza", "restaurant", "cafe", "chai", "kfc", "mcdonald", "burger", "dhaba", "biryani"],
    "Groceries": ["bigbasket", "blinkit", "zepto", "dmart", "grocery", "kirana", "sabzi", "ration", "instamart"],
    "Transport": ["uber", "ola", "rapido", "petrol", "diesel", "fuel", "metro", "bus", "train", "irctc", "cab", "auto", "toll"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "mall", "croma"],
    "Bills & Recharge": ["recharge", "jio", "airtel", "vodafone", "bsnl", "electricity", "bijli", "wifi", "broadband", "dth", "cylinder", "bill", "postpaid", "prepaid"],
    "Rent/Housing": ["rent", "kiraya", "maintenance", "hostel", "landlord", "society"],
    "Health": ["doctor", "hospital", "medicine", "pharmacy", "apollo", "medical", "clinic", "gym", "dawai", "1mg", "pharmeasy", "lab"],
    "Entertainment": ["netflix", "spotify", "hotstar", "prime video", "movie", "pvr", "inox", "bookmyshow", "game", "concert"],
    "Education": ["fees", "course", "udemy", "coursera", "tuition", "coaching", "exam", "college", "school"],
    "Cosmetics": ["nykaa", "salon", "cosmetic", "makeup", "shampoo", "parlour"]
};

function suggestCategory(payee) {
    if (!payee) return null;
    const p = payee.toLowerCase();
    for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
        for (const kw of keywords) {
            if (p.includes(kw)) return category;
        }
    }
    return null;
}

document.addEventListener("DOMContentLoaded", function () {
    // Wire every form that has both a payee input and a category select
    document.querySelectorAll("form").forEach(function (form) {
        const payeeInput = form.querySelector('input[name="payee"]');
        const categorySelect = form.querySelector('select[name="category"]');
        if (!payeeInput || !categorySelect) return;

        payeeInput.addEventListener("input", function () {
            const suggestion = suggestCategory(payeeInput.value);
            if (!suggestion) return;

            // Only auto-fill if the user hasn't picked a category manually
            const untouched = categorySelect.value === "" ||
                              categorySelect.dataset.autofilled === "true";
            if (untouched && categorySelect.value !== suggestion) {
                categorySelect.value = suggestion;
                categorySelect.dataset.autofilled = "true";
                categorySelect.style.borderColor = "#F48C06";
                setTimeout(function () { categorySelect.style.borderColor = ""; }, 800);
            }
        });

        // Manual choice wins: stop auto-filling after the user touches the select
        categorySelect.addEventListener("change", function () {
            categorySelect.dataset.autofilled = "false";
        });
    });
});

// ================= Dark mode (v2.1) =================
document.addEventListener("DOMContentLoaded", function () {
    const navRight = document.querySelector(".nav-right");
    if (!navRight) return; // login/register pages keep their own look

    // Apply saved preference
    if (localStorage.getItem("k2-theme") === "dark") {
        document.body.classList.add("dark");
    }

    const btn = document.createElement("button");
    btn.id = "theme-toggle";
    btn.type = "button";
    btn.title = "Toggle dark mode";
    btn.textContent = document.body.classList.contains("dark") ? "\u2600\uFE0F" : "\uD83C\uDF19";
    btn.addEventListener("click", function () {
        const dark = document.body.classList.toggle("dark");
        localStorage.setItem("k2-theme", dark ? "dark" : "light");
        btn.textContent = dark ? "\u2600\uFE0F" : "\uD83C\uDF19";
    });
    navRight.insertBefore(btn, navRight.firstChild);
});
