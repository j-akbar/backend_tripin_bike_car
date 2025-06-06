from app.data.database import Base
from sqlalchemy import String, DateTime, Column, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    added_on = Column(DateTime(timezone=True))
    update_on = Column(DateTime(timezone=True), default=None)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    coord_ke = Column(Integer, default=1) # jumlah lokasi yang dipilih dalam sekali order
    id_user = Column(Integer)
    phone = Column(String)
    name = Column(String, default="")
    place_id = Column(String, default="") # Google Place ID
    place_type = Column(String, default="") # e.g. N, W, S, etc.
    place_key = Column(String, default="") # e.g. amenity etc
    place_value = Column(String, default="") # e.g. Starbucks, restaurant, etc.
    lat = Column(String)
    lon = Column(String)
    country_code = Column(String, default="")
    country_name = Column(String, default="")
    country_code_iso3 = Column(String, default="") # IDN, USA, etc.
    region = Column(String, default="")
    province = Column(String, default="") # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city = Column(String, default="")
    label = Column(String, default="")
    sublabel = Column(String, default="")
    postcode = Column(String, default="")
    district = Column(String, default="")   # Kecamatan, Kelurahan, etc.
    locality = Column(String, default="") # Kota, Kabupaten, etc.
    place = Column(String, default="")
    neighborhood = Column(String, default="")
    address = Column(String, default="") # Alamat lengkap e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    building = Column(String, default="")
    house_number = Column(String, default="")
    road = Column(String, default="")
    geojson = Column(String, default="")
    jarak = Column(Float)
    pendakian = Column(Float)
    waktu = Column(Float)
    kendaraan = Column(String)
    vehicle_type_ordered = Column(Integer, default=0) # 0 = bike, 1 = car, 2 = truck, etc.
    status = Column(Integer, default=0) # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
    created_on = Column(DateTime(timezone=True))
    updated_on = Column(DateTime(timezone=True), default=None)

class OrderPickup(Base): # order tercatat hanya detail order pickup
    __tablename__ = "order_pickup"
    id = Column(Integer, primary_key=True, index=True)
    id_order = Column(Integer)
    id_user = Column(Integer)
    phone = Column(String)
    name = Column(String, default="")
    place_id = Column(String, default="") # Google Place ID
    place_type = Column(String, default="") # e.g. N, W, S, etc.
    place_key = Column(String, default="") # e.g. amenity etc
    place_value = Column(String, default="") # e.g. Starbucks, restaurant, etc.
    lat = Column(String)
    lon = Column(String)
    country_code = Column(String, default="")
    country_name = Column(String, default="")
    country_code_iso3 = Column(String, default="") # IDN, USA, etc.
    region = Column(String, default="")
    province = Column(String, default="") # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city = Column(String, default="")
    label = Column(String, default="")
    sublabel = Column(String, default="")
    postcode = Column(String, default="")
    district = Column(String, default="")   # Kecamatan, Kelurahan, etc.
    locality = Column(String, default="") # Kota, Kabupaten, etc.
    place = Column(String, default="")
    neighborhood = Column(String, default="")
    address = Column(String, default="") # Alamat lengkap e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    building = Column(String, default="")
    house_number = Column(String, default="")
    road = Column(String, default="")
    description = Column(String, default="")
    city_block = Column(String, default="") # e.g. Jl. Merdeka Blok A
    geojson = Column(String, default="")
    jarak = Column(Float)
    pendakian = Column(Float)
    waktu = Column(Float)
    kendaraan = Column(String)
    vehicle_type_ordered = Column(Integer, default=0) # 0 = bike, 1 = car, 2 = truck, etc.
    status = Column(Integer, default=0) # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
    canceled_reason = Column(String, default="") # Alasan pembatalan order
    promo = Column(String, default="") # e.g. promo code, discount code, etc.
    is_pickup = Column(Integer, default=0)  # 0 = belum pickup, 1 = driver sudah tiba, 2 = sudah di pickup oleh driver
    id_driver = Column(Integer, default=0)
    waiting_time = Column(Float, default=0.0)   # waktu tunggu
    running = Column(Integer, default=0)    # 0 = belum jalan, 1 = sudah jalan, 2 = sudah sampai tujuan
    # 3 = sudah selesai, 4 = dibatalkan
    finished = Column(Integer, default=0)   # 0 = belum selesai, 1 = sudah selesai
    is_active = Column(Integer, default=1)  # 0 = tidak aktif, 1 = aktif, 2 = pending, 3 = cancelled, 4 = completed
    created_on = Column(DateTime(timezone=True))
    updated_on = Column(DateTime(timezone=True), default=None)

class DriverCoords(Base):
    __tablename__ = "driver_coords"
    id = Column(Integer, primary_key=True, index=True)
    id_driver = Column(Integer)
    phone = Column(String)
    name = Column(String, default="")
    place_id = Column(String, default="") # Google Place ID
    place_type = Column(String, default="") # e.g. N, W, S, etc.
    place_key = Column(String, default="") # e.g. amenity etc
    place_value = Column(String, default="") # e.g. Starbucks, restaurant, etc.
    lat = Column(String)
    lon = Column(String)
    country_code = Column(String, default="") # ID, US, etc.
    country_name = Column(String, default="") # Indonesia, USA, etc.
    country_code_iso3 = Column(String, default="") # IDN, USA, etc.
    region = Column(String, default="") # Jawa Barat, DKI Jakarta, etc.
    province = Column(String, default="") # Jawa Barat, DKI Jakarta, Tangerang, etc.
    city = Column(String, default="") # Bandung, Jakarta, etc.
    label = Column(String, default="")
    sublabel = Column(String, default="")
    postcode = Column(String, default="") # postcode = Column(String, default="") # 40111, 10110, etc.
    district = Column(String, default="") # Kecamatan, Kelurahan, etc.
    locality = Column(String, default="") # Kota, Kabupaten, etc.
    place = Column(String, default="") # Tempat, Lokasi, etc.
    neighborhood = Column(String, default="") # Lingkungan, Komplek, etc.
    address = Column(String, default="") # Alamat lengkap e.g. Jl. Merdeka No. 1, RT 01/RW 02, Kelurahan Merdeka
    vehicle_type = Column(Integer, default=0) # 0 = bike, 1 = car, 2 = truck, etc.
    vehicle_number = Column(String, default="")
    priority = Column(Integer, default=10) # 10=prajurit, 9=kopral, 5=sersan, 4=letnan, 3=kapten 2=kolonel, 1=mayor, 0=jenderal, etc.
    progress_order = Column(Boolean, default=False)  # 0 = belum ada order, 1 = sedang proses order
    active = Column(Boolean, default=True)  # 0 = sedang tidak aktif, 1 = sedang aktif
    last_active = Column(DateTime(timezone=True), default=datetime.now)
    daily_order_count = Column(Integer, default=0) # Count all orders today
    daily_completed_count = Column(Integer, default=0) # Count of orders completed today
    daily_cancelled_count = Column(Integer, default=0) # Count of orders cancelled today
    status = Column(Integer, default=1) # 0 = tidak aktif, 1 = aktif, 3 = diskors, 4 = diblokir
    is_active = Column(Integer, default=1)  # 0 = tidak aktif, 1 = aktif, 2 = pending, 3 = cancelled, 4 = completed, 5 = blocked, 6 = suspended, 7 = deactivated
    created_on = Column(DateTime(timezone=True))
    updated_on = Column(DateTime(timezone=True), default=None)

class OrderAssigned(Base):
    __tablename__ = "order_assigned"
    id = Column(Integer, primary_key=True, index=True)
    id_order_pickup = Column(Integer)
    id_driver = Column(Integer)
    id_user = Column(Integer)
    vehicle_type = Column(Integer, default=0)  # 0 = bike, 1 = car, 2 = truck, etc.
    waiting_time = Column(Float, default=0.0)  # waktu tunggu driver pickup customer
    waktu_jemput = Column(Float, default=0.0)   # waktu jemput driver ke user
    waktu_antar = Column(Float, default=0.0)  # waktu antar customer ke lokasi destinasi
    url = Column(String, default="") 
    status = Column(Integer, default=0)  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
    is_active = Column(Boolean, default=False)  # 0 = tidak aktif, 1 = aktif
    created_on = Column(DateTime(timezone=True))
    updated_on = Column(DateTime(timezone=True), default=None)

class CountryPrice(Base): # setting harga berdasarkan negara
    __tablename__ = "country_prices"
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String)
    country_name = Column(String)
    country_code_iso3 = Column(String, default="")
    region = Column(String, default="")
    city = Column(String, default="")
    country_calling_code = Column(String, default="")
    currency_name = Column(String)
    currency_symbol = Column(String)
    bike_harga_pertama = Column(Float)
    bike_harga_meter_pertama = Column(Integer)
    bike_harga_permeter = Column(Float)
    car_harga_pertama = Column(Float)
    car_harga_meter_pertama = Column(Integer)
    car_harga_permeter = Column(Float)
    created_on = Column(DateTime(timezone=True))
    updated_on = Column(DateTime(timezone=True), default=None)
