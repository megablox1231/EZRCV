var origEntry = document.getElementsByClassName("ballot-entry")[0];
var parent = document.getElementById("ballotForm");
var submitButton = document.getElementById("submitBtn");

function newEntry() {
    let entry = origEntry.cloneNode(true);
    entry.style.display = "flex";
    input = entry.getElementsByTagName("input")[0];
    input.name = "entries";
    input.required = true;
    parent.insertBefore(entry, origEntry);

    submitButton.disabled = false;
}

function deleteEntry(button) {
    button.parentNode.parentNode.remove();
}