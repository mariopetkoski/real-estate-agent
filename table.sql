CREATE TABLE properties.real_estate_listings (
    ID VARCHAR PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Price FLOAT,
    Currency VARCHAR(10) NOT NULL,
    Number_of_rooms FLOAT,
    Location VARCHAR(255) NOT NULL,
    Area_m2 FLOAT,
    Url varchar(255) NOT NULL,
    Accuracy INT
);
