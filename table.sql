CREATE TABLE properties.real_estate_listings (
    ID SERIAL PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Price FLOAT,
    Currency VARCHAR(10) NOT NULL,
    Number_of_rooms FLOAT,
    Location VARCHAR(255) NOT NULL,
    Area_m2 FLOAT
);
