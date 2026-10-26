import streamlit as st
import mysql.connector
import pandas as pd

# 1. Establish Database Connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # Change to your MySQL username if different
        password="password",  # Change to your MySQL password
        database="hotel_management_db"
    )

st.title("🏨 Hotel Management System")
st.sidebar.title("Navigation Menu")

menu = st.sidebar.radio("Choose Action", ["View Rooms", "Add Room", "Register Guest", "Book a Room"])

# --- 1. VIEW ROOMS ---
if menu == "View Rooms":
    st.subheader("Available & Occupied Rooms")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rooms", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- 2. ADD ROOM ---
elif menu == "Add Room":
    st.subheader("Add a New Room to the Hotel")
    with st.form("add_room_form"):
        room_no = st.text_input("Room Number (e.g., 103)")
        room_type = st.selectbox("Room Type", ["Single", "Double", "Suite"])
        price = st.number_input("Price Per Night ($)", min_value=0.0, format="%.2f")
        submit = st.form_submit_button("Save Room")
        
        if submit:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                query = "INSERT INTO rooms (room_number, room_type, price_per_night, status) VALUES (%s, %s, %s, 'Available')"
                cursor.execute(query, (room_no, room_type, price))
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"Room {room_no} added successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. REGISTER GUEST ---
elif menu == "Register Guest":
    st.subheader("Register a New Guest")
    with st.form("guest_form"):
        fname = st.text_input("First Name")
        lname = st.text_input("Last Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        submit = st.form_submit_button("Register Guest")
        
        if submit:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                query = "INSERT INTO guests (first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (fname, lname, email, phone))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Guest registered successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 4. BOOK A ROOM ---
elif menu == "Book a Room":
    st.subheader("Create a Room Booking")
    
    conn = get_connection()
    guests_df = pd.read_sql("SELECT guest_id, CONCAT(first_name, ' ', last_name) AS name FROM guests", conn)
    rooms_df = pd.read_sql("SELECT room_id, room_number, price_per_night FROM rooms WHERE status = 'Available'", conn)
    conn.close()
    
    if guests_df.empty or rooms_df.empty:
        st.warning("Please make sure you have registered at least one guest and have available rooms in the system.")
    else:
        with st.form("booking_form"):
            guest_choice = st.selectbox("Select Guest", guests_df['name'].tolist())
            room_choice = st.selectbox("Select Available Room Number", rooms_df['room_number'].tolist())
            check_in = st.date_input("Check-In Date")
            check_out = st.date_input("Check-Out Date")
            
            submit = st.form_submit_button("Confirm Booking")
            
            if submit:
                selected_guest_id = guests_df.loc[guests_df['name'] == guest_choice, 'guest_id'].values[0]
                selected_room_id = rooms_df.loc[rooms_df['room_number'] == room_choice, 'room_id'].values[0]
                price_per_night = rooms_df.loc[rooms_df['room_number'] == room_choice, 'price_per_night'].values[0]
                
                days = (check_out - check_in).days
                if days <= 0:
                    st.error("Check-out date must be after check-in date.")
                else:
                    total_amount = days * float(price_per_night)
                    
                    try:
                        conn = get_connection()
                        conn.start_transaction()
                        cursor = conn.cursor()
                        
                        b_query = "INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date, total_amount) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(b_query, (selected_guest_id, selected_room_id, check_in, check_out, total_amount))
                        
                        r_query = "UPDATE rooms SET status = 'Occupied' WHERE room_id = %s"
                        cursor.execute(r_query, (selected_room_id,))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"Booking confirmed! Total Amount: ${total_amount:.2f}")
                    except Exception as e:
                        st.error(f"Transaction failed: {e}")