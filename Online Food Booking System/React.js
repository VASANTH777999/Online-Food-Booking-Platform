const verifyLogin = async (token) => {
    try {
        const response = await fetch(`http://localhost:5000/api/auth/verify-login/${token}`);
        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("token", data.token);
            window.location.href = "/dashboard"; // Redirect after successful login
        } else {
            alert("Verification failed. Try again.");
        }
    } catch (error) {
        console.error("Error verifying login", error);
    }
};
