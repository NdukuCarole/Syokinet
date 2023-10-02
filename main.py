from typing import List

from fastapi import FastAPI, HTTPException, Body, Depends
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, String, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from starlette import status
from starlette.responses import JSONResponse

# Create a SQLite database
DATABASE_URL = "sqlite:///./ip_addresses.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


# Define IP Address model
class IPAddress(Base):
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True)
    status = Column(Enum("available", "allocated", "reserved"), default="available")
    customer_name = Column(String, nullable=True)
    email = Column(String, nullable=True)


class CustomerDetails(BaseModel):
    name: str
    email: str

class IPAddressModel(BaseModel):
    ip_address: str
    customer: CustomerDetails


class IPAddressListResponse(BaseModel):
    allocated_ips: List[IPAddressModel]


# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)


# API endpoints
@app.post("/ip/allocate", response_model=dict)
async def allocate_ip(ip_data: dict = Body(...)):
    try:
        customer_name = ip_data.get("customer_name")
        email = ip_data.get("email")

        # Check if there are available IPs
        db = SessionLocal()
        ip_record = db.query(IPAddress).filter_by(status="available").first()

        if ip_record:
            ip_record.status = "allocated"
            ip_record.customer_name = customer_name
            ip_record.email = email
            db.commit()

            return {
                "status_code": status.HTTP_201_CREATED,
                "ip_address": ip_record.ip_address
            }
        else:
            raise HTTPException(status_code=500, detail="No available IPs")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/ip/release/{ip_address}", response_model=dict)
async def release_ip(ip_address: str):
    try:
        db = SessionLocal()
        ip_record = db.query(IPAddress).filter_by(ip_address=ip_address, status="allocated").first()

        if ip_record:
            ip_record.status = "available"
            ip_record.customer_name = None
            ip_record.email = None
            db.commit()
            return {
                "status_code": status.HTTP_200_OK,
                "message": "IP released successfully"}
        else:
            raise HTTPException(status_code=404, detail="IP not found or not allocated")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ip/allocated", response_model=IPAddressListResponse)
async def list_allocated_ips():
    db = SessionLocal()
    try:
        allocated_ips_db = db.query(IPAddress).filter_by(status="allocated").all()
        allocated_ips = []
        for ip in allocated_ips_db:
            customer_details = CustomerDetails(name=ip.customer_name, email=ip.email)
            ip_address_model = IPAddressModel(ip_address=ip.ip_address, customer=customer_details)
            allocated_ips.append(ip_address_model)

        response_model = IPAddressListResponse(allocated_ips=allocated_ips)
        return JSONResponse(
            content=response_model.dict(),
            status_code=status.HTTP_200_OK)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import status


@app.get("/ip/available", response_model=list, status_code=status.HTTP_200_OK)
async def list_available_ips():
    try:
        db = SessionLocal()
        available_ips_db = db.query(IPAddress.ip_address).filter_by(status="available").all()

        available_ips = [ip[0] for ip in available_ips_db]

        return available_ips
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
