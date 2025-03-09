import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import time
import threading

from main import (
    app, Base, get_db, User, AutoPlate, Bid, 
    get_password_hash, verify_password
)

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test fixtures
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(client):
    # Create and login admin user
    client.post("/register", json={
        "username": "admin",
        "email": "admin@test.com",
        "password": "admin123",
        "is_staff": True
    })
    response = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]

@pytest.fixture
def user_token(client):
    # Create and login regular user
    client.post("/register", json={
        "username": "user",
        "email": "user@test.com",
        "password": "user123",
        "is_staff": False
    })
    response = client.post("/login", data={
        "username": "user",
        "password": "user123"
    })
    return response.json()["access_token"]

# Authentication tests
def test_register_user(client):
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "is_staff": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert not data["is_staff"]

def test_login_success(client):
    # Register user first
    client.post("/register", json={
        "username": "logintest",
        "email": "login@test.com",
        "password": "password123"
    })
    
    response = client.post("/login", data={
        "username": "logintest",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

# Auto plate tests
def test_create_plate_admin(client, admin_token):
    response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "01A123BC",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["plate_number"] == "01A123BC"
    assert data["is_active"]

def test_create_plate_non_admin(client, user_token):
    response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "plate_number": "01B123CD",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    assert response.status_code == 403

def test_list_plates(client, admin_token):
    # Create a plate first
    client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "01C123DE",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    
    response = client.get("/plates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["plate_number"] == "01C123DE"

# Bid tests
def test_create_bid(client, user_token, admin_token):
    # Create plate first
    plate_response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "01D123EF",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    plate_id = plate_response.json()["id"]
    
    # Create bid
    response = client.post(
        "/bids",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "amount": 100.0,
            "plate_id": plate_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100.0
    assert data["plate_id"] == plate_id

def test_get_bid(client, user_token, admin_token):
    # Create plate and bid first
    plate_response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "01E123FG",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    plate_id = plate_response.json()["id"]
    
    bid_response = client.post(
        "/bids",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "amount": 100.0,
            "plate_id": plate_id
        }
    )
    bid_id = bid_response.json()["id"]
    
    # Get bid
    response = client.get(
        f"/bids/{bid_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == bid_id
    assert data["amount"] == 100.0

def test_update_bid(client, user_token, admin_token):
    # Create plate and bid first
    plate_response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "01F123GH",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    plate_id = plate_response.json()["id"]
    
    bid_response = client.post(
        "/bids",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "amount": 100.0,
            "plate_id": plate_id
        }
    )
    bid_id = bid_response.json()["id"]
    
    # Update bid
    response = client.put(
        f"/bids/{bid_id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "amount": 200.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 200.0

# Validation tests
def test_invalid_plate_number(client, admin_token):
    response = client.post(
        "/plates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "plate_number": "INVALID",
            "description": "Test plate",
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    )
    assert response.status_code == 422

def test_past_deadline(client, admin_token):
    from main import (
        app, Base, get_db, User, AutoPlate, Bid, 
        get_password_hash, verify_password
    )

    # Test database setup
    SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Test fixtures
    @pytest.fixture
    def db_session():
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def client(db_session):
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def admin_token(client):                  # Create and login admin user
        client.post("/register", json={
            "username": "admin",
            "email": "admin@test.com",
            "password": "admin123",
            "is_staff": True
        })
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]

    @pytest.fixture
    def user_token(client):
        # Create and login regular user
        client.post("/register", json={
            "username": "user",
            "email": "user@test.com", 
            "password": "user123",
            "is_staff": False
        })
        response = client.post("/login", data={
            "username": "user",
            "password": "user123"
        })
        return response.json()["access_token"]

    # Authentication tests
    def test_register_user(client):
        response = client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "is_staff": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert not data["is_staff"]

    def test_register_duplicate_username(client):
        # Register first user
        client.post("/register", json={
            "username": "duplicate",
            "email": "first@test.com",
            "password": "password123"
        })
        
        # Try registering duplicate username
        response = client.post("/register", json={
            "username": "duplicate", 
            "email": "second@test.com",
            "password": "password123"
        })
        assert response.status_code == 400

    def test_login_success(client):
        # Register user first
        client.post("/register", json={
            "username": "logintest",
            "email": "login@test.com",
            "password": "password123"
        })
        
        response = client.post("/login", data={
            "username": "logintest",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(client):
        # Register user
        client.post("/register", json={
            "username": "logintest",
            "email": "login@test.com",
            "password": "password123"
        })
        
        # Try logging in with wrong password
        response = client.post("/login", data={
            "username": "logintest",
            "password": "wrongpass"
        })
        assert response.status_code == 401

    # Auto plate tests
    def test_create_plate_admin(client, admin_token):
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01A123BC",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plate_number"] == "01A123BC"
        assert data["is_active"]

    def test_create_plate_non_admin(client, user_token):
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "plate_number": "01B123CD",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == 403

    def test_list_plates(client, admin_token):
        # Create a plate first
        client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01C123DE",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        
        response = client.get("/plates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["plate_number"] == "01C123DE"

    def test_get_plate_detail(client, admin_token):
        # Create plate
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01D123EF",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = response.json()["id"]
        
        # Get plate detail
        response = client.get(f"/plates/{plate_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["plate_number"] == "01D123EF"
        assert "bids" in data

    def test_update_plate(client, admin_token):
        # Create plate
        response = client.post(
            "/plates", 
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01E123FG",
                "description": "Original desc",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = response.json()["id"]
        
        # Update plate
        new_deadline = (datetime.utcnow() + timedelta(days=14)).isoformat()
        response = client.put(
            f"/plates/{plate_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01E123FG",
                "description": "Updated desc",
                "deadline": new_deadline
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated desc"

    # Bid tests
    def test_create_bid(client, user_token, admin_token):
        # Create plate first
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01F123GH",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        # Create bid
        response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["plate_id"] == plate_id

    def test_create_duplicate_bid(client, user_token, admin_token):
        # Create plate
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01G123HJ",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        # Create first bid
        client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        
        # Try creating duplicate bid
        response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": 200.0,
                "plate_id": plate_id
            }
        )
        assert response.status_code == 400

    def test_create_bid_closed_plate(client, user_token, admin_token):
        # Create plate with past deadline
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01H123JK",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(seconds=1)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        # Wait for deadline to pass
        time.sleep(2)
        
        # Try creating bid
        response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        assert response.status_code == 400

    def test_get_bid(client, user_token, admin_token):
        # Create plate and bid first
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01J123KL",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        bid_response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        bid_id = bid_response.json()["id"]
        
        # Get bid
        response = client.get(
            f"/bids/{bid_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bid_id
        assert data["amount"] == 100.0

    def test_get_other_user_bid(client, user_token, admin_token):
        # Create plate and admin's bid
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01K123LM",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        bid_response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        bid_id = bid_response.json()["id"]
        
        # Try getting admin's bid as regular user
        response = client.get(
            f"/bids/{bid_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    # Validation tests
    def test_invalid_plate_number(client, admin_token):
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "INVALID",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == 422

    def test_past_deadline(client, admin_token):
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01L123MN",
                "description": "Test plate",
                "deadline": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        )
        assert response.status_code == 422

    def test_duplicate_plate_number(client, admin_token):
        # Create first plate
        client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01M123NO",
                "description": "Test plate 1",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        
        # Try to create duplicate
        response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01M123NO",
                "description": "Test plate 2",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == 400

    def test_negative_bid_amount(client, user_token, admin_token):
        # Create plate
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01N123OP",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        # Try creating bid with negative amount
        response = client.post(
            "/bids",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "amount": -100.0,
                "plate_id": plate_id
            }
        )
        assert response.status_code == 422

    def test_bid_less_than_highest(client, user_token, admin_token):
        # Create plate
        plate_response = client.post(
            "/plates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plate_number": "01P123QR",
                "description": "Test plate",
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        plate_id = plate_response.json()["id"]
        
        # Create admin's bid
        client.post(
            "/bids",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "amount": 100.0,
                "plate_id": plate_id
            }
        )
        
        def test_bidding_closed_plate(client, user_token, admin_token):
            # Create plate that is not active
            plate_response = client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01X123YZ",
                    "description": "Test plate",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            plate_id = plate_response.json()["id"]
            
            # Deactivate plate
            client.put(
                f"/plates/{plate_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01X123YZ",
                    "description": "Test plate",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
                    "is_active": False
                }
            )
            
            # Try to bid on inactive plate
            response = client.post(
                "/bids",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "amount": 100.0,
                    "plate_id": plate_id
                }
            )
            assert response.status_code == 400

        def test_multiple_users_bidding(client, admin_token):
            # Create additional user
            client.post("/register", json={
                "username": "user2",
                "email": "user2@test.com",
                "password": "user2123",
                "is_staff": False
            })
            user2_response = client.post("/login", data={
                "username": "user2",
                "password": "user2123"
            })
            user2_token = user2_response.json()["access_token"]
            
            # Create plate
            plate_response = client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01Y123ZA",
                    "description": "Test plate",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            plate_id = plate_response.json()["id"]
            
            # First user bids
            client.post(
                "/bids",
                headers={"Authorization": f"Bearer {user2_token}"},
                json={
                    "amount": 100.0,
                    "plate_id": plate_id
                }
            )
            
            # Second user tries to bid less
            response = client.post(
                "/bids",
                headers={"Authorization": f"Bearer {user2_token}"},
                json={
                    "amount": 90.0,
                    "plate_id": plate_id
                }
            )
            assert response.status_code == 400
            
            # Second user bids more
            response = client.post(
                "/bids",
                headers={"Authorization": f"Bearer {user2_token}"},
                json={
                    "amount": 110.0,
                    "plate_id": plate_id
                }
            )
            assert response.status_code == 200

        def test_invalid_token(client):
            response = client.get(
                "/bids",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401

        def test_expired_token(client, admin_token):
            # Create token that expires immediately
            expired_token = create_access_token(
                data={"sub": "admin"},
                expires_delta=timedelta(microseconds=1)
            )
            time.sleep(1)
            
            response = client.get(
                "/bids",
                headers={"Authorization": f"Bearer {expired_token}"}
            )
            assert response.status_code == 401

        def test_plate_filters(client, admin_token):
            # Create plates with different regions
            client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01Z123AB",
                    "description": "Region 01",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            
            client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "10Z123AB",
                    "description": "Region 10",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            
            # Filter by region 01
            response = client.get("/plates?plate_number_contains=01")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["plate_number"].startswith("01")

        def test_plate_statistics(client, admin_token, user_token):
            # Create plate
            plate_response = client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01AA123BB",
                    "description": "Test plate",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            plate_id = plate_response.json()["id"]
            
            # Create multiple bids
            bids = [100.0, 200.0, 300.0]
            for amount in bids:
                client.post(
                    "/bids",
                    headers={"Authorization": f"Bearer {user_token}"},
                    json={
                        "amount": amount,
                        "plate_id": plate_id
                    }
                )
            
            # Get plate details
            response = client.get(f"/plates/{plate_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["highest_bid"] == max(bids)
            assert len(data["bids"]) == len(bids)

        def test_concurrent_bidding(client, admin_token):
            
            # Create plate
            plate_response = client.post(
                "/plates",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "plate_number": "01BB123CC",
                    "description": "Test plate",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            )
            plate_id = plate_response.json()["id"]
            
            # Create multiple users
            users = []
            for i in range(5):
                client.post("/register", json={
                    "username": f"user{i}",
                    "email": f"user{i}@test.com",
                    "password": "password123",
                    "is_staff": False
                })
                response = client.post("/login", data={
                    "username": f"user{i}",
                    "password": "password123"
                })
                users.append(response.json()["access_token"])
            
            def make_bid(token, amount):
                client.post(
                    "/bids",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "amount": amount,
                        "plate_id": plate_id
                    }
                )
            
            # Create concurrent bids
            threads = []
            for i, token in enumerate(users):
                t = threading.Thread(target=make_bid, args=(token, 100.0 * (i + 1)))
                threads.append(t)
                t.start()
            
            # Wait for all bids to complete
            for t in threads:
                t.join()
            
            # Check final state
            response = client.get(f"/plates/{plate_id}")
            assert response.status_code == 200
            data = response.json()
            assert len(data["bids"]) == len(users)
            assert data["highest_bid"] == 100.0 * len(users)