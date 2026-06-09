import psycopg2

try:
    # Connessione al database
    conn = psycopg2.connect('postgresql://postgres.itqjupaxatvsnwbtbeiv:RGD-Alpha-2025@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')
    cur = conn.cursor()

    # Esecuzione comando di attivazione
    query = "UPDATE users SET is_active = True, role = 'user' WHERE email = 'nancydc82@yahoo.it';"
    cur.execute(query)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ ALLINEAMENTO COMPLETATO: TUA SORELLA È ATTIVA COME CLIENTE")

except Exception as e:
    print(f"❌ Errore durante l'operazione: {e}")