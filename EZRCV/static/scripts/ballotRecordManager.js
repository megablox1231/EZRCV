var origRecord = document.getElementsByClassName("bal-record")[0];
var parent = document.getElementById("recordHolder");

function newRecord() {
    let record = origRecord.cloneNode(true);
    record.style.display = "block";
    record.getElementsByTagName("input")[0].name = "entries"
    parent.insertBefore(record, origRecord);
}

function deleteEntry(button) {
    button.parentNode.parentNode.remove();
}