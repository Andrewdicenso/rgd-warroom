import psycopg2

try:
    # Connessione al tuo database Supabase
    conn = psycopg2.connect('postgresql://postgres.itqjupaxatvsnwbtbeiv:RGD-Alpha-2025@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')
    cur = conn.cursor()
    
    # Interrogazione per vedere tutte le tabelle create da te
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cur.fetchall()
    
    print("\n--- TABELLE PRESENTI NEL TUO DATABASE ---")
    if not tables:
        print("Il database è vuoto (nessuna tabella trovata).")
    else:
        for t in tables:
            print(f"-> {t[0]}")
    print("------------------------------------------\n")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Errore di connessione: {e}")