function startScan() {
  document.getElementById("loader").classList.remove("hidden");
  document.getElementById("scanBtn").disabled = true;
}

function handleExplain(button) {
  const index = button.dataset.index;
  const issue = JSON.parse(button.dataset.issue);
  const severity = JSON.parse(button.dataset.severity);
  const reasons = JSON.parse(button.dataset.reasons);

  const box = document.getElementById(`explanation-${index}`);

  // 🔒 Prevent double-clicks
  if (box.dataset.loading === "true") return;

  box.dataset.loading = "true";
  box.innerText = "Generating explanation…";

  fetch("/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      issue: issue,
      severity: severity,
      reasons: reasons
    })
  })
    .then(res => res.json())
    .then(data => {
      box.innerText = data.explanation || "AI explanation unavailable.";
      box.dataset.loading = "false";   // ✅ SUCCESS CASE
    })
    .catch(err => {
      console.error(err);
      box.innerText = "AI explanation failed.";
      box.dataset.loading = "false";   // ✅ FAILURE CASE
    });
}
