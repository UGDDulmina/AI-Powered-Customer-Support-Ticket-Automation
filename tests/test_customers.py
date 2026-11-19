from app.models.customer import Customer

def test_create_customer(
        client, 
        sample_customer,
        db_session

 ):

    response = client.post(
        "/api/v1/customers",
        json=sample_customer
    )

    assert response.status_code == 201

    customer_id = response.json()["id"]

    customer = db_session.get(Customer, customer_id)

    assert customer is not None
    assert customer.email == sample_customer["email"]

def test_duplicate_customer_email(client, sample_customer):

    first_response = client.post(
        "/api/v1/customers",
        json=sample_customer
    )

    second_response = client.post(
        "/api/v1/customers",
        json=sample_customer
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

def test_get_customer_by_id(client, created_customer):

    customer_id = created_customer["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["email"] == created_customer["email"]

def test_get_nonexistent_customer(client):

    response = client.get(
        "/api/v1/customers/999999999"
    )

    assert response.status_code == 404  

def test_update_customer(client, created_customer):

    customer_id = created_customer["id"]

    update_data = {
        "name": "John Williams",
        "email": created_customer["email"]
    }

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        json=update_data
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "John Williams"  
    assert data["email"] == created_customer["email"]

def test_delete_customer(client, created_customer):

    customer_id = created_customer["id"]

    response = client.delete(
        f"/api/v1/customers/{customer_id}"
    )

    assert response.status_code in [200, 204]

    get_response = client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert get_response.status_code == 404

def test_get_all_customers(client, created_customer):

    customer_id = created_customer["id"]
    
    response = client.get("/api/v1/customers")

    assert response.status_code == 200

    data = response.json()

    customer_ids = [
        data["id"]
        for data in data
    ]

    assert customer_id in customer_ids


