const preview = document.getElementById("CreateNewPost");
const input = document.getElementById("WriteNewPost");
const back = document.getElementById("Get-back-from-post");
const post_button = document.getElementById("Posts-post-button")
const message_button = document.getElementById("Post-message-button");
const post_view_port = document.getElementById("Posts");
const message_view_port = document.getElementById("Messsage-view-port");

const write_new_message_form = document.getElementById("NewMessageAndMessages")
const write_new_message = document.getElementById("create-new-message");
const back_message = document.getElementById("Get-back-from-message");
const CreateNewmessage = document.getElementById("NewMessageAndMessagesform");


// This is to track follow

const Track_visible_follow = document.getElementById("Visible_Follow_Button");
const Track_Hidden_follow = document.getElementById("Hidden_Follow_Button");


preview.addEventListener("click", () => {
    input.style.zIndex=1;
    input.style.display="block";
    preview.style.display="none";
});

back.addEventListener('click', () => {
    input.style.display="none";
    preview.style.display="block";

})

post_button.addEventListener("click", () => {
    message_view_port.style.display = "none";
    post_view_port.style.display = "block";
});

message_button.addEventListener("click", () => {
    post_view_port.style.display = "none";
    message_view_port.style.display = "block";
});

write_new_message.addEventListener("click", () => {
    write_new_message_form.style.display = "block";
})

back_message.addEventListener('click', () => {
    write_new_message_form.style.display="none";
    message_view_port.style.display="block";

})

Track_visible_follow.addEventListener("click", () => {
    Track_Hidden_follow.click();
});