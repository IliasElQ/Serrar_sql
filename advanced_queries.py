from flask import current_app
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import os

# Configuration de la base de données
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
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

# Fonction pour obtenir la classification des produits par niveau de stock
def get_stock_classification():
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        p.id,
        p.name,
        p.reference,
        p.current_stock,
        p.alert_threshold,
        CASE 
            WHEN p.current_stock = 0 THEN 'Épuisé'
            WHEN p.current_stock <= p.alert_threshold THEN 'Stock faible'
            WHEN p.current_stock <= p.alert_threshold * 2 THEN 'Stock moyen'
            ELSE 'Stock suffisant'
        END AS stock_status,
        CASE 
            WHEN p.current_stock = 0 THEN 'danger'
            WHEN p.current_stock <= p.alert_threshold THEN 'warning'
            WHEN p.current_stock <= p.alert_threshold * 2 THEN 'info'
            ELSE 'success'
        END AS status_class
    FROM products p
    ORDER BY 
        CASE 
            WHEN p.current_stock = 0 THEN 1
            WHEN p.current_stock <= p.alert_threshold THEN 2
            WHEN p.current_stock <= p.alert_threshold * 2 THEN 3
            ELSE 4
        END
    """
    
    cursor.execute(query)
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return products

# Fonction pour analyser les mouvements de stock sur une période
def analyze_stock_movements(start_date=None, end_date=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    # Définir les dates par défaut si non spécifiées
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    query = """
    SELECT 
        p.id,
        p.name,
        p.reference,
        p.current_stock,
        COALESCE(SUM(CASE WHEN sm.quantity > 0 THEN sm.quantity ELSE 0 END), 0) AS total_entrees,
        COALESCE(SUM(CASE WHEN sm.quantity < 0 THEN ABS(sm.quantity) ELSE 0 END), 0) AS total_sorties,
        COALESCE(SUM(sm.quantity), 0) AS mouvement_net
    FROM 
        products p
    LEFT JOIN 
        stock_movements sm ON p.id = sm.product_id AND sm.movement_date BETWEEN %s AND %s
    GROUP BY 
        p.id, p.name, p.reference, p.current_stock
    ORDER BY 
        mouvement_net DESC
    """
    
    cursor.execute(query, (start_date, end_date))
    movements = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return movements

# Fonction pour obtenir les recommandations de réapprovisionnement
def get_restock_recommendations():
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        p.id,
        p.name,
        p.reference,
        p.current_stock,
        p.alert_threshold,
        CASE 
            WHEN p.current_stock <= p.alert_threshold THEN 
                CASE
                    -- Si beaucoup de sorties récentes, commander plus que le minimum
                    WHEN (SELECT COUNT(*) FROM stock_movements 
                          WHERE product_id = p.id AND quantity < 0 
                          AND movement_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)) > 5 
                    THEN p.alert_threshold * 3 - p.current_stock
                    
                    -- Sinon, commander juste pour atteindre le seuil optimal
                    ELSE p.alert_threshold * 2 - p.current_stock
                END
            ELSE 0
        END AS quantite_recommandee,
        CASE 
            WHEN p.current_stock <= p.alert_threshold THEN 'Oui'
            ELSE 'Non'
        END AS reapprovisionner
    FROM 
        products p
    WHERE 
        p.current_stock <= p.alert_threshold * 1.5
    ORDER BY 
        (p.current_stock / p.alert_threshold) ASC
    """
    
    cursor.execute(query)
    recommendations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return recommendations

# Fonction pour analyser les produits par catégorie
def analyze_products_by_category():
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        c.id,
        c.name AS category_name,
        COUNT(p.id) AS nombre_produits,
        SUM(p.current_stock) AS stock_total,
        SUM(p.price * p.current_stock) AS valeur_stock,
        SUM(CASE WHEN p.current_stock <= p.alert_threshold THEN 1 ELSE 0 END) AS produits_alerte,
        ROUND(SUM(CASE WHEN p.current_stock <= p.alert_threshold THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id), 2) AS pourcentage_alerte,
        CASE 
            WHEN SUM(CASE WHEN p.current_stock <= p.alert_threshold THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id) > 50 THEN 'Critique'
            WHEN SUM(CASE WHEN p.current_stock <= p.alert_threshold THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id) > 20 THEN 'Attention'
            ELSE 'Normal'
        END AS statut_categorie
    FROM 
        categories c
    LEFT JOIN 
        products p ON c.id = p.category_id
    GROUP BY 
        c.id, c.name
    ORDER BY 
        pourcentage_alerte DESC
    """
    
    cursor.execute(query)
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return categories

# Fonction pour identifier les produits sans mouvement
def identify_inactive_products(days=30):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        p.id,
        p.name,
        p.reference,
        p.current_stock,
        p.price,
        p.price * p.current_stock AS valeur_stock,
        MAX(sm.movement_date) AS dernier_mouvement,
        DATEDIFF(CURRENT_DATE, COALESCE(MAX(sm.movement_date), p.entry_date)) AS jours_sans_mouvement,
        CASE 
            WHEN MAX(sm.movement_date) IS NULL THEN 'Jamais utilisé'
            WHEN DATEDIFF(CURRENT_DATE, MAX(sm.movement_date)) > 90 THEN 'Inactif'
            WHEN DATEDIFF(CURRENT_DATE, MAX(sm.movement_date)) > 30 THEN 'Peu actif'
            ELSE 'Actif'
        END AS statut_activite
    FROM 
        products p
    LEFT JOIN 
        stock_movements sm ON p.id = sm.product_id
    GROUP BY 
        p.id, p.name, p.reference, p.current_stock, p.price, p.entry_date
    HAVING 
        jours_sans_mouvement > %s OR jours_sans_mouvement IS NULL
    ORDER BY 
        jours_sans_mouvement DESC
    """
    
    cursor.execute(query, (days,))
    inactive_products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return inactive_products

# Fonction pour recherche avancée avec filtres dynamiques
def advanced_search(category_id=None, min_price=None, max_price=None, search_term=None, stock_status=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT p.*, c.name as category_name
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE 1=1
    """
    
    params = []
    
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    
    if min_price is not None:
        query += " AND p.price >= %s"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND p.price <= %s"
        params.append(max_price)
    
    if search_term:
        query += " AND (p.name LIKE %s OR p.reference LIKE %s)"
        search_param = f"%{search_term}%"
        params.extend([search_param, search_param])
    
    if stock_status == 'low':
        query += " AND p.current_stock <= p.alert_threshold"
    elif stock_status == 'out':
        query += " AND p.current_stock = 0"
    elif stock_status == 'in':
        query += " AND p.current_stock > 0"
    
    query += " ORDER BY p.name"
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return products