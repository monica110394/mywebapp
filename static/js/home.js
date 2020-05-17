$(document).ready(function(){
    $("#close_btn").click(function(){
        location.reload(true);
    })
});

function password() {
        var testV = 1;
        var pass1 = prompt('Please enter the password', '');
        while (testV < 3) {
             if (!pass1)
                 history.go(-1);
             if (pass1 == "flora") {
                 alert('Welcome to ScrubShrubs!');
                 break;
             }
             testV += 1;
             var pass1 =
                 prompt('Password error, please retype!');
         }
         if (pass1 != "password" & testV == 3)
             history.go(-1);
         return " ";
     }
    document.write(password());
