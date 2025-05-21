from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_difficile_a_deviner'

# Configuration de la base de données
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'inventory_management')
}

# Fonction pour se connecter à la base de données
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None

# Route pour la page d'accueil
@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)

        # Récupérer les produits
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        """)
        products = cursor.fetchall()

        # Récupérer les produits en alerte
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock <= p.alert_threshold
            ORDER BY (p.current_stock / p.alert_threshold) ASC
        """)
        low_stock_products = cursor.fetchall()

        # Récupérer les catégories
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('index.html',
                              products=products,
                              low_stock_products=low_stock_products,
                              categories=categories)

    flash('Erreur de connexion à la base de données', 'danger')
    return render_template('index.html', products=[], low_stock_products=[], categories=[])

# Route pour filtrer les produits
@app.route('/products/filter', methods=['GET'])
def filter_products():
    category_id = request.args.get('category_id')
    search = request.args.get('search')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    stock_status = request.args.get('stock_status')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)

        # Construction de la requête avec filtres
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []

        if category_id and category_id != '':
            query += " AND p.category_id = %s"
            params.append(int(category_id))

        if search and search != '':
            query += " AND (p.name LIKE %s OR p.reference LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        if min_price and min_price != '':
            query += " AND p.price >= %s"
            params.append(float(min_price))

        if max_price and max_price != '':
            query += " AND p.price <= %s"
            params.append(float(max_price))

        if stock_status == 'low':
            query += " AND p.current_stock <= p.alert_threshold"
        elif stock_status == 'out':
            query += " AND p.current_stock = 0"
        elif stock_status == 'in':
            query += " AND p.current_stock > 0"

        query += " ORDER BY p.name"

        cursor.execute(query, params)
        products = cursor.fetchall()

        # Récupérer les catégories pour le filtre
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('filtered_products.html',
                              products=products,
                              categories=categories,
                              filters={
                                  'category_id': category_id,
                                  'search': search,
                                  'min_price': min_price,
                                  'max_price': max_price,
                                  'stock_status': stock_status
                              })

    flash('Erreur de connexion à la base de données', 'danger')
    return redirect(url_for('index'))

# Route pour ajouter un produit
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        reference = request.form['reference']
        price = float(request.form['price'])
        current_stock = int(request.form['current_stock'])
        alert_threshold = int(request.form['alert_threshold'])
        category_id = request.form['category_id'] if request.form['category_id'] else None

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            try:
                # Insérer le produit
                cursor.execute("""
                    INSERT INTO products
                    (name, reference, price, current_stock, alert_threshold, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, reference, price, current_stock, alert_threshold, category_id))

                product_id = cursor.lastrowid

                # Créer un mouvement de stock initial si nécessaire
                if current_stock > 0:
                    cursor.execute("""
                        INSERT INTO stock_movements
                        (product_id, quantity, reason)
                        VALUES (%s, %s, %s)
                    """, (product_id, current_stock, 'Stock initial'))

                conn.commit()
                flash('Produit ajouté avec succès', 'success')

            except Error as e:
                conn.rollback()
                flash(f'Erreur lors de l\'ajout du produit: {e}', 'danger')

            cursor.close()
            conn.close()

            return redirect(url_for('index'))

        flash('Erreur de connexion à la base de données', 'danger')

    # GET request - afficher le formulaire
    conn = get_db_connection()
    categories = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('add_product.html', categories=categories)

# Route pour mettre à jour le stock
@app.route('/products/update-stock/<int:product_id>', methods=['GET', 'POST'])
def update_stock(product_id):
    conn = get_db_connection()
    if not conn:
        flash('Erreur de connexion à la base de données', 'danger')
        return redirect(url_for('index'))

    cursor = conn.cursor(dictionary=True)

    # Récupérer les informations du produit
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash('Produit non trouvé', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        reason = request.form['reason']
        movement_type = request.form['movement_type']

        # Ajuster la quantité selon le type de mouvement
        if movement_type == 'out':
            quantity = -abs(quantity)
        else:
            quantity = abs(quantity)

        # Vérifier si le stock est suffisant pour une sortie
        if quantity < 0 and (product['current_stock'] + quantity) < 0:
            flash('Stock insuffisant pour cette opération', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('update_stock', product_id=product_id))

        try:
            # Insérer le mouvement de stock
            cursor.execute("""
                INSERT INTO stock_movements
                (product_id, quantity, reason)
                VALUES (%s, %s, %s)
            """, (product_id, quantity, reason))

            # Mettre à jour le stock du produit
            cursor.execute("""
                UPDATE products
                SET current_stock = current_stock + %s
                WHERE id = %s
            """, (quantity, product_id))

            conn.commit()
            flash('Stock mis à jour avec succès', 'success')

        except Error as e:
            conn.rollback()
            flash(f'Erreur lors de la mise à jour du stock: {e}', 'danger')

        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    # GET request - afficher le formulaire
    cursor.close()
    conn.close()
    return render_template('update_stock.html', product=product)

# Route pour voir l'historique des mouvements d'un produit
@app.route('/products/history/<int:product_id>')
def product_history(product_id):
    conn = get_db_connection()
    if not conn:
        flash('Erreur de connexion à la base de données', 'danger')
        return redirect(url_for('index'))

    cursor = conn.cursor(dictionary=True)

    # Récupérer les informations du produit
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash('Produit non trouvé', 'danger')
        return redirect(url_for('index'))

    # Récupérer l'historique des mouvements
    cursor.execute("""
        SELECT * FROM stock_movements
        WHERE product_id = %s
        ORDER BY movement_date DESC
    """, (product_id,))
    movements = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('product_history.html', product=product, movements=movements)

# Route pour la recherche avancée
@app.route('/advanced-search')
def advanced_search():
    category_id = request.args.get('category_id')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    search = request.args.get('search')
    stock_status = request.args.get('stock_status')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)

        # Construction de la requête avec filtres conditionnels
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []

        if category_id and category_id != '':
            query += " AND p.category_id = %s"
            params.append(int(category_id))

        if search and search != '':
            query += " AND (p.name LIKE %s OR p.reference LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        if min_price and min_price != '':
            query += " AND p.price >= %s"
            params.append(float(min_price))

        if max_price and max_price != '':
            query += " AND p.price <= %s"
            params.append(float(max_price))

        if stock_status == 'low':
            query += " AND p.current_stock <= p.alert_threshold"
        elif stock_status == 'out':
            query += " AND p.current_stock = 0"
        elif stock_status == 'in':
            query += " AND p.current_stock > 0"

        query += " ORDER BY p.name"

        cursor.execute(query, params)
        products = cursor.fetchall()

        # Récupérer les catégories pour le formulaire
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('advanced_search.html',
                              products=products,
                              categories=categories,
                              filters={
                                  'category_id': category_id,
                                  'min_price': min_price,
                                  'max_price': max_price,
                                  'search': search,
                                  'stock_status': stock_status
                              })

    flash('Erreur de connexion à la base de données', 'danger')
    return render_template('advanced_search.html', products=[], categories=[], filters={})

if __name__ == '__main__':
    app.run(debug=True)
