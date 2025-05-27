
Instrucțiuni de rulare:
1. Instalează dependențele cu: pip install flask mysql-connector-python
2. Asigură-te că ai baza de date creată pe https://freedb.tech
3. Creează tabelul cu comanda SQL:

CREATE TABLE weather (
    id INT PRIMARY KEY,
    nume VARCHAR(255),
    valoare FLOAT,
    unitate_masura VARCHAR(50)
);

4. Rulează aplicația cu: python app.py
5. Accesează în browser: http://localhost:5000
