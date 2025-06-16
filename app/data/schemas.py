from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from typing import Union


class User(BaseModel):
    name : str
    email: str
    password: str


class UserOut(BaseModel):
    # id : int
    name: str
    email : str
    # password: str
    added_on : Optional[datetime] = None
    update_on : Optional[datetime] = None

    class Config():
        orm_mode = True


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type : str


class UserUpdate(BaseModel):
    name : Union[str , None] = None
    email: Union[str , None] = None

class Order(BaseModel):
    coord_ke: int = 1  # jumlah lokasi yang dipilih dalam sekali order
    id_user: int
    phone: str = ""
    name: str = ""
    place_id: str = ""  # Google Place ID
    place_type: str = ""  # e.g. N, W, S, etc.
    place_key: str = ""  # e.g. amenity etc
    place_value: str = ""  # e.g. Starbucks, restaurant, etc.
    lat: str = ""
    lon: str = ""
    country_code: str = ""
    country_name: str = ""
    country_code_iso3: str = ""  # IDN, USA, etc.
    region: str = ""
    province: str = ""  # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city: str = ""
    label: str = ""
    sublabel: str = ""
    postcode: str = ""
    district: str = ""   # Kecamatan, Kelurahan, etc.
    locality: str = ""  # Kota, Kabupaten, etc.
    place: str = ""
    neighborhood: str = ""
    address: str = ""  # Alamat lengkap e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    building: str = ""
    house_number: str = ""
    road: str = ""
    geojson: str = ""
    jarak: float = 0.0
    pendakian: float = 0.0
    waktu: float = 0.0
    kendaraan: str = ""
    vehicle_type_ordered: int = 0  # 0 = bike, 1 = car, 2 = truck, etc.
    status: int = 0
    status_nearest: int = 0  # = 0, order no process, 1 = order near 0-5 minutes , 2 = order near 5-10 minutes, 3 = order near 10-30 minutes, 4 = order near than 30-120 minutes, 5 = order not assigned

class OrderPickup(BaseModel):
    id_order: int
    id_user: int
    phone: str = ""
    name: str = ""
    place_id: str = ""  # Google Place ID
    place_type: str = ""  # e.g. N, W, S, etc.
    place_key: str = ""  # e.g. amenity etc
    place_value: str = ""  # e.g. Starbucks, restaurant, etc.
    lat: str = ""
    lon: str = ""
    country_code: str = ""
    country_name: str = ""
    country_code_iso3: str = ""  # IDN, USA, etc.
    region: str = ""
    province: str = ""  # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city: str = ""
    label: str = ""
    sublabel: str = ""
    postcode: str = ""
    district: str = ""   # Kecamatan, Kelurahan, etc.
    locality: str = ""  # Kota, Kabupaten, etc.
    place: str = ""
    neighborhood: str = ""
    address: str = ""  # Alamat lengkap e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    building: str = ""
    house_number: str = ""
    road: str = ""
    description: str = ""
    city_block: str = ""  # e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    geojson: str = ""
    jarak: float = 0.0
    pendakian: float = 0.0
    waktu: float = 0.0
    kendaraan: str = ""
    vehicle_type_ordered: int = 0  # 0 = bike, 1 = car, 2 = truck, etc.
    status: int = 0 # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
    status_nearest: int = 0  # = 0, order no process, 1 = order near 0-5 minutes , 2 = order near 5-10 minutes, 3 = order near 10-30 minutes, 4 = order near than 30-120 minutes, 5 = order not assigned
    canceled_reason: str = ""  # Alasan pembatalan order
    promo: str = ""
    is_pickup: int = 0  # 0 = belum pickup, 1 = driver sudah tiba, 2 = sudah di pickup oleh driver
    id_driver: int = 0
    waiting_time: float = 0.0  # waktu tunggu driver pickup customer
    running: int = 0  # sudah diproses atau belum oleh driver
    finished: int = 0  # sudah selesai atau belum oleh driver
    is_active: int = 1  # 0 = tidak aktif, 1 = aktif, 2 = pending, 3 = cancelled, 4 = completed

class DriverCoords(BaseModel):
    id_driver: int
    phone: str = ""
    name: str = ""
    place_id: str = ""  # Google Place ID
    place_type: str = ""  # e.g. N, W, S, etc.
    place_key: str = ""  # e.g. amenity etc
    place_value: str = ""  # e.g. Starbucks, restaurant, etc.
    lat: str = ""
    lon: str = ""
    country_code: str = ""
    country_name: str = ""
    region: str = ""
    province: str = ""  # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city: str = ""
    label: str = ""
    sublabel: str = ""
    postcode: str = ""
    district: str = ""
    locality: str = ""
    place: str = ""
    neighborhood: str = ""
    address: str = ""
    vehicle_type: int = 0
    vehicle_number: str = ""
    priority: int = 10
    progress_order: bool = False    # 0 = belum ada order, 1 = sedang proses order
    active: bool = True # toogle switch ditrigger dari app driver | 0 = tidak aktif, 1 = sedang aktif
    last_active: Optional[datetime] = None # Optional[datetime] = datetime.now()
    daily_order_count: int = 0  # Count all orders today
    daily_completed_count: int = 0  # Count of orders completed today
    daily_cancelled_count: int = 0  # Count of orders cancelled today
    status: int = 1
    is_active: int = 1  # 0 = tidak aktif, 1 = aktif, 2 = pending, 3 = cancelled, 4 = completed, 5 = blocked, 6 = suspended, 7 = deactivated

class DriverCoordsOut(BaseModel):
    id_user: int
    vehicle_type: int = 0   # 0 = bike, 1 = car, 2 = truck, etc.
    country_code: str = ""
    region: str = ""
    province: str = ""  # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city: str = ""
    label: str = ""
    sublabel: str = ""
    postcode: str = ""
    district: str = ""
    locality: str = ""
    place: str = ""
    neighborhood: str = ""
    address: str = ""

class ProcessAssign(BaseModel):
    id_user: int
    vehicle_type: int
    country_code: str = "ID"
    region: str = "Banten"
    url: str = ""  # URL for the latest location of the driver

class OrderAssigned(BaseModel):
    id_order_pickup: int
    id_driver: int
    id_user: int
    vehicle_type: int = 0  # 0 = bike, 1 = car, 2 = truck, etc.
    latest_url: str = ""
    waiting_time: float = 0.0  # waktu tunggu driver pickup customer
    status: int
    is_active: bool = False  # 0 = tidak aktif, 1 = aktif

class CountryPrice(BaseModel):
    country_code: str
    country_name: str
    country_code_iso3: str = ""
    region: str = ""
    city: str = ""
    country_calling_code: str = ""
    currency_name: str
    currency_symbol: str
    bike_harga_pertama: float
    bike_harga_meter_pertama: int
    bike_harga_permeter: float
    car_harga_pertama: float
    car_harga_meter_pertama: int
    car_harga_permeter: float

class TripBikeCar(BaseModel):
    country_code: str = "ID"  # Default to Indonesia
    region: str = "Jakarta"  # Default to Jakarta
    type_trip: int = 0  # 0 = "sekarang", 1 = "reservasi"
    jarak_trip: float = 0.0  # Distance in meters for the trip
    waktu_trip: float = 0.0   # e.g 6572.795
    pickup_lat: str = ""
    pickup_lon: str = ""
    dropoff_lat: str = ""
    dropoff_lon: str = ""
    vehicle_type: str = "bike"  # 0 = bike, 1 = car, 2 = truck, etc.
    # points_encoded: bool = False  # if True, the points are encoded in a compact format
    snap_prevention: str = "ferry"  # "ferry", "none", "all"