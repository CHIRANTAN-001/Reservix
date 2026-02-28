import http from 'k6/http'

export const options = {
    vus: 90,
    duration: '10s'
}

const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJzdWIiOiIwMTljOWIyNC0xY2QzLTdlYmMtOWIzMi03Njg3N2FjYTNkNGMiLCJwaG9uZSI6IjYyODk3MTUyNDUiLCJleHAiOjE3NzIyMzg0NTEuMTA3NzgzMywiaWF0IjoxNzcyMjM0ODUxLjEwNzc4OTh9.EFsJ_QBAdu_5kGB5S0Q-GU4zRstqG3YzbAw1xHHEze0'

export default function () {
     const payload = JSON.stringify({
        event_id: "019c8707-19b1-7a62-b183-c4e7b135ef19",
        section_id: "019c8707-1a16-79bb-af2b-c4c4fc4b196d",
        seats_requested: 1
    });

    let res = http.post(
        "http://localhost:8000/api/v1/bookings/hold",
        payload,
        {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        }
    );
}