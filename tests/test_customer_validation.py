
def test_create_customer_invalid_email(client):

    response = client.post(
        "/api/v1/customers",
        json={
            "name":"John",
            "email":"invalid-email"
        }
    )

    assert response.status_code == 422
    assert "detail" in response.json()

def test_create_customer_missing_name(client):

    reponse = client.post(
        "/api/v1/customers",
        json={
            "email": "john@example.com"
        }
    )

    assert reponse.status_code == 422
    assert "detail" in reponse.json()