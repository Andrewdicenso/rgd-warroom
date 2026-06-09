import psycopg2

try:
    # Connessione al database esterno
    conn = psycopg2.connect('postgresql://postgres.itqjupaxatvsnwbtbeiv:RGD-Alpha-2025@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')
    cur = conn.cursor()

    # Comando per attivare tua sorella SOLO come USER
    query = "UPDATE users SET is_active = True, role = 'user' WHERE email = 'nancydc82@yahoo.it';"
    
    cur.execute(query)
    conn.commit()
    
    cur.close()
    conn.close()
    print("✅ OPERAZIONE RIUSCITA: Nancy attivata con ruolo USER")

except Exception as e:
    print(f"❌ Errore: {e}")