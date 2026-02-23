import psycopg
from psycopg import cursor
import time
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
import os

# --- CONFIGURATION ---
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

fake = Faker()

# Table Names
TBL_GEO = "geolocation"
TBL_CUST = "customers"
TBL_SELLER = "sellers"
TBL_PROD = "products"
TBL_ORDERS = "orders"
TBL_ITEMS = "order_items"
TBL_PAYMENTS = "payments"
TBL_REVIEWS = "order_reviews"

def get_conn():
    # Remove autocommit=True to use proper transaction blocks
    conn = psycopg.connect(**DB_CONFIG)
    return conn

# --- HELPERS ---

def get_random_geo_from_db(cur: cursor.Cursor):
    try:
        # Changed to TABLESAMPLE SYSTEM (1) to ensure it works on small tables
        sql = f"SELECT geolocation_zip_code_prefix, geolocation_city, geolocation_state FROM {TBL_GEO} TABLESAMPLE SYSTEM (1) LIMIT 1"
        cur.execute(sql)
        res = cur.fetchone()
        return res if res else (10000, "Sao Paulo", "SP")
    except Exception:
        return (10000, "Sao Paulo", "SP")

def get_random_id(cur: cursor.Cursor, table, column):
    try:
        cur.execute(f"SELECT {column} FROM {table} TABLESAMPLE SYSTEM (1) LIMIT 1;")
        res = cur.fetchone()
        return res[0] if res else None
    except Exception:
        return None

def get_product_price(cur: cursor.Cursor, product_id):
    try:
        cur.execute(f"SELECT price FROM {TBL_ITEMS} WHERE product_id = %s LIMIT 1", (product_id,))
        res = cur.fetchone()
        if res:
            return float(res[0])
    except Exception:
        pass
    return round(random.uniform(10, 300), 2)

# --- ENTITY MANAGEMENT ---

def prepare_customer_for_order(cur: cursor.Cursor):
    is_returning = random.random() < 0.85
    
    # Try to reuse existing customer (85% chance)
    if is_returning:
        cur.execute(f"SELECT customer_id FROM {TBL_CUST} TABLESAMPLE SYSTEM (1) LIMIT 1")
        existing = cur.fetchone()
        if existing:
            return existing[0]  # REUSE existing customer_id, no INSERT
    
    # Create NEW customer only when needed (15% new customers)
    # Check for UUID collision (defensive programming)
    while True:
        new_cust_id = uuid.uuid4().hex
        u_id = uuid.uuid4().hex
        
        # Check if customer_id already exists (collision check)
        cur.execute(f"SELECT 1 FROM {TBL_CUST} WHERE customer_id = %s", (new_cust_id,))
        if not cur.fetchone():  # UUID not found, safe to use
            break
        # If collision (extremely rare), loop and generate new UUID
        print(f"⚠️  UUID collision detected! Retrying...")
    
    zip_code, city, state = get_random_geo_from_db(cur)
    
    sql = f"INSERT INTO {TBL_CUST} (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(sql, (new_cust_id, u_id, zip_code, city, state))
    return new_cust_id

def get_or_create_seller(cur: cursor.Cursor):
    # Try to reuse existing seller (99% chance)
    if random.random() < 0.99:
        cur.execute(f"SELECT seller_id FROM {TBL_SELLER} TABLESAMPLE SYSTEM (1) LIMIT 1")
        existing = cur.fetchone()
        if existing:
            return existing[0]  # REUSE existing seller_id, no INSERT
    
    # Create NEW seller only when needed (1% new sellers)
    # Check for UUID collision (defensive programming)
    while True:
        s_id = uuid.uuid4().hex
        
        # Check if seller_id already exists (collision check)
        cur.execute(f"SELECT 1 FROM {TBL_SELLER} WHERE seller_id = %s", (s_id,))
        if not cur.fetchone():  # UUID not found, safe to use
            break
        # If collision (extremely rare), loop and generate new UUID
        print(f"⚠️  Seller UUID collision detected! Retrying...")
    
    zip_code, city, state = get_random_geo_from_db(cur)
    cur.execute(f"INSERT INTO {TBL_SELLER} (seller_id, seller_zip_code_prefix, seller_city, seller_state) VALUES (%s, %s, %s, %s)", 
                (s_id, zip_code, city, state))
    return s_id

# def get_or_create_product(cur: cursor.Cursor):
def get_product(cur: cursor.Cursor):
    # if random.random() < 0.98:
    p_id = get_random_id(cur, TBL_PROD, "product_id")
    # if p_id: return p_id

    # p_id = uuid.uuid4().hex
    # cat = random.choice(['bed_bath_table', 'health_beauty', 'sports_leisure', 'computers_accessories', 'electronics', 'furniture_decor'])
    # cur.execute(f"INSERT INTO {TBL_PROD} (product_id, product_category_name, product_weight_g, product_length_cm, product_height_cm, product_width_cm) VALUES (%s, %s, %s, %s, %s, %s)", 
    #             (p_id, cat, random.randint(100, 5000), 20, 10, 15))
    return p_id

# --- 2. TRANSACTION LOGIC (Start at Created) ---

def create_transaction(conn):
    try:
        with conn.transaction():
            cur = conn.cursor()
            
            # A. Always Start as Created
            status = 'created'
            purchase_ts = datetime.now()
            estimated_ts = purchase_ts + timedelta(days=random.randint(10, 20))
            
            # All other timestamps are None initially
            approved_ts = None
            carrier_ts = None
            delivered_ts = None

            # B. Insert Order
            cust_id = prepare_customer_for_order(cur)
            
            # Generate unique order_id (with collision check)
            while True:
                order_id = uuid.uuid4().hex
                cur.execute(f"SELECT 1 FROM {TBL_ORDERS} WHERE order_id = %s", (order_id,))
                if not cur.fetchone():  # UUID not found, safe to use
                    break
                print(f"⚠️  Order UUID collision detected! Retrying...")
            
            sql = f"""INSERT INTO {TBL_ORDERS} 
                      (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, 
                       order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (order_id, cust_id, status, purchase_ts, approved_ts, carrier_ts, delivered_ts, estimated_ts))

            # C. Insert Items
            num_items = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            total_val = 0

            for i in range(1, num_items + 1):
                # prod_id = get_or_create_product(cur)
                prod_id = get_product(cur)
                seller_id = get_or_create_seller(cur)
                
                price = get_product_price(cur, prod_id) 
                freight = round(random.uniform(5, 50), 2)
                total_val += price + freight
                
                # Shipping limit is calculated, but item is not shipped yet
                limit_date = purchase_ts + timedelta(days=5)

                cur.execute(f"""INSERT INTO {TBL_ITEMS} 
                                (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                            (order_id, i, prod_id, seller_id, limit_date, price, freight))

            # D. Payments
            pay_type = random.choices(['credit_card', 'boleto', 'voucher', 'debit_card'], weights=[74, 19, 5.5, 1.5])[0]
            installments = random.randint(1, 10) if pay_type == 'credit_card' else 1
            
            cur.execute(f"INSERT INTO {TBL_PAYMENTS} (order_id, payment_sequential, payment_type, payment_installments, payment_value) VALUES (%s, 1, %s, %s, %s)", 
                        (order_id, pay_type, installments, total_val))

            print(f"🆕 [NEW] Order {order_id[:8]} created.")

    except Exception as e:
        print(f"❌ Create Failed: {e}")

# --- 3. LIFECYCLE UPDATES ---

def create_review(cur, order_id):
    # Only create review if lucky (40% chance to create review)
    if random.random() > 0.40: return
    
    # Generate unique review_id (with collision check)
    while True:
        rev_id = uuid.uuid4().hex
        cur.execute(f"SELECT 1 FROM {TBL_REVIEWS} WHERE review_id = %s", (rev_id,))
        if not cur.fetchone():  # UUID not found, safe to use
            break
        print(f"⚠️  Review UUID collision detected! Retrying...")
    
    score = random.choices([5, 4, 3, 2, 1], weights=[50, 20, 10, 10, 10])[0]
    title = fake.sentence(nb_words=3) if random.random() > 0.5 else None
    msg = fake.text(max_nb_chars=100) if random.random() > 0.3 else None
    
    now = datetime.now()
    cur.execute(f"INSERT INTO {TBL_REVIEWS} (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                (rev_id, order_id, score, title, msg, now, now + timedelta(hours=2)))
    print(f"   ⭐ Review added for {order_id[:8]}")

def scenario_update_location(conn: psycopg.Connection):
    """Update a customer or seller location (triggers CDC SCD Type 2 change)"""
    try:
        with conn.transaction():
            cur = conn.cursor()
            
            # Decide whether to update customer (80%) or seller (20%)
            update_seller = random.random() < 0.1
            
            if update_seller:
                # Update seller location
                cur.execute(f"SELECT seller_id FROM {TBL_SELLER} TABLESAMPLE SYSTEM (1) LIMIT 1")
                res = cur.fetchone()
                if not res: return
                
                seller_id = res[0]
                
                # Get new random location (different from current)
                while True:
                    new_zip, new_city, new_state = get_random_geo_from_db(cur)
                    # Check if location is different from current
                    cur.execute(f"SELECT seller_zip_code_prefix, seller_city, seller_state FROM {TBL_SELLER} WHERE seller_id = %s", (seller_id,))
                    current = cur.fetchone()
                    if current and (current[0] != new_zip or current[1] != new_city or current[2] != new_state):
                        break  # Found different location
                
                # UPDATE triggers CDC event
                cur.execute(f"""UPDATE {TBL_SELLER} 
                                SET seller_zip_code_prefix = %s, 
                                    seller_city = %s, 
                                    seller_state = %s 
                                WHERE seller_id = %s""", 
                            (new_zip, new_city, new_state, seller_id))
                
                print(f"📦 [SELLER LOCATION] Seller {seller_id[:8]} relocated to {new_city}, {new_state}")
            else:
                # Update customer location (default 80% probability)
                cur.execute(f"SELECT customer_id FROM {TBL_CUST} TABLESAMPLE SYSTEM (1) LIMIT 1")
                res = cur.fetchone()
                if not res: return
                
                cust_id = res[0]
                
                # Get new random location (different from current)
                while True:
                    new_zip, new_city, new_state = get_random_geo_from_db(cur)
                    # Check if location is different from current
                    cur.execute(f"SELECT customer_zip_code_prefix, customer_city, customer_state FROM {TBL_CUST} WHERE customer_id = %s", (cust_id,))
                    current = cur.fetchone()
                    if current and (current[0] != new_zip or current[1] != new_city or current[2] != new_state):
                        break  # Found different location
                
                # UPDATE triggers CDC event
                cur.execute(f"""UPDATE {TBL_CUST} 
                                SET customer_zip_code_prefix = %s, 
                                    customer_city = %s, 
                                    customer_state = %s 
                                WHERE customer_id = %s""", 
                            (new_zip, new_city, new_state, cust_id))
                
                print(f"📍 [LOCATION] Customer {cust_id[:8]} moved to {new_city}, {new_state}")

    except Exception as e:
        print(f"⚠️ Location Update Failed: {e}")


def scenario_update_order_status(conn: psycopg.Connection):
    try:
        with conn.transaction():
            cur = conn.cursor()
            
            # Find an order that is NOT yet delivered or canceled
            cur.execute(f"SELECT order_id, order_status FROM {TBL_ORDERS} WHERE order_status NOT IN ('delivered', 'canceled') ORDER BY RANDOM() LIMIT 1")
            res = cur.fetchone()
            if not res: return

            o_id, current_status = res
            new_status = current_status
            
            # STRICT LIFECYCLE FLOW
            if current_status == 'created': 
                new_status = 'approved'
            elif current_status == 'approved': 
                new_status = 'processing'
            elif current_status == 'processing': 
                new_status = 'invoiced'
            elif current_status == 'invoiced': 
                new_status = 'shipped'
            elif current_status == 'shipped': 
                new_status = 'delivered'
            
            # Small chance to cancel (unless it's already shipped)
            if random.random() < 0.05 and current_status not in ['shipped', 'delivered']:
                new_status = 'canceled'

            if new_status != current_status:
                sql = f"UPDATE {TBL_ORDERS} SET order_status = %s"
                
                # Update specific timestamps based on status
                if new_status == 'approved':
                    sql += ", order_approved_at = NOW()"
                elif new_status == 'shipped':
                    sql += ", order_delivered_carrier_date = NOW()"
                elif new_status == 'delivered':
                    sql += ", order_delivered_customer_date = NOW()"
                
                # If your table has 'order_updated_at', un-comment the next line:
                # sql += ", order_updated_at = NOW()"

                sql += " WHERE order_id = %s"
                
                cur.execute(sql, (new_status, o_id))
                print(f"🔄 [UPDATE] Order {o_id[:8]} moved {current_status} -> {new_status}")

                # If delivered, maybe leave a review
                if new_status == 'delivered':
                    create_review(cur, o_id)

    except Exception as e:
        print(f"⚠️ Update Failed: {e}")

# --- MAIN LOOP ---
def run():
    conn = get_conn()
    
    print("🚀 Starting Olist Lifecycle Simulation...")
    print("   (Orders start 'created' and evolve sequentially)")
    
    try:
        while True:
            # Create 1 transaction
            create_transaction(conn)
            
            # Update order status multiple times
            for _ in range(random.randint(0, 10)):
                scenario_update_order_status(conn)
            
            # Occasionally update customer or seller location (triggers SCD Type 2)
            if random.random() < 0.3:  # 30% chance per cycle
                scenario_update_location(conn)
            
            # Sleep between cycles
            time.sleep(random.uniform(3, 6))

    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    run()