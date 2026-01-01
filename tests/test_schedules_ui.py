def test_schedules_page_loads(client):
    response = client.get('/manage/schedules')
    assert response.status_code == 200
    assert b'Manage Scheduled Scans' in response.data
