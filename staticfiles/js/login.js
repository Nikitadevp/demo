const showPassword = document.getElementById("showPassword");
const password = document.getElementById("password");

if (showPassword && password) {

    showPassword.addEventListener("change", function () {

        if (this.checked) {
            password.type = "text";
        } else {
            password.type = "password";
        }

    });

}