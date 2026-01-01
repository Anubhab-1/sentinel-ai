document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#schedules-table tbody');
  const form = document.getElementById('create-form');
  const result = document.getElementById('create-result');

  async function loadSchedules() {
    const resp = await fetch('/schedules', { headers: { 'X-API-Key': '' } });
    if (resp.ok) {
      const data = await resp.json();
      tableBody.innerHTML = '';
      for (const s of data.schedules) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${s.id}</td>
          <td>${s.url}</td>
          <td>${s.interval_minutes}</td>
          <td>${s.enabled}</td>
          <td>${s.last_run || ''}</td>
          <td><button data-id="${s.id}" class="delete">Delete</button></td>
        `;
        tableBody.appendChild(tr);
      }
    } else {
      tableBody.innerHTML = '<tr><td colspan="6">Unable to load schedules</td></tr>';
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('url').value;
    const interval = document.getElementById('interval').value;
    const resp = await fetch('/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': '' },
      body: JSON.stringify({ url, interval_minutes: interval }),
    });

    if (resp.status === 201) {
      result.textContent = 'Created';
      loadSchedules();
    } else {
      result.textContent = 'Error creating schedule';
    }
  });

  tableBody.addEventListener('click', async (e) => {
    if (e.target.classList.contains('delete')) {
      const id = e.target.getAttribute('data-id');
      const resp = await fetch(`/schedules/${id}`, {
        method: 'DELETE',
        headers: { 'X-API-Key': '' }
      });
      if (resp.ok) loadSchedules();
    }
  });

  // Initial load
  loadSchedules();
});