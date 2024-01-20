var origEntry = document.getElementsByClassName("ballot-entry")[0];
var parent = document.getElementById("ballotForm");

function newEntry() {
    let entry = origEntry.cloneNode(true);
    entry.style.display = "flex";
    parent.insertBefore(entry, origEntry);
}

function deleteEntry(button) {
    button.parentNode.parentNode.remove();
}